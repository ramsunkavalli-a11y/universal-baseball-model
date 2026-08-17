#!/usr/bin/env python3
"""Combine reconciled MLB and tracked-MiLB BBE into one season input.

This command performs no source requests and no talent modeling. It validates that
source-family materializations do not overlap at the canonical pitch-grain BBE key
and emits the exact per-season parquet consumed by richer Current Talent fitting.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_batted_ball_materialization import (
    combine_reconciled_tracked_bbe,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--mlb-parquet", type=Path, required=True)
    parser.add_argument("--milb-parquet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    mlb = pl.read_parquet(args.mlb_parquet)
    milb = pl.read_parquet(args.milb_parquet)
    combined = combine_reconciled_tracked_bbe(
        [mlb, milb],
        expected_season=args.season,
    )
    if combined.is_empty():
        raise ValueError("combined tracked BBE is empty")

    parquet_path = args.output_dir / f"reconciled_tracked_bbe_{args.season}.parquet"
    csv_path = args.output_dir / f"reconciled_tracked_bbe_{args.season}.csv"
    combined.write_parquet(parquet_path, compression="zstd")
    combined.write_csv(csv_path)

    by_source = (
        combined.group_by(["source_family", "level_group"])
        .agg(
            pl.len().cast(pl.Int64).alias("model_bbe"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("game_count"),
            pl.col("player_id").n_unique().cast(pl.Int64).alias("player_count"),
        )
        .sort(["source_family", "level_group"])
    )
    by_source_path = args.output_dir / f"reconciled_tracked_bbe_{args.season}_by_source.csv"
    by_source.write_csv(by_source_path)

    report = {
        "report_schema_version": "0.1",
        "scope": "combined_reconciled_tracked_bbe",
        "network_requests_performed": False,
        "season": args.season,
        "canonical_model_bbe_contract": "result_producing_non_bunt_pitch_grain_v1",
        "canonical_model_bbe_count": int(combined.height),
        "game_count": int(combined.get_column("game_pk").n_unique()),
        "player_count": int(combined.get_column("player_id").n_unique()),
        "source_summary": by_source.to_dicts(),
        "inputs": {
            "mlb_parquet": str(args.mlb_parquet),
            "milb_parquet": str(args.milb_parquet),
        },
        "outputs": {
            "parquet": str(parquet_path),
            "csv": str(csv_path),
            "by_source_csv": str(by_source_path),
        },
    }
    report_path = args.output_dir / f"reconciled_tracked_bbe_{args.season}_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
