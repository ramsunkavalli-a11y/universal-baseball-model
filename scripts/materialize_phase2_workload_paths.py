#!/usr/bin/env python3
"""Apply the Phase 2 established-player workload correction."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.phase2_workload import WORKLOAD_MODEL_ID, anchor_workload_paths
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--input-root", type=Path,
        default=Path("reports/generated/current-opportunity-paths-v2"),
    )
    parser.add_argument(
        "--current-source-root", type=Path,
        default=Path("reports/generated/opportunity-current-source-2026-09-08/tables/2026"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/phase2-workload-paths"),
    )
    return parser.parse_args()


def _current(stats: pl.DataFrame, group: str, column: str, output: str) -> pl.DataFrame:
    return (
        stats.filter((pl.col("stat_group") == group) & (pl.col("sport_id") == 1))
        .group_by("player_id")
        .agg(pl.col(column).sum().cast(pl.Float64).alias(output))
    )


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    tables = args.input_root / dated / "tables"
    stats = pl.read_parquet(args.current_source_root / "affiliated_season_stats.parquet")
    hitters = anchor_workload_paths(
        pl.read_parquet(tables / "hitter_opportunity_paths.parquet"),
        _current(stats, "hitting", "plate_appearances", "current_season_mlb_pa"),
        conditional_column="conditional_mlb_pa",
        expected_column="expected_mlb_pa",
        current_column="current_season_mlb_pa",
        variance_column="conditional_mlb_pa_variance",
        workload_cap=700.0,
        reliability_exposure=300.0,
    )
    pitchers = anchor_workload_paths(
        pl.read_parquet(tables / "pitcher_opportunity_paths.parquet"),
        _current(stats, "pitching", "batters_faced", "current_season_mlb_bf"),
        conditional_column="conditional_mlb_bf",
        expected_column="expected_mlb_bf",
        current_column="current_season_mlb_bf",
        variance_column="conditional_mlb_bf_variance",
        workload_cap=900.0,
        reliability_exposure=250.0,
        anchor_strength=0.25,
    )
    output = args.output_root / dated
    output_tables = output / "tables"
    output_tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitters": write_canonical_parquet(
            hitters, output_tables / "hitter_opportunity_paths.parquet",
            table_name="phase2_hitter_opportunity_paths",
        ).as_record(),
        "pitchers": write_canonical_parquet(
            pitchers, output_tables / "pitcher_opportunity_paths.parquet",
            table_name="phase2_pitcher_opportunity_paths",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "phase2_established_player_workload_anchor",
        "as_of_date": dated,
        "model_id": WORKLOAD_MODEL_ID,
        "parameters": {
            "hitter_anchor_strength": 0.75,
            "pitcher_anchor_strength": 0.25,
            "annual_decay": 0.75,
            "hitter_reliability_pa": 300.0, "pitcher_reliability_bf": 250.0,
            "hitter_cap_pa": 700.0, "pitcher_cap_bf": 900.0,
        },
        "boundaries": {
            "active_probability_changed": False,
            "non_mlb_players_receive_anchor": False,
            "parameters_production_confirmed": False,
            "phase1_high_workload_bias_addressed": True,
            "2025_historical_check": (
                "overall MAE improved for both groups; hitter established bias "
                "-70 to -12 PA; pitcher established bias -33 to -2 BF"
            ),
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
