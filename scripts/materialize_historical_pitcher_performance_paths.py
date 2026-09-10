#!/usr/bin/env python3
"""Build linked historical pitcher workload and component-performance paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.historical_pitcher_performance import (
    build_historical_pitcher_performance_paths,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--annual-paths",
        type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/"
            "post-debut-annual-workload-paths.parquet"
        ),
    )
    parser.add_argument(
        "--pitching",
        type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/"
            "mlb_pitching_2009_2025.parquet"
        ),
    )
    parser.add_argument(
        "--conditional-report",
        type=Path,
        default=Path(
            "reports/generated/phase2-conditional-war-paths/2026-09-08/report.json"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/"
            "post-debut-pitcher-performance-paths.parquet"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/historical-pitcher-performance-paths-result.json"),
    )
    args = parser.parse_args()
    reference = json.loads(args.conditional_report.read_text(encoding="utf-8"))[
        "reference_environment"
    ]
    paths = build_historical_pitcher_performance_paths(
        pl.read_parquet(args.annual_paths),
        pl.read_parquet(args.pitching),
        runs_per_win=float(reference["runs_per_win"]),
    )
    storage = write_canonical_parquet(
        paths,
        args.output,
        table_name="historical_pitcher_component_performance_paths",
    ).as_record()
    careers = paths.group_by(["path_player_id", "outcome_tier_v2", "career_role"]).agg(
        pl.col("observed_component_war").sum().alias("six_year_component_war"),
        pl.col("adjusted_workload").sum().alias("six_year_bf"),
    )
    report = {
        "report_schema_version": 1,
        "status": "linked_pitcher_performance_path_source_ready_not_model_promoted",
        "players": careers.height,
        "annual_rows": paths.height,
        "active_rows": paths.filter(pl.col("adjusted_workload") > 0).height,
        "source_seasons": [
            int(paths["source_season"].min()),
            int(paths["source_season"].max()),
        ],
        "by_tier": careers.group_by("outcome_tier_v2")
        .agg(
            pl.len().alias("players"),
            pl.col("six_year_bf").mean().alias("mean_six_year_bf"),
            pl.col("six_year_component_war")
            .mean()
            .alias("mean_six_year_component_war"),
            pl.col("six_year_component_war")
            .median()
            .alias("median_six_year_component_war"),
        )
        .sort("outcome_tier_v2")
        .to_dicts(),
        "method": (
            "same five-part neutral-wOBA pitcher run conversion as the current "
            "conditional WAR model; annual league environment and 2020 workload adjusted"
        ),
        "purpose": (
            "future challenger must resample performance, workload and role from "
            "the same historical player path"
        ),
        "model_effect": "none",
        "sources": {
            args.annual_paths.as_posix(): sha256_file(args.annual_paths),
            args.pitching.as_posix(): sha256_file(args.pitching),
            args.conditional_report.as_posix(): sha256_file(args.conditional_report),
        },
        "storage": storage,
    }
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "sources"}, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
