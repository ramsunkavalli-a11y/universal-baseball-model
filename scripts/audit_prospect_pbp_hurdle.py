#!/usr/bin/env python3
"""Run the frozen one-year prospect PBP hurdle audit."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression

from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_WEIGHTS
from universal_baseball.prospect_arrival import arrival_design, build_arrival_cohort
from universal_baseball.prospect_arrival_validation import (
    calibration_diagnostics,
    paired_bootstrap_difference,
    proper_scores,
)
from universal_baseball.prospect_pbp_features import (
    FEATURE_FAMILIES,
    aggregate_prospect_pbp_features,
    attach_prospect_pbp_features,
    contact_shape_design,
    contact_shape_priors,
)


INCUMBENT_C = 1.0
PRODUCTION_REGRESSION = 50.0
CONTACT_REGRESSION = (50.0, 200.0, 600.0)
REGULARIZATION = (0.03, 0.1, 0.3, 1.0)
ORIGINS = (2021, 2022, 2023)


@dataclass(frozen=True, slots=True)
class Fit:
    model: LogisticRegression
    production_priors: tuple[float, float, float, float]
    pbp_priors: dict[str, float] | None
    family: str
    contact_regression: float


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-pbp-hurdle-test-result.json"),
    )
    return parser.parse_args()


def _history_stats(root: Path) -> pl.DataFrame:
    paths = sorted((root / "opportunity-history-sources-v2/tables").glob(
        "*/affiliated_season_stats.parquet"
    ))
    if not paths:
        raise FileNotFoundError("no affiliated history tables")
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")


def _career_hitting(root: Path) -> pl.DataFrame:
    tables = root / "career-mlb-outcome-inventory/tables"
    source = pl.concat([
        pl.read_parquet(tables / "mlb_batting_2015_2024.parquet"),
        pl.read_parquet(tables / "mlb_batting_2025_2025.parquet"),
    ])
    return source.select(
        "season", "player_id", pl.lit(1).alias("sport_id"),
        pl.col("batting_pa").alias("plate_appearances"),
        pl.col("batting_hits").alias("hits"),
        pl.col("batting_doubles").alias("doubles"),
        pl.col("batting_triples").alias("triples"),
        pl.col("batting_hr").alias("home_runs"),
        pl.col("batting_bb").alias("base_on_balls"),
        pl.lit(0).alias("intentional_walks"),
        pl.col("batting_hbp").alias("hit_by_pitch"),
    )


def _pbp_source(root: Path, year: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    season_root = root / "prospect-pbp-hurdle-source" / str(year)
    profile_paths = sorted(season_root.rglob("current_talent_game_profile_*.parquet"))
    summary_paths = sorted(season_root.rglob("current_talent_game_summary_*.parquet"))
    if len(profile_paths) != 5 or len(summary_paths) != 5:
        raise FileNotFoundError(f"{year} requires exactly five profile and summary tables")
    return (
        pl.concat([pl.read_parquet(path) for path in profile_paths]),
        pl.concat([pl.read_parquet(path) for path in summary_paths]),
    )


def _production_priors(frame: pl.DataFrame) -> tuple[float, float, float, float]:
    workload = frame.get_column("current_milb_workload").to_numpy()
    total = float(workload.sum())
    if total <= 0:
        raise ValueError("training cohort has no affiliated workload")
    return tuple(
        float(np.dot(frame.get_column(f"production_rate_{index}").to_numpy(), workload) / total)
        for index in range(1, 5)
    )


def _design(frame: pl.DataFrame, fit: Fit) -> np.ndarray:
    core = arrival_design(
        frame, feature_set="core", production_priors=fit.production_priors,
        production_regression=PRODUCTION_REGRESSION,
    )
    if fit.family == "core":
        return core
    assert fit.pbp_priors is not None
    pbp = contact_shape_design(
        frame, feature_family=fit.family, priors=fit.pbp_priors,
        regression_strength=fit.contact_regression,
    )
    return np.hstack([core, pbp])


def _fit(
    training: pl.DataFrame, *, target: str, family: str, c: float,
    contact_regression: float,
) -> Fit:
    observed = training.get_column(target).to_numpy()
    if np.unique(observed).size != 2:
        raise ValueError(f"{target} training data requires both outcomes")
    fit = Fit(
        model=LogisticRegression(C=c, max_iter=2_000),
        production_priors=_production_priors(training),
        pbp_priors=None if family == "core" else contact_shape_priors(training),
        family=family,
        contact_regression=contact_regression,
    )
    fit.model.fit(_design(training, fit), observed)
    return fit


def _predict(fit: Fit, frame: pl.DataFrame) -> np.ndarray:
    return fit.model.predict_proba(_design(frame, fit))[:, 1]


def _subgroups(
    frame: pl.DataFrame, observed: np.ndarray, incumbent: np.ndarray, candidate: np.ndarray
) -> list[dict[str, object]]:
    dimensions = {
        "level": frame.get_column("level_tier").to_list(),
        "age": ["16-19" if v < 20 else "20-22" if v < 23 else "23-25" if v < 26 else "26-30"
                for v in frame.get_column("age_years")],
        "workload": ["0" if v == 0 else "1-99" if v < 100 else "100-299" if v < 300 else "300+"
                     for v in frame.get_column("current_milb_workload")],
        "bat_side": frame.get_column("bat_side").to_list(),
        "pbp_coverage": ["observed" if v else "missing" for v in frame.get_column("pbp_observed")],
    }
    rows: list[dict[str, object]] = []
    for dimension, values in dimensions.items():
        labels = np.asarray(values, dtype=object)
        for group in sorted(set(values)):
            mask = labels == group
            y = observed[mask]
            base = proper_scores(y, incumbent[mask])
            richer = proper_scores(y, candidate[mask])
            rows.append({
                "dimension": dimension, "group": group, "players": int(mask.sum()),
                "successes": int(y.sum()),
                "supported": bool(mask.sum() >= 100 and y.sum() >= 5),
                "log_loss_difference": richer["log_loss"] - base["log_loss"],
                "brier_difference": richer["brier"] - base["brier"],
            })
    return rows


def _evaluate_outcome(
    cohorts: dict[int, pl.DataFrame], *, target: str, conditioning: str | None
) -> dict[str, object]:
    prepared = {
        year: frame if conditioning is None else frame.filter(pl.col(conditioning) == 1)
        for year, frame in cohorts.items()
    }
    train = prepared[2021]
    selection = prepared[2022]
    incumbent_selection_fit = _fit(
        train, target=target, family="core", c=INCUMBENT_C, contact_regression=0.0
    )
    incumbent_selection_probability = _predict(incumbent_selection_fit, selection)
    selection_observed = selection.get_column(target).to_numpy()
    incumbent_selection = proper_scores(selection_observed, incumbent_selection_probability)
    candidates: list[dict[str, object]] = []
    for family in FEATURE_FAMILIES:
        for c in REGULARIZATION:
            strengths = CONTACT_REGRESSION if family != "coverage" else (CONTACT_REGRESSION[0],)
            for strength in strengths:
                fit = _fit(train, target=target, family=family, c=c, contact_regression=strength)
                metrics = proper_scores(selection_observed, _predict(fit, selection))
                candidates.append({
                    "family": family, "regularization_c": c,
                    "contact_regression": strength, **metrics,
                })
    eligible = [row for row in candidates if row["brier"] <= incumbent_selection["brier"]]
    selected = min(eligible, key=lambda row: (row["log_loss"], row["brier"])) if eligible else None

    combined = pl.concat([prepared[2021], prepared[2022]], how="vertical_relaxed")
    outer = prepared[2023]
    incumbent_fit = _fit(
        combined, target=target, family="core", c=INCUMBENT_C, contact_regression=0.0
    )
    if selected is None:
        candidate_fit = incumbent_fit
        selected_spec = {"family": "core", "reason": "no_candidate_passed_selection_brier"}
    else:
        candidate_fit = _fit(
            combined, target=target, family=str(selected["family"]),
            c=float(selected["regularization_c"]),
            contact_regression=float(selected["contact_regression"]),
        )
        selected_spec = selected
    observed = outer.get_column(target).to_numpy()
    incumbent_probability = _predict(incumbent_fit, outer)
    candidate_probability = _predict(candidate_fit, outer)
    incumbent = proper_scores(observed, incumbent_probability)
    candidate = proper_scores(observed, candidate_probability)
    incumbent_calibration = calibration_diagnostics(observed, incumbent_probability, bins=5)
    candidate_calibration = calibration_diagnostics(observed, candidate_probability, bins=5)
    subgroups = _subgroups(outer, observed, incumbent_probability, candidate_probability)
    supported_damage = [
        row for row in subgroups
        if row["supported"] and row["log_loss_difference"] > 0 and row["brier_difference"] > 0
    ]
    calibration_ok = (
        candidate_calibration["intercept"] is not None
        and abs(float(candidate_calibration["intercept"]))
        <= 1.25 * max(abs(float(incumbent_calibration["intercept"])), 1e-6)
        and abs(float(candidate_calibration["slope"]) - 1.0)
        <= 1.25 * max(abs(float(incumbent_calibration["slope"]) - 1.0), 1e-6)
    )
    passed = bool(
        selected is not None
        and candidate["log_loss"] < incumbent["log_loss"]
        and candidate["brier"] < incumbent["brier"]
        and calibration_ok
        and not supported_damage
    )
    return {
        "target": target, "conditioning_column": conditioning,
        "cohorts": {
            str(year): {
                "players": frame.height,
                "positives": int(frame.get_column(target).sum()),
                "pbp_observed_players": int(frame.get_column("pbp_observed").sum()),
            }
            for year, frame in prepared.items()
        },
        "selection_incumbent": incumbent_selection,
        "selection_candidates": candidates,
        "selected_candidate": selected_spec,
        "outer_incumbent": incumbent,
        "outer_candidate": candidate,
        "paired_bootstrap": paired_bootstrap_difference(
            observed, incumbent_probability, candidate_probability
        ),
        "outer_incumbent_calibration": incumbent_calibration,
        "outer_candidate_calibration": candidate_calibration,
        "supported_subgroup_damage": supported_damage,
        "subgroups": subgroups,
        "outer_gate_passed": passed,
        "production_change_authorized": False,
    }


def main() -> int:
    args = _args()
    root = args.generated_root
    stats = _history_stats(root)
    membership = pl.read_parquet(
        root / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    demographics = pl.read_parquet(
        root / "player-demographics/tables/player-demographics.parquet"
    )
    draft = pl.read_parquet(root / "draft-history/draft-history.parquet")
    skill = pl.read_parquet(
        root / "phase2-arrival-skill-source/tables/affiliated_hitting_components.parquet"
    )
    outcome_skill = _career_hitting(root)
    snapshots = pl.read_parquet(
        root / "opportunity-history-sources-v2/tables/hitter_snapshots.parquet"
    )
    cohorts: dict[int, pl.DataFrame] = {}
    source_metrics: dict[str, object] = {}
    for year in ORIGINS:
        profile, summary = _pbp_source(root, year)
        features = aggregate_prospect_pbp_features(profile, summary, predictor_year=year)
        cohort = build_arrival_cohort(
            snapshots, stats, membership, skill, snapshot_year=year, horizon=1,
            player_type="hitter", demographics=demographics, draft_history=draft,
            outcome_skill_stats=outcome_skill,
        )
        cohorts[year] = attach_prospect_pbp_features(cohort, features)
        source_metrics[str(year)] = {
            "profile_rows": profile.height,
            "summary_rows": summary.height,
            "feature_players": features.height,
            "profile_contacts": int(features.get_column("pbp_contact_count").sum()),
            "minimum_game_date": profile.get_column("game_date").min().isoformat(),
            "maximum_game_date": profile.get_column("game_date").max().isoformat(),
        }
    report = {
        "report_schema_version": "0.1",
        "created_date": date.today().isoformat(),
        "status": "retrospective_outer_test_not_fresh_confirmation",
        "plan": "docs/prospect-pbp-hurdle-test-plan.md",
        "source_semantics": "retrospective_event_cutoff_corrected_not_vintage",
        "source_metrics": source_metrics,
        "fixed_settings": {
            "origins": list(ORIGINS), "outcome_horizon_years": 1,
            "incumbent_c": INCUMBENT_C,
            "production_regression": PRODUCTION_REGRESSION,
            "feature_families": list(FEATURE_FAMILIES),
            "contact_regression": list(CONTACT_REGRESSION),
            "regularization_c": list(REGULARIZATION),
            "neutral_woba_weights": NEUTRAL_WOBA_WEIGHTS,
        },
        "meaningful_opportunity": _evaluate_outcome(
            cohorts, target="meaningful_role_within_horizon", conditioning=None
        ),
        "positive_component_given_meaningful": _evaluate_outcome(
            cohorts, target="positive_component_role_within_horizon",
            conditioning="meaningful_role_within_horizon",
        ),
        "binding_interpretation": {
            "outside_fv_used": False,
            "catcher_preference_added": False,
            "missing_pbp_players_dropped": False,
            "pitch_sequence_features_used": False,
            "current_values_changed": False,
            "fresh_later_confirmation_required": True,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
