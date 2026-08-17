#!/usr/bin/env python3
"""Materialize reconciled tracked BBE from retained Savant CSV bytes only.

No network I/O occurs here. The command is source-family agnostic:

- point MLB_SAVANT at the certified historical MLB raw Savant cache; or
- point MILB_SAVANT_TRACKED at tracked-only Minor Savant raw chunks captured by a
  separate manual source workflow.

Both paths use the same corrected canonical BBE projection, certified player-game
reconciliation, and broad source-completeness audit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_batted_ball_materialization import (
    build_tracking_environment_completeness,
    load_certified_player_game_environments,
    materialize_reconciled_tracked_bbe,
    read_retained_savant_csv_tree,
)
from universal_baseball.current_talent_batted_ball_reconciliation import (
    TRACKED_SOURCE_FAMILIES,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--certified-evidence-root", type=Path, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument(
        "--source-family",
        choices=sorted(TRACKED_SOURCE_FAMILIES),
        required=True,
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    raw, manifest = read_retained_savant_csv_tree(args.raw_root)
    certified = load_certified_player_game_environments(
        args.certified_evidence_root,
        season=args.season,
        source_family=args.source_family,
    )
    completeness, completeness_metrics = build_tracking_environment_completeness(
        raw,
        certified,
        source_family=args.source_family,
    )
    reconciled = materialize_reconciled_tracked_bbe(
        raw,
        certified,
        source_family=args.source_family,
    )
    if reconciled.is_empty():
        raise ValueError(
            f"{args.source_family} retained source produced zero canonical model BBE for {args.season}"
        )

    stem = f"{args.season}_{args.source_family.lower()}"
    parquet_path = args.output_dir / f"reconciled_tracked_bbe_{stem}.parquet"
    csv_path = args.output_dir / f"reconciled_tracked_bbe_{stem}.csv"
    manifest_path = args.output_dir / f"raw_savant_manifest_{stem}.csv"
    completeness_path = args.output_dir / f"tracking_completeness_{stem}.csv"
    reconciled.write_parquet(parquet_path, compression="zstd")
    reconciled.write_csv(csv_path)
    manifest.write_csv(manifest_path)
    completeness.write_csv(completeness_path)

    by_tier = (
        reconciled.group_by(
            ["source_family", "source_capability_tier", "level_group", "league_id"]
        )
        .agg(
            pl.len().cast(pl.Int64).alias("model_bbe"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("game_count"),
            pl.col("player_id").n_unique().cast(pl.Int64).alias("player_count"),
            pl.col("game_date").min().alias("first_game_date"),
            pl.col("game_date").max().alias("last_game_date"),
            pl.col("launch_speed").mean().alias("mean_exit_velocity"),
            pl.col("sweet_spot").mean().alias("sweet_spot_share"),
        )
        .sort(["level_group", "league_id", "source_capability_tier"])
    )
    by_tier_path = args.output_dir / f"tracked_bbe_capability_{stem}.csv"
    by_tier.write_csv(by_tier_path)

    report = {
        "report_schema_version": "0.2",
        "scope": "offline_reconciled_tracked_bbe_materialization",
        "network_requests_performed": False,
        "season": args.season,
        "source_family": args.source_family,
        "canonical_model_bbe_contract": "result_producing_non_bunt_pitch_grain_v1",
        "raw_root": str(args.raw_root),
        "certified_evidence_root": str(args.certified_evidence_root),
        "raw_csv_file_count": int(manifest.height),
        "raw_response_bytes": int(manifest.get_column("response_bytes").sum()),
        "raw_row_count": int(manifest.get_column("row_count").sum()),
        "broad_tracking_completeness": completeness_metrics,
        "broad_tracking_completeness_by_environment": completeness.to_dicts(),
        "canonical_model_bbe_count": int(reconciled.height),
        "canonical_game_count": int(reconciled.get_column("game_pk").n_unique()),
        "canonical_player_count": int(reconciled.get_column("player_id").n_unique()),
        "first_game_date": str(reconciled.get_column("game_date").min()),
        "last_game_date": str(reconciled.get_column("game_date").max()),
        "source_capability_tiers": by_tier.to_dicts(),
        "outputs": {
            "reconciled_parquet": str(parquet_path),
            "reconciled_csv": str(csv_path),
            "raw_manifest_csv": str(manifest_path),
            "tracking_completeness_csv": str(completeness_path),
            "capability_csv": str(by_tier_path),
        },
    }
    report_path = args.output_dir / f"report_{stem}.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
