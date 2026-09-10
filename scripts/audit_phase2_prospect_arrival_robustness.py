#!/usr/bin/env python3
"""Run an embargoed nested robustness audit of prospect-arrival features."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.player_demographics import normalize_birth_country
from universal_baseball.prospect_arrival import (
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)
from universal_baseball.prospect_arrival_validation import (
    CandidateSpec,
    ForecastExperimentProtocol,
    calibration_diagnostics,
    common_cohort_fingerprint,
    completed_evaluation_years,
    paired_bootstrap_difference,
    proper_scores,
    select_nested_candidate,
)


HORIZON = 2
OUTER_YEAR = 2023
EVALUATION_SPECS = ((2021, (2018,)), (2022, (2018,)), (2023, (2018, 2021)))
FEATURE_SETS = (
    "core",
    "handedness",
    "origin",
    "stable_demographics",
    "stable_interactions",
    "development_interactions",
    "role_production_interactions",
    "baseball_interactions",
    "baseball_demographics",
    "draft_pedigree",
    "baseball_pedigree",
)
REGULARIZATION = (0.03, 0.1, 0.3, 1.0)
PRODUCTION_REGRESSION = (0.0, 50.0, 200.0, 600.0)
INCUMBENT = CandidateSpec("core", 1.0)
OUTCOMES = (
    ("arrival", "arrived_within_horizon", None),
    ("meaningful_role", "meaningful_role_within_horizon", None),
    ("established_role", "established_role_within_horizon", None),
    (
        "positive_component_given_meaningful",
        "positive_component_role_within_horizon",
        "meaningful_role_within_horizon",
    ),
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-arrival-nested-robustness-result.json"),
    )
    return parser.parse_args()


def _history_stats(root: Path) -> pl.DataFrame:
    paths = sorted(
        (root / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
    if not paths:
        raise FileNotFoundError("no affiliated history tables")
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")


def _career_component_stats(root: Path, player_type: str) -> pl.DataFrame:
    tables = root / "career-mlb-outcome-inventory/tables"
    if player_type == "hitter":
        source = pl.concat(
            [
                pl.read_parquet(tables / "mlb_batting_2015_2024.parquet"),
                pl.read_parquet(tables / "mlb_batting_2025_2025.parquet"),
            ]
        )
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
    source = pl.concat(
        [
            pl.read_parquet(tables / "mlb_pitching_2015_2024.parquet"),
            pl.read_parquet(tables / "mlb_pitching_2025_2025.parquet"),
        ]
    )
    return source.select(
        "season", "player_id", pl.lit(1).alias("sport_id"),
        pl.col("pitching_bf").alias("batters_faced"),
        pl.col("pitching_so").alias("strike_outs"),
        pl.col("pitching_ubb").alias("base_on_balls"),
        pl.lit(0).alias("intentional_walks"),
        pl.col("pitching_hbp").alias("hit_batters"),
        pl.col("pitching_hr").alias("home_runs"),
    )


def _score(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    *,
    player_type: str,
    outcome: str,
    target: str,
    candidate: CandidateSpec,
) -> tuple[dict[str, object], np.ndarray]:
    fit = fit_arrival_model(
        training,
        player_type=player_type,
        target_column=target,
        outcome_name=outcome,
        feature_set=candidate.feature_set,
        regularization_c=candidate.regularization_c,
        production_regression=candidate.production_regression,
    )
    probability = (
        predict_arrival(fit, evaluation)
        .get_column(f"predicted_two_year_{outcome}_probability")
        .to_numpy()
    )
    metrics = proper_scores(evaluation.get_column(target).to_numpy(), probability)
    metrics.update(
        {
            "model_id": candidate.model_id,
            "feature_set": candidate.feature_set,
            "regularization_c": candidate.regularization_c,
            "production_regression": candidate.production_regression,
        }
    )
    return metrics, probability


def _subgroup_rows(
    evaluation: pl.DataFrame,
    observed: np.ndarray,
    incumbent: np.ndarray,
    candidate: np.ndarray,
) -> list[dict[str, object]]:
    dimensions: dict[str, list[str]] = {
        "level": evaluation.get_column("level_tier").cast(pl.String).to_list(),
        "age": [
            "16-19" if age < 20 else "20-22" if age < 23 else "23-25" if age < 26 else "26-30"
            for age in evaluation.get_column("age_years").to_list()
        ],
        "workload": [
            "0" if value == 0 else "1-99" if value < 100 else "100-299" if value < 300 else "300+"
            for value in evaluation.get_column("current_milb_workload").to_list()
        ],
        "birth_country": [
            normalize_birth_country(value)
            for value in evaluation.get_column("birth_country").to_list()
        ],
        "bat_side": evaluation.get_column("bat_side").cast(pl.String).to_list(),
        "throw_hand": evaluation.get_column("pitch_hand").cast(pl.String).to_list(),
        "entry_path": [
            "rule4_draft" if drafted else "international_or_other"
            for drafted in evaluation.get_column("rule4_drafted").to_list()
        ],
    }
    rows: list[dict[str, object]] = []
    for dimension, labels in dimensions.items():
        label_array = np.asarray(labels, dtype=object)
        for group in sorted(set(labels)):
            mask = label_array == group
            y = observed[mask]
            base = proper_scores(y, incumbent[mask])
            challenger = proper_scores(y, candidate[mask])
            rows.append(
                {
                    "dimension": dimension,
                    "group": group,
                    "players": int(mask.sum()),
                    "successes": int(y.sum()),
                    "supported": bool(mask.sum() >= 100 and y.sum() >= 5),
                    "incumbent_log_loss": base["log_loss"],
                    "candidate_log_loss": challenger["log_loss"],
                    "log_loss_difference": challenger["log_loss"] - base["log_loss"],
                    "incumbent_brier": base["brier"],
                    "candidate_brier": challenger["brier"],
                    "brier_difference": challenger["brier"] - base["brier"],
                }
            )
    return rows


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
    draft_history = pl.read_parquet(root / "draft-history/draft-history.parquet")
    normalized = demographics.get_column("birth_country").map_elements(
        normalize_birth_country, return_dtype=pl.String
    )
    raw = demographics.get_column("birth_country").fill_null("UNKNOWN")
    normalization = {
        "source_rows": demographics.height,
        "rows_changed": int((normalized != raw).sum()),
        "raw_distinct": demographics.get_column("birth_country").n_unique(),
        "normalized_distinct": normalized.n_unique(),
    }
    candidates = [
        CandidateSpec(feature_set, regularization_c, production_regression)
        for feature_set in FEATURE_SETS
        for regularization_c in REGULARIZATION
        for production_regression in PRODUCTION_REGRESSION
    ]
    if INCUMBENT not in candidates:
        raise AssertionError("incumbent must be in candidate grid")
    eligible_years = completed_evaluation_years(
        outer_year=OUTER_YEAR,
        horizon=HORIZON,
        evaluation_years=tuple(year for year, _ in EVALUATION_SPECS),
    )
    results: dict[str, object] = {}
    for player_type in ("hitter", "pitcher"):
        skill_file = (
            "affiliated_hitting_components.parquet"
            if player_type == "hitter"
            else "affiliated_pitching_components.parquet"
        )
        skill = pl.read_parquet(root / "phase2-arrival-skill-source/tables" / skill_file)
        outcome_skill = _career_component_stats(root, player_type)
        snapshots = pl.read_parquet(
            root
            / "opportunity-history-sources-v2/tables"
            / f"{player_type}_snapshots.parquet"
        )
        cohorts = {
            year: build_arrival_cohort(
                snapshots,
                stats,
                membership,
                skill,
                snapshot_year=year,
                horizon=HORIZON,
                player_type=player_type,
                demographics=demographics,
                draft_history=draft_history,
                outcome_skill_stats=outcome_skill,
            )
            for year in (2018, 2021, 2022, 2023)
        }
        player_results: dict[str, object] = {}
        for outcome, target, conditioning_column in OUTCOMES:
            selection_rows: list[dict[str, object]] = []
            for evaluation_year, training_years in EVALUATION_SPECS:
                if evaluation_year not in eligible_years:
                    continue
                training = pl.concat([cohorts[year] for year in training_years])
                evaluation = cohorts[evaluation_year]
                if conditioning_column is not None:
                    training = training.filter(pl.col(conditioning_column) == 1)
                    evaluation = evaluation.filter(pl.col(conditioning_column) == 1)
                for candidate in candidates:
                    metrics, _ = _score(
                        training,
                        evaluation,
                        player_type=player_type,
                        outcome=outcome,
                        target=target,
                        candidate=candidate,
                    )
                    metrics["evaluation_year"] = evaluation_year
                    selection_rows.append(metrics)
            selected_id = select_nested_candidate(
                selection_rows,
                eligible_years=eligible_years,
                incumbent_id=INCUMBENT.model_id,
            )
            selected = next(
                candidate for candidate in candidates if candidate.model_id == selected_id
            )
            outer_training_years = next(
                years for year, years in EVALUATION_SPECS if year == OUTER_YEAR
            )
            outer_training = pl.concat(
                [cohorts[year] for year in outer_training_years]
            )
            outer_evaluation = cohorts[OUTER_YEAR]
            if conditioning_column is not None:
                outer_training = outer_training.filter(
                    pl.col(conditioning_column) == 1
                )
                outer_evaluation = outer_evaluation.filter(
                    pl.col(conditioning_column) == 1
                )
            incumbent_metrics, incumbent_probability = _score(
                outer_training,
                outer_evaluation,
                player_type=player_type,
                outcome=outcome,
                target=target,
                candidate=INCUMBENT,
            )
            selected_metrics, selected_probability = _score(
                outer_training,
                outer_evaluation,
                player_type=player_type,
                outcome=outcome,
                target=target,
                candidate=selected,
            )
            observed = outer_evaluation.get_column(target).to_numpy()
            protocol = ForecastExperimentProtocol(
                name=f"prospect-{player_type}-{outcome}",
                target=target,
                player_universe=(
                    "all affiliated pre-MLB players age 16-30 in the dated snapshot; "
                    "failures and non-arrivals retained"
                ),
                horizon=HORIZON,
                incumbent_id=INCUMBENT.model_id,
                candidate_ids=tuple(candidate.model_id for candidate in candidates),
                selection_origins=eligible_years,
                outer_origin=OUTER_YEAR,
                outcome_available_through=args.as_of_date.year - 1,
            )
            player_results[outcome] = {
                "experiment_protocol": protocol.as_dict(include_candidate_ids=False),
                "conditioning_column": conditioning_column,
                "selection_evaluation_years": list(eligible_years),
                "selection_scores": selection_rows,
                "selected_candidate": {
                    "model_id": selected.model_id,
                    "feature_set": selected.feature_set,
                    "regularization_c": selected.regularization_c,
                    "production_regression": selected.production_regression,
                },
                "outer_year": OUTER_YEAR,
                "outer_training_years": list(outer_training_years),
                "incumbent": incumbent_metrics,
                "candidate": selected_metrics,
                "paired_bootstrap": paired_bootstrap_difference(
                    observed,
                    incumbent_probability,
                    selected_probability,
                ),
                "outer_cohort_fingerprint": common_cohort_fingerprint(
                    outer_evaluation.get_column("player_id").to_numpy(),
                    observed,
                    {
                        INCUMBENT.model_id: incumbent_probability,
                        selected.model_id: selected_probability,
                    },
                ),
                "incumbent_calibration": calibration_diagnostics(
                    observed, incumbent_probability
                ),
                "candidate_calibration": calibration_diagnostics(
                    observed, selected_probability
                ),
                "subgroups": _subgroup_rows(
                    outer_evaluation,
                    observed,
                    incumbent_probability,
                    selected_probability,
                ),
            }
        results[player_type] = player_results
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "retrospective_nested_process_audit_not_confirmation",
        "horizon_years": HORIZON,
        "outer_year": OUTER_YEAR,
        "country_normalization": normalization,
        "candidate_grid": {
            "feature_sets": list(FEATURE_SETS),
            "regularization_c": list(REGULARIZATION),
            "production_regression": list(PRODUCTION_REGRESSION),
            "candidate_count": len(candidates),
        },
        "guardrails": {
            "same_players_for_every_comparison": True,
            "non_arrivals_retained_as_zero_outcomes": True,
            "proper_score_selection": "log_loss_with_brier_no_harm",
            "two_year_outcome_embargo": True,
            "player_level_paired_bootstrap": True,
            "country_used_for_arrival_or_role_not_direct_talent": True,
            "draft_evidence_known_by_snapshot_year_only": True,
            "draft_dollars_compared_within_draft_year": True,
            "undrafted_international_path_explicit": True,
            "physical_current_profile_fields_excluded": True,
            "production_values_changed": False,
            "established_role_definition": {
                "hitter": "one 400 PA season or two 300 PA seasons within two years",
                "pitcher": "one 400 BF season or two 200 BF seasons within two years",
            },
            "positive_component_role_definition": (
                "at least 200 future MLB PA/BF in a season and at-least-league-"
                "average neutral batting wOBA components or fielding-independent "
                "pitching components"
            ),
            "quality_hurdle_factorization": (
                "P(meaningful role) multiplied later by P(positive components "
                "given meaningful role); conditional quality is scored only among "
                "players meeting the observed workload hurdle"
            ),
            "positive_component_is_not_whole_player_war": True,
            "hitter_outcome_walk_field": (
                "total BB because the certified career backbone omits IBB; applied "
                "consistently to player and league rates"
            ),
            "shortened_2020_workload_scaled_to_162_games": True,
            "fresh_confirmation_still_required": True,
        },
        "results": results,
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
