#!/usr/bin/env python3
"""Test a cutoff-safe conditional two-year prospect component-WAR bridge."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from universal_baseball.historical_hitter_performance import (
    build_historical_hitter_performance_paths,
)
from universal_baseball.historical_pitcher_performance import (
    build_historical_pitcher_performance_paths,
)
from universal_baseball.prospect_arrival import (
    ArrivalFit,
    arrival_design,
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)
from universal_baseball.prospect_arrival_validation import (
    common_continuous_cohort_fingerprint,
    continuous_scores,
    paired_continuous_bootstrap_difference,
)
from universal_baseball.storage import sha256_file


TRAINING_ORIGIN = 2018
OUTER_ORIGIN = 2021
HORIZON = 2
RIDGE_ALPHA = 100.0
RATE_REGRESSION = 200.0
SHORTENED_2020_SCALE = 2.7
CORE_FEATURE_NAMES = (
    "age",
    "current_workload",
    "prior_workload",
    "prior_affiliated_seasons",
    "on_40man",
    "level_A_OR_BELOW",
    "level_AA",
    "level_AAA",
    "level_INACTIVE",
    "role_C",
    "role_MIDDLE_INFIELD",
    "role_OUTFIELD",
    "role_CORNER",
    "role_STARTER",
    "role_SWINGMAN",
    "production_rate_1",
    "production_rate_2",
    "production_rate_3",
    "production_rate_4",
)


@dataclass(slots=True)
class BridgeFit:
    arrival_fit: ArrivalFit
    scaler: StandardScaler
    ridge: Ridge
    conditional_mean: float
    training_arrivals: int
    training_outcome_threshold_counts: dict[str, int]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-conditional-war-bridge-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-conditional-war-bridge-result.md"),
    )
    return parser.parse_args()


def _history_stats(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = sorted(
        (root / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
    if not paths:
        raise FileNotFoundError("no affiliated history tables")
    return pl.concat(
        [pl.read_parquet(path) for path in paths], how="vertical_relaxed"
    ), paths


def _annual_skeleton(
    player_ids: list[int], *, player_type: str, origin: int
) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "path_player_id": int(player_id),
                "player_type": player_type,
                "outcome_tier_v2": "unknown",
                "career_role": "unknown",
                "path_year": season - origin,
                "source_season": season,
                "adjusted_workload": 0.0,
                "annual_role": "inactive",
            }
            for player_id in player_ids
            for season in range(origin + 1, origin + HORIZON + 1)
        ]
    )


def _hitter_outcomes(
    cohort: pl.DataFrame,
    hitting: pl.DataFrame,
    *,
    origin: int,
    runs_per_win: float,
) -> pl.DataFrame:
    annual = (
        _annual_skeleton(
            cohort["player_id"].to_list(), player_type="hitter", origin=origin
        )
        .join(
            hitting.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("batting_plate_appearances")
                .cast(pl.Float64)
                .alias("raw_workload"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col("raw_workload").fill_null(0.0),
            pl.when(pl.col("source_season") == 2020)
            .then(pl.col("raw_workload").fill_null(0.0) * SHORTENED_2020_SCALE)
            .otherwise(pl.col("raw_workload").fill_null(0.0))
            .alias("adjusted_workload"),
            pl.when(pl.col("raw_workload").fill_null(0.0) > 0)
            .then(pl.lit("hitter"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("raw_workload")
    )
    return _summarize_paths(
        build_historical_hitter_performance_paths(
            annual,
            hitting,
            runs_per_win=runs_per_win,
            shortened_2020_scale=SHORTENED_2020_SCALE,
        )
    )


def _pitcher_outcomes(
    cohort: pl.DataFrame,
    pitching: pl.DataFrame,
    *,
    origin: int,
    runs_per_win: float,
) -> pl.DataFrame:
    annual = (
        _annual_skeleton(
            cohort["player_id"].to_list(), player_type="pitcher", origin=origin
        )
        .join(
            pitching.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("pitching_bf").cast(pl.Float64).alias("raw_workload"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col("raw_workload").fill_null(0.0),
            pl.when(pl.col("source_season") == 2020)
            .then(pl.col("raw_workload").fill_null(0.0) * SHORTENED_2020_SCALE)
            .otherwise(pl.col("raw_workload").fill_null(0.0))
            .alias("adjusted_workload"),
            pl.when(pl.col("raw_workload").fill_null(0.0) > 0)
            .then(pl.lit("unknown"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("raw_workload")
    )
    return _summarize_paths(
        build_historical_pitcher_performance_paths(
            annual,
            pitching,
            runs_per_win=runs_per_win,
            shortened_2020_scale=SHORTENED_2020_SCALE,
        )
    )


def _summarize_paths(paths: pl.DataFrame) -> pl.DataFrame:
    return (
        paths.group_by("path_player_id")
        .agg(
            pl.col("observed_component_war")
            .sum()
            .alias("observed_two_year_component_war"),
            pl.col("adjusted_workload").sum().alias("observed_two_year_workload"),
        )
        .rename({"path_player_id": "player_id"})
    )


def _subgroups(frame: pl.DataFrame) -> list[dict[str, object]]:
    workload = [
        "0" if value == 0 else "1-99" if value < 100 else "100-299" if value < 300 else "300+"
        for value in frame["current_milb_workload"].to_list()
    ]
    dimensions = {
        "level": frame["level_tier"].cast(pl.String).to_list(),
        "role": frame["role_tier"].cast(pl.String).to_list(),
        "evidence": workload,
        "hand": frame["pitch_hand"].cast(pl.String).to_list(),
    }
    y = frame["observed_two_year_component_war"].to_numpy()
    baseline = frame["pooled_prediction"].to_numpy()
    candidate = frame["ridge_prediction"].to_numpy()
    arrival_flags = frame["observed_arrival"].to_numpy()
    rows = []
    for dimension, labels in dimensions.items():
        values = np.asarray(labels, dtype=object)
        for group in sorted(set(labels)):
            mask = values == group
            if int(mask.sum()) < 100:
                continue
            base = continuous_scores(y[mask], baseline[mask])
            challenger = continuous_scores(y[mask], candidate[mask])
            arrivals = int(arrival_flags[mask].sum())
            rows.append(
                {
                    "dimension": dimension,
                    "group": group,
                    "players": int(mask.sum()),
                    "arrivals": arrivals,
                    "supported": bool(mask.sum() >= 100 and arrivals >= 5),
                    "baseline_rmse": base["rmse"],
                    "candidate_rmse": challenger["rmse"],
                    "baseline_mae": base["mae"],
                    "candidate_mae": challenger["mae"],
                }
            )
    return rows


def _fit_bridge(training: pl.DataFrame, *, player_type: str) -> BridgeFit:
    arrival_fit = fit_arrival_model(training, player_type=player_type)
    training_arrivals = training.filter(pl.col("observed_arrival"))
    if training_arrivals.height < 50:
        raise ValueError("conditional WAR bridge requires at least 50 training arrivals")
    x_train = arrival_design(
        training_arrivals,
        feature_set="core",
        production_priors=arrival_fit.production_priors,
        production_regression=RATE_REGRESSION,
    )
    scaler = StandardScaler().fit(x_train)
    ridge = Ridge(alpha=RIDGE_ALPHA).fit(
        scaler.transform(x_train),
        training_arrivals["observed_two_year_component_war"].to_numpy(),
    )
    if len(ridge.coef_) != len(CORE_FEATURE_NAMES):
        raise ValueError("core conditional-WAR feature names do not match the design")
    conditional_mean = float(
        training_arrivals["observed_two_year_component_war"].mean()
    )
    training_y = training_arrivals["observed_two_year_component_war"].to_numpy()
    return BridgeFit(
        arrival_fit=arrival_fit,
        scaler=scaler,
        ridge=ridge,
        conditional_mean=conditional_mean,
        training_arrivals=training_arrivals.height,
        training_outcome_threshold_counts={
            f"war_at_least_{threshold:g}": int((training_y >= threshold).sum())
            for threshold in (0.0, 0.25, 0.5, 1.0, 2.0)
        },
    )


def _score_bridge(evaluation: pl.DataFrame, fit: BridgeFit) -> dict[str, object]:
    scored = predict_arrival(fit.arrival_fit, evaluation)
    evaluation_arrivals = evaluation.filter(pl.col("observed_arrival"))
    if evaluation_arrivals.height < 50:
        raise ValueError("conditional WAR bridge requires at least 50 outer arrivals")
    x_outer = arrival_design(
        scored,
        feature_set="core",
        production_priors=fit.arrival_fit.production_priors,
        production_regression=RATE_REGRESSION,
    )
    conditional_candidate = fit.ridge.predict(fit.scaler.transform(x_outer))
    probability = scored["predicted_two_year_arrival_probability"].to_numpy()
    scored = scored.with_columns(
        pl.Series(
            "pooled_conditional_war", np.full(scored.height, fit.conditional_mean)
        ),
        pl.Series("ridge_conditional_war", conditional_candidate),
        pl.Series("pooled_prediction", probability * fit.conditional_mean),
        pl.Series("ridge_prediction", probability * conditional_candidate),
    )
    y = scored["observed_two_year_component_war"].to_numpy()
    baseline = scored["pooled_prediction"].to_numpy()
    candidate = scored["ridge_prediction"].to_numpy()
    arrived = scored["observed_arrival"].to_numpy()
    outer_conditional_candidate = conditional_candidate[arrived]
    outer_conditional_y = y[arrived]
    outer_conditional_baseline = np.full(arrived.sum(), fit.conditional_mean)
    end_to_end_baseline = continuous_scores(y, baseline)
    end_to_end_candidate = continuous_scores(y, candidate)
    conditional_baseline = continuous_scores(
        outer_conditional_y, outer_conditional_baseline
    )
    conditional_score = continuous_scores(
        outer_conditional_y, outer_conditional_candidate
    )
    paired = paired_continuous_bootstrap_difference(y, baseline, candidate)
    decision_checks = {
        "end_to_end_rmse_improved": bool(
            end_to_end_candidate["rmse"] < end_to_end_baseline["rmse"]
        ),
        "end_to_end_mae_improved": bool(
            end_to_end_candidate["mae"] < end_to_end_baseline["mae"]
        ),
        "absolute_bias_not_worse": bool(
            abs(end_to_end_candidate["bias"]) <= abs(end_to_end_baseline["bias"])
        ),
        "arrived_player_rmse_not_worse": bool(
            conditional_score["rmse"] <= conditional_baseline["rmse"]
        ),
    }
    outcome_thresholds = {
        f"war_at_least_{threshold:g}": {
            "all_players": int((y >= threshold).sum()),
            "arrived_players": int((outer_conditional_y >= threshold).sum()),
        }
        for threshold in (0.0, 0.25, 0.5, 1.0, 2.0)
    }
    return {
        "players": scored.height,
        "training_arrivals": fit.training_arrivals,
        "outer_arrivals": evaluation_arrivals.height,
        "training_conditional_mean_war": fit.conditional_mean,
        "training_outcome_threshold_counts": (
            fit.training_outcome_threshold_counts
        ),
        "ridge_alpha": RIDGE_ALPHA,
        "rate_regression_opportunities": RATE_REGRESSION,
        "end_to_end_baseline": end_to_end_baseline,
        "end_to_end_candidate": end_to_end_candidate,
        "conditional_on_observed_arrival_baseline": conditional_baseline,
        "conditional_on_observed_arrival_candidate": conditional_score,
        "paired_difference": paired,
        "decision_checks": decision_checks,
        "promising_development_evidence": all(decision_checks.values()),
        "observed_outcome_threshold_counts": outcome_thresholds,
        "cohort_fingerprint": common_continuous_cohort_fingerprint(
            scored["player_id"].to_numpy(),
            y,
            {"pooled": baseline, "ridge": candidate},
        ),
        "ridge_coefficient_l2_norm": float(np.linalg.norm(fit.ridge.coef_)),
        "standardized_ridge_coefficients": sorted(
            (
                {"feature": feature, "coefficient": float(coefficient)}
                for feature, coefficient in zip(
                    CORE_FEATURE_NAMES, fit.ridge.coef_, strict=True
                )
            ),
            key=lambda row: abs(row["coefficient"]),
            reverse=True,
        ),
        "ridge_conditional_prediction_distribution": {
            "minimum": float(np.min(conditional_candidate)),
            "p01": float(np.quantile(conditional_candidate, 0.01)),
            "median": float(np.median(conditional_candidate)),
            "p99": float(np.quantile(conditional_candidate, 0.99)),
            "maximum": float(np.max(conditional_candidate)),
            "negative_predictions": int((conditional_candidate < 0).sum()),
        },
        "subgroups": _subgroups(scored),
    }


def main() -> int:
    args = _args()
    root = args.generated_root
    stats, stat_paths = _history_stats(root)
    history_root = root / "opportunity-history-sources-v2/tables"
    membership_path = (
        root
        / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    membership = pl.read_parquet(membership_path)
    environment_path = Path("docs/prospect-component-uncertainty-result.json")
    plan_path = Path("docs/prospect-conditional-war-bridge-plan.md")
    stability_plan_path = Path(
        "docs/prospect-conditional-war-bridge-stability-plan.md"
    )
    runs_per_win = float(
        json.loads(environment_path.read_text(encoding="utf-8"))["runs_per_win"]
    )
    demographics_path = root / "player-demographics/tables/player-demographics.parquet"
    demographics = pl.read_parquet(demographics_path)
    hitting_path = (
        root
        / "career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet"
    )
    pitching_path = (
        root
        / "career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet"
    )
    hitting = pl.read_parquet(hitting_path)
    pitching = pl.read_parquet(pitching_path)
    sources = [
        *stat_paths,
        membership_path,
        demographics_path,
        hitting_path,
        pitching_path,
        environment_path,
        plan_path,
        stability_plan_path,
    ]
    results = {}
    stability_results = {}
    for player_type in ("hitter", "pitcher"):
        snapshot_path = history_root / f"{player_type}_snapshots.parquet"
        skill_path = (
            root
            / "phase2-arrival-skill-source/tables"
            / f"affiliated_{'hitting' if player_type == 'hitter' else 'pitching'}_components.parquet"
        )
        snapshots = pl.read_parquet(snapshot_path)
        skill = pl.read_parquet(skill_path)
        cohorts = {}
        for origin in (TRAINING_ORIGIN, OUTER_ORIGIN, 2022, 2023):
            cohort = build_arrival_cohort(
                snapshots,
                stats,
                membership,
                skill,
                snapshot_year=origin,
                horizon=HORIZON,
                player_type=player_type,
                demographics=demographics,
            )
            outcome = (
                _hitter_outcomes(
                    cohort, hitting, origin=origin, runs_per_win=runs_per_win
                )
                if player_type == "hitter"
                else _pitcher_outcomes(
                    cohort, pitching, origin=origin, runs_per_win=runs_per_win
                )
            )
            cohorts[origin] = (
                cohort.join(outcome, on="player_id", how="left", validate="1:1")
                .with_columns(
                    pl.col("observed_two_year_component_war").fill_null(0.0),
                    pl.col("observed_two_year_workload").fill_null(0.0),
                )
                .with_columns(
                    (pl.col("observed_two_year_workload") > 0).alias(
                        "observed_arrival"
                    )
                )
            )
            mismatch = cohorts[origin].filter(
                pl.col("observed_arrival")
                != (pl.col("arrived_within_horizon") == 1)
            )
            if mismatch.height:
                raise ValueError(
                    f"{player_type} {origin} workload and arrival labels disagree"
                )
        fit = _fit_bridge(cohorts[TRAINING_ORIGIN], player_type=player_type)
        results[player_type] = _score_bridge(cohorts[OUTER_ORIGIN], fit)
        stability_results[player_type] = {
            str(origin): _score_bridge(cohorts[origin], fit)
            for origin in (2022, 2023)
        }
        sources.extend([snapshot_path, skill_path])

    protocol = {
        "training_origin": TRAINING_ORIGIN,
        "outer_origin": OUTER_ORIGIN,
        "horizon_years": HORIZON,
        "ridge_alpha": RIDGE_ALPHA,
        "rate_regression_opportunities": RATE_REGRESSION,
        "candidate": "arrival_probability_x_standardized_core_ridge_conditional_war",
        "baseline": "arrival_probability_x_pooled_conditional_war",
        "frozen_plan_sha256": sha256_file(plan_path),
    }
    protocol["fingerprint"] = sha256(
        json.dumps(protocol, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    stability_passed = all(
        all(result["decision_checks"].values())
        for years in stability_results.values()
        for result in years.values()
    )
    report = {
        "report_schema_version": 1,
        "as_of_date": args.as_of_date.isoformat(),
        "status": "retrospective_development_not_confirmation",
        "protocol": protocol,
        "results": results,
        "stability_protocol": {
            "fit_origin": TRAINING_ORIGIN,
            "evaluation_origins": [2022, 2023],
            "horizon_years": HORIZON,
            "refit_or_recalibration": False,
            "frozen_plan_sha256": sha256_file(stability_plan_path),
        },
        "stability_results": stability_results,
        "stability_passed": stability_passed,
        "boundaries": {
            "all_non_arrivals_retained": True,
            "demographics_used_as_talent": False,
            "outside_fv_used": False,
            "organization_used": False,
            "predictions_clipped": False,
            "production_values_changed": False,
        },
        "sources": {path.as_posix(): sha256_file(path) for path in sorted(set(sources))},
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    hitter = results["hitter"]
    pitcher = results["pitcher"]
    hitter_drivers = ", ".join(
        f"{row['feature']} ({row['coefficient']:+.3f})"
        for row in hitter["standardized_ridge_coefficients"][:5]
    )
    pitcher_drivers = ", ".join(
        f"{row['feature']} ({row['coefficient']:+.3f})"
        for row in pitcher["standardized_ridge_coefficients"][:5]
    )
    hitter_2022 = stability_results["hitter"]["2022"]
    hitter_2023 = stability_results["hitter"]["2023"]
    pitcher_2022 = stability_results["pitcher"]["2022"]
    pitcher_2023 = stability_results["pitcher"]["2023"]
    markdown = f"""# Prospect conditional-WAR bridge result

