#!/usr/bin/env python3
"""Compare point-preserving hurdle and moment-normal WAR ranges on 2025."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.war_hurdle_uncertainty import (
    build_component_hurdle_war_uncertainty,
    build_component_simulated_war_uncertainty,
)
from universal_baseball.war_uncertainty_validation import summarize_interval_coverage


ROOT = Path("reports/generated")
CHECKPOINT = "2025-03-27"
TARGET = 2025
ROLLING_PERFORMANCE_SCALE = {
    "hitter": 1.2073796145508366,
    "pitcher": 1.2453154808489515,
}


def _score(
    component: str, *, runs_per_win: float, nb_alpha: float
) -> dict[str, object]:
    paths = pl.read_parquet(
        ROOT
        / "historical-projection-paths"
        / CHECKPOINT
        / "tables"
        / f"{component}-expected-war-paths.parquet"
    ).filter(pl.col("season") == TARGET)
    if component == "hitter":
        workload = "pa"
        observed_workload = "batting_plate_appearances"
        workload_unit = 600.0
    else:
        workload = "bf"
        observed_workload = "pitching_batters_faced"
        workload_unit = 800.0
    hurdle = build_component_hurdle_war_uncertainty(
        paths,
        component=component,
        conditional_workload_column=f"conditional_mlb_{workload}",
        conditional_workload_variance_column=f"conditional_mlb_{workload}_variance",
        conditional_war_rate_column=f"conditional_war_per_{int(workload_unit)}_{workload}",
        workload_unit=workload_unit,
        runs_per_win=runs_per_win,
    )
    scaled_hurdle = build_component_hurdle_war_uncertainty(
        paths,
        component=component,
        conditional_workload_column=f"conditional_mlb_{workload}",
        conditional_workload_variance_column=f"conditional_mlb_{workload}_variance",
        conditional_war_rate_column=f"conditional_war_per_{int(workload_unit)}_{workload}",
        workload_unit=workload_unit,
        runs_per_win=runs_per_win,
        performance_standard_deviation_multiplier=ROLLING_PERFORMANCE_SCALE[component],
    )
    simulated = build_component_simulated_war_uncertainty(
        paths,
        component=component,
        conditional_workload_column=f"conditional_mlb_{workload}",
        conditional_workload_variance_column=f"conditional_mlb_{workload}_variance",
        conditional_war_rate_column=f"conditional_war_per_{int(workload_unit)}_{workload}",
        workload_unit=workload_unit,
        runs_per_win=runs_per_win,
        nb_alpha=nb_alpha,
        performance_standard_deviation_multiplier=ROLLING_PERFORMANCE_SCALE[component],
    )
    normal = pl.read_parquet(
        ROOT
        / "historical-war-uncertainty"
        / CHECKPOINT
        / "tables/component-war-uncertainty.parquet"
    ).filter(
        (pl.col("season") == TARGET) & (pl.col("projection_component") == component)
    )
    outcomes = pl.read_parquet(
        ROOT
        / "historical-war-score"
        / CHECKPOINT
        / f"{component}-neutral-war-scores.parquet"
    ).select("player_id", observed_workload, "observed_neutral_war")

    def joined(intervals: pl.DataFrame) -> pl.DataFrame:
        result = intervals.join(outcomes, on="player_id", how="inner", validate="1:1")
        if result.height != intervals.height:
            raise ValueError("hurdle uncertainty audit changed the forecast universe")
        return result.with_columns(
            pl.when(pl.col(observed_workload) > 0)
            .then(pl.lit("observed_active"))
            .otherwise(pl.lit("observed_inactive"))
            .alias("observed_activity")
        )

    hurdle_joined = joined(hurdle)
    normal_joined = joined(normal)
    if hurdle.select("player_id", "projected_war_mean").join(
        normal.select("player_id", "projected_war_mean"),
        on="player_id",
        suffix="_normal",
        validate="1:1",
    ).filter(
        (pl.col("projected_war_mean") - pl.col("projected_war_mean_normal")).abs() > 1e-10
    ).height:
        raise ValueError("hurdle challenger changed point estimates")
    output: dict[str, object] = {}
    scaled_hurdle_joined = joined(scaled_hurdle)
    for label, frame in (
        ("moment_normal", normal_joined),
        ("hurdle", hurdle_joined),
        ("rolling_performance_scaled_hurdle", scaled_hurdle_joined),
        ("rolling_scaled_exact_simulation", joined(simulated)),
    ):
        output[label] = {
            "all": summarize_interval_coverage(frame),
            "observed_active": summarize_interval_coverage(
                frame.filter(pl.col("observed_activity") == "observed_active")
            ),
            "observed_inactive": summarize_interval_coverage(
                frame.filter(pl.col("observed_activity") == "observed_inactive")
            ),
        }
    normal_all = output["moment_normal"]["all"]
    hurdle_all = output["hurdle"]["all"]
    output["hurdle_minus_normal"] = {
        "mean_interval_score": float(hurdle_all["mean_interval_score"])
        - float(normal_all["mean_interval_score"]),
        "median_interval_width": float(hurdle_all["median_interval_width"])
        - float(normal_all["median_interval_width"]),
        "absolute_coverage_error": abs(float(hurdle_all["coverage"]) - 0.80)
        - abs(float(normal_all["coverage"]) - 0.80),
    }
    scaled_all = output["rolling_performance_scaled_hurdle"]["all"]
    output["scaled_hurdle_minus_normal"] = {
        "performance_standard_deviation_multiplier": ROLLING_PERFORMANCE_SCALE[
            component
        ],
        "mean_interval_score": float(scaled_all["mean_interval_score"])
        - float(normal_all["mean_interval_score"]),
        "median_interval_width": float(scaled_all["median_interval_width"])
        - float(normal_all["median_interval_width"]),
        "absolute_coverage_error": abs(float(scaled_all["coverage"]) - 0.80)
        - abs(float(normal_all["coverage"]) - 0.80),
    }
    return output


def main() -> int:
    reference = json.loads(
        (
            ROOT
            / "free-agent-historical-skill-source/2025-12-31/report.json"
        ).read_text(encoding="utf-8")
    )["reference_environment"]
    path_report = json.loads(
        (ROOT / "historical-projection-paths" / CHECKPOINT / "report.json").read_text(
            encoding="utf-8"
        )
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_2025_hurdle_war_uncertainty_diagnostic",
        "checkpoint_date": CHECKPOINT,
        "target_season": TARGET,
        "hitter": _score(
            "hitter",
            runs_per_win=float(reference["runs_per_win"]),
            nb_alpha=float(path_report["fit"]["hitter_nb_alpha"]),
        ),
        "pitcher": _score(
            "pitcher",
            runs_per_win=float(reference["runs_per_win"]),
            nb_alpha=float(path_report["fit"]["pitcher_nb_alpha"]),
        ),
        "point_estimates_changed": False,
        "production_changed": False,
        "decision": "diagnostic_only_add_rolling_origins_before_promotion",
    }
    output = ROOT / "historical-war-hurdle-uncertainty" / CHECKPOINT
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                component: report[component]["hurdle_minus_normal"]
                | {
                    "scaled": report[component]["scaled_hurdle_minus_normal"],
                    "scaled_active": report[component][
                        "rolling_performance_scaled_hurdle"
                    ]["observed_active"],
                    "exact": report[component]["rolling_scaled_exact_simulation"],
                }
                for component in ("hitter", "pitcher")
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
