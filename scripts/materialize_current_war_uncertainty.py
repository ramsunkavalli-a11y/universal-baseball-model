#!/usr/bin/env python3
"""Materialize Phase 1 annual WAR reference ranges for universal paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import write_canonical_parquet
from universal_baseball.war_hurdle_uncertainty import (
    CENTRAL_COVERAGE,
    SIMULATED_UNCERTAINTY_MODEL_ID,
    build_component_simulated_war_uncertainty,
    build_whole_player_from_component_intervals,
)


PERFORMANCE_STANDARD_DEVIATION_MULTIPLIER = {
    "hitter": 1.2073796145508366,
    "pitcher": 1.2453154808489515,
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--war-root", type=Path,
        default=Path("reports/generated/current-conditional-war-paths"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/current-war-uncertainty"),
    )
    return parser.parse_args()


def _summary(frame: pl.DataFrame) -> dict[str, float]:
    width = frame.get_column("projected_war_upper") - frame.get_column(
        "projected_war_lower"
    )
    return {
        "projected_war_mean_sum": float(
            frame.get_column("projected_war_mean").sum()
        ),
        "median_reference_width": float(width.median()),
        "p90_reference_width": float(width.quantile(0.90, interpolation="linear")),
        "maximum_reference_width": float(width.max()),
        "opportunity_variance_share": float(
            frame.get_column("opportunity_war_variance").sum()
            / frame.get_column("annual_war_variance").sum()
        ),
    }


def main() -> int:
    args = _args()
    source_root = args.war_root / args.as_of_date.isoformat()
    tables = source_root / "tables"
    source_report = json.loads(
        (source_root / "report.json").read_text(encoding="utf-8")
    )
    runs_per_win = float(source_report["reference_environment"]["runs_per_win"])
    hitters = build_component_simulated_war_uncertainty(
        pl.read_parquet(tables / "hitter_expected_war_paths.parquet"),
        component="hitter",
        conditional_workload_column="conditional_mlb_pa",
        conditional_workload_variance_column="conditional_mlb_pa_variance",
        conditional_war_rate_column="conditional_war_per_600_pa",
        workload_unit=600.0,
        runs_per_win=runs_per_win,
        performance_standard_deviation_multiplier=(
            PERFORMANCE_STANDARD_DEVIATION_MULTIPLIER["hitter"]
        ),
    )
    pitchers = build_component_simulated_war_uncertainty(
        pl.read_parquet(tables / "pitcher_expected_war_paths.parquet"),
        component="pitcher",
        conditional_workload_column="conditional_mlb_bf",
        conditional_workload_variance_column="conditional_mlb_bf_variance",
        conditional_war_rate_column="conditional_war_per_800_bf",
        workload_unit=800.0,
        runs_per_win=runs_per_win,
        performance_standard_deviation_multiplier=(
            PERFORMANCE_STANDARD_DEVIATION_MULTIPLIER["pitcher"]
        ),
    )
    components = pl.concat([hitters, pitchers]).sort(
        ["player_id", "season", "projection_component"]
    )
    whole = build_whole_player_from_component_intervals(components)
    output_root = args.output_root / args.as_of_date.isoformat()
    output_tables = output_root / "tables"
    output_tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "components": write_canonical_parquet(
            components,
            output_tables / "component-war-uncertainty.parquet",
            table_name="current_component_war_uncertainty",
        ).as_record(),
        "whole_player": write_canonical_parquet(
            whole,
            output_tables / "whole-player-war-uncertainty.parquet",
            table_name="current_whole_player_war_uncertainty",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_multiyear_exact_mixture_war_uncertainty",
        "as_of_date": args.as_of_date.isoformat(),
        "uncertainty_model_id": SIMULATED_UNCERTAINTY_MODEL_ID,
        "central_reference_coverage": CENTRAL_COVERAGE,
        "hitter": _summary(hitters),
        "pitcher": _summary(pitchers),
        "whole_player": _summary(whole),
        "method": {
            "opportunity": (
                "zero-inclusive active probability plus positive workload variance "
                "estimated from pre-cutoff historical cohorts"
            ),
            "performance": (
                "multinomial event variance plus Dirichlet-equivalent posterior "
                "rate variance from declared regression strength; standard-deviation "
                "scale learned from prior rolling origins"
            ),
            "combination": (
                "Bernoulli zero mass plus moment-matched positive-workload gamma and "
                "conditional performance simulation; the small two-way subset uses "
                "independent component moments"
            ),
        },
        "not_modeled": [
            "cross-season covariance",
            "hitter-pitcher covariance for two-way players",
            "independent baserunning and future-position error",
            "pitcher contact-outcome detail inside the other-BF bucket",
            "future injury timing beyond observed opportunity attrition",
            "parameter and source-revision error",
        ],
        "interpretation": (
            "rolling-supported annual simulation range, not a guarantee or a "
            "cross-season stochastic career path"
        ),
        "current_team_depth_used": False,
        "workload_cap_used": False,
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "gate": report["gate"],
                "hitter": report["hitter"],
                "pitcher": report["pitcher"],
                "whole_player": report["whole_player"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