Status: **retrospective development; no production change**.

The fixed candidate uses only cutoff-known core baseball evidence to estimate two-year
component WAR conditional on arrival, then multiplies by the unchanged arrival
probability. Non-arrivals remain zero in the end-to-end score.

| Type | Players | Arrivals | Baseline RMSE | Ridge RMSE | Baseline MAE | Ridge MAE |
|---|---:|---:|---:|---:|---:|---:|
| Hitters | {hitter['players']:,} | {hitter['outer_arrivals']:,} | {hitter['end_to_end_baseline']['rmse']:.3f} | {hitter['end_to_end_candidate']['rmse']:.3f} | {hitter['end_to_end_baseline']['mae']:.3f} | {hitter['end_to_end_candidate']['mae']:.3f} |
| Pitchers | {pitcher['players']:,} | {pitcher['outer_arrivals']:,} | {pitcher['end_to_end_baseline']['rmse']:.3f} | {pitcher['end_to_end_candidate']['rmse']:.3f} | {pitcher['end_to_end_baseline']['mae']:.3f} | {pitcher['end_to_end_candidate']['mae']:.3f} |

Hitter promising gate: **{hitter['promising_development_evidence']}**. Pitcher
promising gate: **{pitcher['promising_development_evidence']}**. These are development
decisions only; the 2021 cohort is already exposed and cannot promote a model.

