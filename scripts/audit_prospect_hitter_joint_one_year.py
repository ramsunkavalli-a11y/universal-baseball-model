#!/usr/bin/env python3
"""Audit joint next-season prospect hitter WAR with non-arrivals retained."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_linked_hitter_path_replay import COMPONENTS, _components, _history_stats
from universal_baseball.conditional_war_rates import build_hitter_conditional_war_rates
from universal_baseball.historical_hitter_performance import (
    build_historical_hitter_performance_paths,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
)
from universal_baseball.prospect_arrival import (
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)


TRAINING_YEARS = (2018, 2021, 2022, 2023)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--history-root",
        type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--membership",
        type=Path,
        default=Path(
            "reports/generated/opportunity-40man-history/tables/"
            "historical_40man_membership.parquet"
        ),
    )
    parser.add_argument(
        "--skill",
        type=Path,
        default=Path(
            "reports/generated/phase2-arrival-skill-source/tables/"
            "affiliated_hitting_components.parquet"
        ),
    )
    parser.add_argument(
        "--demographics",
        type=Path,
        default=Path("reports/generated/player-demographics/tables/player-demographics.parquet"),
    )
    parser.add_argument(
        "--hitting",
        type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/"
            "mlb_hitting_components_2009_2025.parquet"
        ),
    )
    parser.add_argument(
        "--debut-dates",
        type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/"
            "people-debut-dates.parquet"
        ),
    )
    parser.add_argument(
        "--performance-paths",
        type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/"
            "post-debut-hitter-performance-paths.parquet"
        ),
    )
    parser.add_argument(
        "--environment-report",
        type=Path,
        default=Path("docs/prospect-component-uncertainty-result.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-hitter-joint-one-year-audit-result.json"),
    )
    return parser.parse_args()


def _first_year(two_year: pl.Expr) -> pl.Expr:
    return 1.0 - (1.0 - two_year).sqrt()


def _metrics(frame: pl.DataFrame) -> dict[str, float | int]:
    error = frame["prediction"] - frame["observed"]
    return {
        "players": frame.height,
        "predicted_mean": float(frame["prediction"].mean()),
        "observed_mean": float(frame["observed"].mean()),
        "bias": float(error.mean()),
        "mae": float(error.abs().mean()),
        "rmse": float(error.pow(2).mean() ** 0.5),
    }


def _bootstrap(frame: pl.DataFrame) -> dict[str, float]:
    error = (frame["prediction"] - frame["observed"]).to_numpy()
    rng = np.random.default_rng(20260910)
    indices = rng.integers(0, len(error), size=(2_000, len(error)))
    bias = error[indices].mean(axis=1)
    return {
        "bias_ci_low": float(np.quantile(bias, 0.025)),
        "bias_ci_high": float(np.quantile(bias, 0.975)),
        "probability_overprediction": float(np.mean(bias > 0)),
    }


def _probability_metrics(
    frame: pl.DataFrame, *, probability: str, observed: str
) -> dict[str, float | int]:
    y = frame.get_column(observed).cast(pl.Float64).to_numpy()
    p = np.clip(frame.get_column(probability).to_numpy(), 1e-9, 1 - 1e-9)
    return {
        "players": len(y),
        "predicted_rate": float(p.mean()),
        "observed_rate": float(y.mean()),
        "brier": float(np.square(p - y).mean()),
        "log_loss": float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()),
    }


def main() -> int:
    args = _args()
    snapshots = pl.read_parquet(args.history_root / "hitter_snapshots.parquet")
    stats, _ = _history_stats(args.history_root)
    membership = pl.read_parquet(args.membership)
    skill = pl.read_parquet(args.skill)
    demographics = pl.read_parquet(args.demographics)
    debut_dates = pl.read_parquet(args.debut_dates)
    training = pl.concat(
        [
            build_arrival_cohort(
                snapshots,
                stats,
                membership,
                skill,
                debut_dates,
                snapshot_year=year,
                horizon=2,
                player_type="hitter",
                demographics=demographics,
            )
            for year in TRAINING_YEARS
        ]
    )
    scored = build_arrival_cohort(
        snapshots,
        stats,
        membership,
        skill,
        debut_dates,
        snapshot_year=2024,
        horizon=1,
        player_type="hitter",
        demographics=demographics,
    )
    specifications = (
        ("arrived_within_horizon", "arrival", "level_exposure", 1.0, 0.0, None),
        (
            "meaningful_role_within_horizon",
            "meaningful_given_arrival",
            "core",
            1.0,
            0.0,
            "arrived_within_horizon",
        ),
        (
            "established_role_within_horizon",
            "established_given_meaningful",
            "core",
            0.1,
            50.0,
            "meaningful_role_within_horizon",
        ),
        ("meaningful_role_within_horizon", "meaningful_role", "level_exposure", 1.0, 0.0, None),
        ("established_role_within_horizon", "established_role", "core", 1.0, 0.0, None),
    )
    for target, outcome, features, regularization, regression, condition in specifications:
        fit_data = training if condition is None else training.filter(pl.col(condition) == 1)
        scored = predict_arrival(
            fit_arrival_model(
                fit_data,
                player_type="hitter",
                target_column=target,
                outcome_name=outcome,
                feature_set=features,
                regularization_c=regularization,
                production_regression=regression,
            ),
            scored,
        )
    scored = scored.with_columns(
        _first_year(pl.col("predicted_two_year_arrival_probability")).alias("p_arrival"),
        _first_year(
            pl.col("predicted_two_year_meaningful_given_arrival_probability")
        ).alias("p_meaningful_given_arrival"),
        _first_year(
            pl.col("predicted_two_year_established_given_meaningful_probability")
        ).alias("p_established_given_meaningful"),
        _first_year(pl.col("predicted_two_year_meaningful_role_probability")).alias(
            "p_direct_meaningful"
        ),
        _first_year(pl.col("predicted_two_year_established_role_probability")).alias(
            "p_direct_established"
        ),
    ).with_columns(
        pl.min_horizontal(
            pl.col("p_arrival") * pl.col("p_meaningful_given_arrival"),
            pl.col("p_direct_meaningful"),
        ).alias("p_meaningful")
    ).with_columns(
        pl.min_horizontal(
            pl.col("p_meaningful") * pl.col("p_established_given_meaningful"),
            pl.col("p_direct_established"),
            pl.col("p_meaningful"),
        ).alias("p_established")
    )

    component_skill = _components(skill)
    offsets = fit_same_season_component_translation(
        component_skill,
        exposure_column="plate_appearances",
        component_columns=COMPONENTS,
        completed_seasons=(2018, 2019, 2021, 2022, 2023, 2024),
        minimum_level_exposure=30,
    ).offsets
    profiles = build_translated_affiliated_profiles(
        scored.select("player_id"),
        component_skill,
        offsets,
        exposure_column="plate_appearances",
        component_columns=COMPONENTS,
        current_season=2024,
        reference_season=2024,
        regression_exposure=1_200.0,
    )
    hitting = pl.read_parquet(args.hitting)
    runs_per_win = float(
        json.loads(args.environment_report.read_text(encoding="utf-8"))["runs_per_win"]
    )
    rates = build_hitter_conditional_war_rates(
        scored.select("player_id", "age_years").with_columns(
            pl.lit("").alias("position_code")
        ),
        hitting,
        current_season=2024,
        forecast_seasons=(2025,),
        reference_plate_appearances=int(
            hitting.filter(pl.col("season") == 2024)["batting_plate_appearances"].sum()
        ),
        runs_per_win=runs_per_win,
        evidence_anchor_season=2024,
        reference_season=2024,
        affiliated_profiles=profiles,
    ).select(
        "player_id",
        "conditional_war_per_600_pa",
        "batting_runs_per_600",
    )
    workload = (
        pl.read_parquet(args.performance_paths)
        .filter((pl.col("window_end_year") <= 2024) & (pl.col("path_year") == 1))
        .group_by("outcome_tier_v2")
        .agg(pl.col("adjusted_workload").mean().alias("mean_first_year_pa"))
    )
    workload_lookup = {
        str(row["outcome_tier_v2"]): float(row["mean_first_year_pa"])
        for row in workload.iter_rows(named=True)
    }
    scored = scored.join(rates, on="player_id", how="left", validate="1:1").with_columns(
        (pl.col("p_arrival") - pl.col("p_meaningful")).clip(0.0, 1.0).alias("p_fringe"),
        (pl.col("p_meaningful") - pl.col("p_established")).clip(0.0, 1.0).alias(
            "p_meaningful_only"
        ),
    ).with_columns(
        (
            (
                pl.col("p_fringe") * workload_lookup["fringe"]
                + pl.col("p_meaningful_only") * workload_lookup["meaningful_only"]
                + pl.col("p_established") * workload_lookup["established"]
            )
            * pl.col("conditional_war_per_600_pa")
            / 600.0
        ).alias("prediction")
    )

    observed_years = (
        scored.select(pl.col("player_id").alias("path_player_id"))
        .with_columns(
            pl.lit("hitter").alias("player_type"),
            pl.lit("unknown").alias("outcome_tier_v2"),
            pl.lit("hitter").alias("career_role"),
            pl.lit(1).alias("path_year"),
            pl.lit(2025).alias("source_season"),
        )
        .join(
            hitting.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("batting_plate_appearances").cast(pl.Float64).alias("observed_pa"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("observed_pa").fill_null(0.0).alias("adjusted_workload"),
            pl.when(pl.col("observed_pa").fill_null(0.0) > 0)
            .then(pl.lit("hitter"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("observed_pa")
    )
    observed = build_historical_hitter_performance_paths(
        observed_years, hitting, runs_per_win=runs_per_win
    ).select(
        pl.col("path_player_id").alias("player_id"),
        pl.col("observed_component_war").alias("observed"),
        pl.col("adjusted_workload").alias("observed_pa"),
    )
    evaluated = scored.join(observed, on="player_id", how="left", validate="1:1").with_columns(
        pl.col("observed").fill_null(0.0),
        pl.col("observed_pa").fill_null(0.0),
    )
    subgroup = evaluated.filter(
        (pl.col("predicted_two_year_arrival_probability") >= 0.80)
        & (pl.col("batting_runs_per_600") < 0.0)
    )
    arrivals = evaluated.filter(pl.col("observed_pa") > 0)
    probability_columns = {
        "arrival": ("p_arrival", "arrived_within_horizon"),
        "meaningful": ("p_meaningful", "meaningful_role_within_horizon"),
        "established": ("p_established", "established_role_within_horizon"),
    }
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "prospect_hitter_joint_one_year_diagnostic_complete",
        "contract": "docs/prospect-hitter-joint-one-year-audit-plan.md",
        "training_origins": list(TRAINING_YEARS),
        "evaluation_origin": 2024,
        "evaluation_outcome": 2025,
        "all_players": _metrics(evaluated),
        "high_arrival_below_average_batting": _metrics(subgroup),
        "observed_arrivals": _metrics(arrivals),
        "one_year_probability_calibration": {
            name: _probability_metrics(
                evaluated, probability=probability, observed=observed_column
            )
            for name, (probability, observed_column) in probability_columns.items()
        },
        "subgroup_probability_calibration": {
            name: _probability_metrics(
                subgroup, probability=probability, observed=observed_column
            )
            for name, (probability, observed_column) in probability_columns.items()
        },
        "bootstrap": {
            "all_players": _bootstrap(evaluated),
            "high_arrival_below_average_batting": _bootstrap(subgroup),
            "observed_arrivals": _bootstrap(arrivals),
        },
        "workload_means": workload_lookup,
        "decision": "diagnostic_only_no_candidate_or_current_value_change",
        "boundaries": {
            "non_arrivals_retained": True,
            "outside_fv_or_rank_used": False,
            "current_2026_outcomes_used": False,
            "position_defense_and_baserunning_excluded": True,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
