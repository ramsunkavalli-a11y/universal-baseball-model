#!/usr/bin/env python3
"""Rolling audit of the complete activity/workload/performance WAR mixture."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.player_value_uncertainty import zero_truncated_nb2_variance
from universal_baseball.war_hurdle_uncertainty import (
    build_component_simulated_war_uncertainty,
)
from universal_baseball.war_uncertainty_paths import build_component_war_uncertainty
from universal_baseball.war_uncertainty_validation import summarize_interval_coverage


OPPORTUNITY = Path("reports/generated/rolling-opportunity-calibration/tables")
PERFORMANCE = Path("reports/generated/rolling-conditional-war-uncertainty/tables")
OUTPUT = Path("reports/generated/rolling-combined-war-uncertainty")
TARGETS = (2022, 2023, 2024, 2025)
RUNS_PER_WIN = 10.0


def _performance_scale(frame: pl.DataFrame, target: int) -> float:
    if target == TARGETS[0]:
        return 1.0
    prior = frame.filter(
        (pl.col("target_season") < target) & (pl.col("observed_workload") > 0)
    ).with_columns(
        (
            (pl.col("observed_neutral_war") - pl.col("projected_war_mean"))
            / pl.col("annual_war_variance").sqrt()
        ).alias("standardized_error")
    )
    return float(prior.select((pl.col("standardized_error") ** 2).mean().sqrt()).item())


def _paths(
    opportunity: pl.DataFrame,
    performance: pl.DataFrame,
    *,
    target: int,
    component: str,
    rate_column: str,
    conditional_workload_column: str,
    conditional_variance_column: str,
    observed_workload_column: str,
    workload_unit: float,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    forecast = opportunity.filter(pl.col("target_season") == target).select(
        "player_id", "raw_probability", "conditional_mean", "nb_alpha"
    )
    outcomes = performance.filter(pl.col("target_season") == target).select(
        "player_id",
        rate_column,
        "event_run_variance",
        "posterior_run_rate_variance",
        pl.col(observed_workload_column).alias("observed_workload"),
        "observed_neutral_war",
    )
    joined = forecast.join(outcomes, on="player_id", how="inner", validate="1:1")
    if joined.height != forecast.height:
        raise ValueError(f"{component} rolling mixture lost forecast rows")
    variances = [
        zero_truncated_nb2_variance(float(mean), alpha=float(alpha))
        for mean, alpha in joined.select("conditional_mean", "nb_alpha").iter_rows()
    ]
    paths = joined.with_columns(
        pl.Series(conditional_variance_column, variances),
        pl.lit(date(target - 1, 12, 31)).alias("as_of_date"),
        pl.lit(target).alias("season"),
        pl.lit(1).alias("horizon"),
        pl.col("raw_probability").alias("mlb_active_probability"),
        pl.col("conditional_mean").alias(conditional_workload_column),
        (
            pl.col("raw_probability")
            * pl.col("conditional_mean")
            * pl.col(rate_column)
            / workload_unit
        ).alias("expected_war"),
    )
    return paths, joined.select("player_id", "observed_workload", "observed_neutral_war")


def _component(component: str) -> dict[str, object]:
    opportunity = pl.read_parquet(
        OPPORTUNITY / f"{component}-rolling-participation.parquet"
    )
    performance = pl.read_parquet(
        PERFORMANCE / f"{component}-rolling-conditional-war.parquet"
    ).rename(
        {
            (
                "batting_plate_appearances"
                if component == "hitter"
                else "pitching_batters_faced"
            ): "observed_workload"
        }
    )
    if component == "hitter":
        rate_column = "conditional_war_per_600_pa"
        conditional_workload_column = "conditional_mlb_pa"
        conditional_variance_column = "conditional_mlb_pa_variance"
        workload_unit = 600.0
    else:
        rate_column = "conditional_war_per_800_bf"
        conditional_workload_column = "conditional_mlb_bf"
        conditional_variance_column = "conditional_mlb_bf_variance"
        workload_unit = 800.0

    exact_frames = []
    normal_frames = []
    annual = []
    for target in TARGETS:
        paths, outcomes = _paths(
            opportunity,
            performance,
            target=target,
            component=component,
            rate_column=rate_column,
            conditional_workload_column=conditional_workload_column,
            conditional_variance_column=conditional_variance_column,
            observed_workload_column="observed_workload",
            workload_unit=workload_unit,
        )
        multiplier = _performance_scale(performance, target)
        alpha = float(paths.get_column("nb_alpha").first())
        normal = build_component_war_uncertainty(
            paths,
            component=component,
            conditional_workload_column=conditional_workload_column,
            conditional_workload_variance_column=conditional_variance_column,
            conditional_war_rate_column=rate_column,
            workload_unit=workload_unit,
            runs_per_win=RUNS_PER_WIN,
        ).join(outcomes, on="player_id", how="inner", validate="1:1")
        exact = build_component_simulated_war_uncertainty(
            paths,
            component=component,
            conditional_workload_column=conditional_workload_column,
            conditional_workload_variance_column=conditional_variance_column,
            conditional_war_rate_column=rate_column,
            workload_unit=workload_unit,
            runs_per_win=RUNS_PER_WIN,
            nb_alpha=alpha,
            performance_standard_deviation_multiplier=multiplier,
        ).join(outcomes, on="player_id", how="inner", validate="1:1")
        normal = normal.with_columns(pl.lit(target).alias("target_season"))
        exact = exact.with_columns(pl.lit(target).alias("target_season"))
        normal_frames.append(normal)
        exact_frames.append(exact)
        normal_score = summarize_interval_coverage(normal)
        exact_score = summarize_interval_coverage(exact)
        annual.append(
            {
                "target_season": target,
                "performance_standard_deviation_multiplier": multiplier,
                "moment_normal": normal_score,
                "rolling_scaled_exact_mixture": exact_score,
                "exact_minus_normal_interval_score": float(
                    exact_score["mean_interval_score"]
                )
                - float(normal_score["mean_interval_score"]),
            }
        )
    normal_all = pl.concat(normal_frames).filter(pl.col("target_season") > TARGETS[0])
    exact_all = pl.concat(exact_frames).filter(pl.col("target_season") > TARGETS[0])
    normal_score = summarize_interval_coverage(normal_all)
    exact_score = summarize_interval_coverage(exact_all)
    return {
        "annual": annual,
        "pooled_2023_2025": {
            "moment_normal": normal_score,
            "rolling_scaled_exact_mixture": exact_score,
            "exact_minus_normal_interval_score": float(
                exact_score["mean_interval_score"]
            )
            - float(normal_score["mean_interval_score"]),
            "exact_minus_normal_absolute_coverage_error": abs(
                float(exact_score["coverage"]) - 0.80
            )
            - abs(float(normal_score["coverage"]) - 0.80),
        },
    }


def main() -> int:
    report = {
        "report_schema_version": "0.1",
        "gate": "rolling_combined_war_uncertainty",
        "targets": list(TARGETS),
        "hitter": _component("hitter"),
        "pitcher": _component("pitcher"),
        "production_changed": False,
        "boundaries": {
            "raw_participation_probability_retained": True,
            "conditional_workload_distribution_unchanged": True,
            "performance_scale_uses_prior_origins_only": True,
            "point_estimates_changed": False,
            "fanGraphs_used": False,
        },
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                component: report[component]["pooled_2023_2025"]
                for component in ("hitter", "pitcher")
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