Both candidates improve end-to-end RMSE and MAE with wholly favorable paired
intervals, and both improve RMSE among players who actually arrive. The frozen gate
still fails because absolute mean bias moves slightly farther from zero. Preserve the
form for later confirmation; do not recalibrate it on this exposed cohort.

Largest standardized hitter coefficients: {hitter_drivers}. Largest standardized
pitcher coefficients: {pitcher_drivers}. These are predictive diagnostics, not causal
effects or player bonuses.

## Unchanged-fit stability extension

| Type / origin | Baseline RMSE | Ridge RMSE | Baseline MAE | Ridge MAE | Arrived-player RMSE change |
|---|---:|---:|---:|---:|---:|
| Hitter 2022 | {hitter_2022['end_to_end_baseline']['rmse']:.3f} | {hitter_2022['end_to_end_candidate']['rmse']:.3f} | {hitter_2022['end_to_end_baseline']['mae']:.3f} | {hitter_2022['end_to_end_candidate']['mae']:.3f} | {hitter_2022['conditional_on_observed_arrival_baseline']['rmse']:.3f} to {hitter_2022['conditional_on_observed_arrival_candidate']['rmse']:.3f} |
| Hitter 2023 | {hitter_2023['end_to_end_baseline']['rmse']:.3f} | {hitter_2023['end_to_end_candidate']['rmse']:.3f} | {hitter_2023['end_to_end_baseline']['mae']:.3f} | {hitter_2023['end_to_end_candidate']['mae']:.3f} | {hitter_2023['conditional_on_observed_arrival_baseline']['rmse']:.3f} to {hitter_2023['conditional_on_observed_arrival_candidate']['rmse']:.3f} |
| Pitcher 2022 | {pitcher_2022['end_to_end_baseline']['rmse']:.3f} | {pitcher_2022['end_to_end_candidate']['rmse']:.3f} | {pitcher_2022['end_to_end_baseline']['mae']:.3f} | {pitcher_2022['end_to_end_candidate']['mae']:.3f} | {pitcher_2022['conditional_on_observed_arrival_baseline']['rmse']:.3f} to {pitcher_2022['conditional_on_observed_arrival_candidate']['rmse']:.3f} |
| Pitcher 2023 | {pitcher_2023['end_to_end_baseline']['rmse']:.3f} | {pitcher_2023['end_to_end_candidate']['rmse']:.3f} | {pitcher_2023['end_to_end_baseline']['mae']:.3f} | {pitcher_2023['end_to_end_candidate']['mae']:.3f} | {pitcher_2023['conditional_on_observed_arrival_baseline']['rmse']:.3f} to {pitcher_2023['conditional_on_observed_arrival_candidate']['rmse']:.3f} |

Stability gate: **{stability_passed}**. Hitter arrived-player RMSE worsens in both
later cohorts. Pitcher absolute bias worsens in both, and later paired MSE intervals
cross zero. The unchanged bridge is rejected as a stable replacement; its typical-row
MAE signal remains useful evidence for a later positive-tail model.
"""
    args.output_md.write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
