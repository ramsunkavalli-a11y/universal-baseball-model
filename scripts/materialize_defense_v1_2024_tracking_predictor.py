#!/usr/bin/env python3
"""Materialize the frozen 2024 MLB tracked-range predictor for Defense v1 confirmation.

Source-only step. No model parameters are loaded, no 2025 target is queried, and
no scoring or fitting is performed.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
from importlib.metadata import version
import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from sportsdataverse.mlb.mlb_fielding_oaa import mlb_fielding_oaa
from sportsdataverse.mlb.mlb_statcast_extra import mlb_statcast_search


PACKAGE_VERSION = "0.0.75"
SEASON = 2024
# Deliberately broad bounded envelope; game_type="R" restricts returned rows
# to the 2024 regular season without depending on hand-entered opening/closing dates.
QUERY_START = "2024-03-01"
QUERY_END = "2024-10-15"
CHUNK_DAYS = 7
POS_ABBR = {3: "1B", 4: "2B", 5: "3B", 6: "SS", 7: "LF", 8: "CF", 9: "RF"}
GENERAL_POSITIONS = set(POS_ABBR.values())


def _file_sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _storage(path: Path, table_name: str, row_count: int) -> dict[str, Any]:
    return {
        "table_name": table_name,
        "path": str(path).replace("\\", "/"),
        "row_count": int(row_count),
        "file_size_bytes": path.stat().st_size,
        "sha256": _file_sha(path),
    }


def _assert_source_shape(pitches: pl.DataFrame) -> None:
    if pitches.is_empty():
        raise RuntimeError("empty 2024 MLB Statcast source")
    required = {"type", "fielder_2", "hc_x", "hc_y", "hit_distance_sc", "launch_angle", "hit_location", "events"}
    missing = sorted(required - set(pitches.columns))
    if missing:
        raise RuntimeError(f"2024 MLB Statcast source missing columns: {missing}")
    if "game_year" in pitches.columns:
        years = {
            int(value)
            for value in pitches.get_column("game_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        }
        if years != {SEASON}:
            raise RuntimeError(f"unexpected game_year values: {sorted(years)}")
    if "game_type" in pitches.columns:
        game_types = {
            str(value)
            for value in pitches.get_column("game_type").cast(pl.Utf8).drop_nulls().unique().to_list()
        }
        if game_types and game_types != {"R"}:
            raise RuntimeError(f"unexpected game_type values: {sorted(game_types)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected sportsdataverse {PACKAGE_VERSION}, observed {installed}")

    output_root = args.output_root
    table_root = output_root / "tables"
    raw_root = output_root / "raw"
    table_root.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)

    print(f"Fetching 2024 MLB regular-season Statcast: {QUERY_START}..{QUERY_END}")
    pitches = mlb_statcast_search(
        QUERY_START,
        QUERY_END,
        season=SEASON,
        game_type="R",
        chunk_days=CHUNK_DAYS,
    )
    _assert_source_shape(pitches)

    bip = pitches.filter(pl.col("type") == "X")
    if bip.is_empty():
        raise RuntimeError("empty 2024 MLB balls-in-play source")

    # The exact raw input used by the pinned OAA implementation is retained.
    raw_bip_path = raw_root / "statcast_bip_2024_mlb.parquet"
    bip.write_parquet(raw_bip_path, compression="zstd")

    oaa = mlb_fielding_oaa(bip)
    required_oaa = {"fielder_id", "position", "opportunities", "oaa"}
    missing_oaa = sorted(required_oaa - set(oaa.columns))
    if missing_oaa:
        raise RuntimeError(f"mlb_fielding_oaa output missing columns: {missing_oaa}")

    proxy = (
        oaa.with_columns(
            pl.col("fielder_id").cast(pl.Int64, strict=False).alias("player_id"),
            pl.col("position").cast(pl.Int64, strict=False).alias("position_code"),
            pl.col("opportunities").cast(pl.Float64, strict=False),
            pl.col("oaa").cast(pl.Float64, strict=False),
        )
        .filter(
            pl.col("player_id").is_not_null()
            & pl.col("position_code").is_in(sorted(POS_ABBR))
            & pl.col("opportunities").is_not_null()
            & pl.col("oaa").is_not_null()
        )
        .with_columns(
            pl.col("position_code").replace_strict(POS_ABBR, return_dtype=pl.Utf8).alias("position_abbreviation"),
            pl.lit(SEASON).alias("season"),
            pl.lit("MLB").alias("level_group"),
            pl.when(pl.col("opportunities") > 0)
            .then(100.0 * pl.col("oaa") / pl.col("opportunities"))
            .otherwise(None)
            .alias("tracked_oaa_per_100"),
        )
        .select(
            "season",
            "level_group",
            "player_id",
            "position_code",
            "position_abbreviation",
            "opportunities",
            "oaa",
            "tracked_oaa_per_100",
        )
        .sort(["player_id", "position_code"])
    )

    key = ["season", "level_group", "player_id", "position_code"]
    duplicate_count = proxy.group_by(key).len().filter(pl.col("len") != 1).height
    if duplicate_count:
        raise RuntimeError(f"2024 tracked proxy violates player-position grain: {duplicate_count} duplicate keys")

    eligible = proxy.filter(
        pl.col("position_abbreviation").is_in(sorted(GENERAL_POSITIONS))
        & (pl.col("opportunities") >= 100)
        & pl.col("tracked_oaa_per_100").is_not_null()
        & pl.col("tracked_oaa_per_100").is_finite()
    )

    moments = (
        eligible.group_by("position_abbreviation")
        .agg(
            pl.col("tracked_oaa_per_100").mean().alias("mean"),
            pl.col("tracked_oaa_per_100").std(ddof=0).alias("sd"),
            pl.len().alias("eligible_player_count"),
        )
        .with_columns(
            (
                (pl.col("eligible_player_count") >= 20)
                & pl.col("sd").is_not_null()
                & pl.col("sd").is_finite()
                & (pl.col("sd") > 1e-12)
            ).alias("tracked_z_available")
        )
        .sort("position_abbreviation")
    )

    scored = (
        eligible.join(moments, on="position_abbreviation", how="left")
        .filter(pl.col("tracked_z_available"))
        .with_columns(
            ((pl.col("tracked_oaa_per_100") - pl.col("mean")) / pl.col("sd")).alias("tracked_range_z")
        )
        .select(
            "season",
            "level_group",
            "player_id",
            "position_code",
            "position_abbreviation",
            "opportunities",
            "oaa",
            "tracked_oaa_per_100",
            "tracked_range_z",
        )
        .sort(["player_id", "position_code"])
    )
    if scored.is_empty():
        raise RuntimeError("no eligible 2024 MLB tracked_range_z rows")
    if scored.filter(~pl.col("tracked_range_z").is_finite()).height:
        raise RuntimeError("nonfinite 2024 tracked_range_z")

    proxy_path = table_root / "tracked_range_proxy_2024_mlb.parquet"
    z_path = table_root / "tracked_range_z_2024_mlb.parquet"
    moments_path = table_root / "tracked_range_moments_2024_mlb.parquet"
    proxy.write_parquet(proxy_path, compression="zstd")
    scored.write_parquet(z_path, compression="zstd")
    moments.write_parquet(moments_path, compression="zstd")

    unavailable_positions = [
        str(row["position_abbreviation"])
        for row in moments.filter(~pl.col("tracked_z_available")).select("position_abbreviation").iter_rows(named=True)
    ]
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_2024_mlb_tracking_confirmation_predictor_source",
        "contract": "docs/defense-v1-2025-confirmation-contract.md",
        "status": "source_materialized",
        "query": {
            "source": "Baseball Savant MLB Statcast CSV via SportsDataverse",
            "season": SEASON,
            "start": QUERY_START,
            "end": QUERY_END,
            "game_type": "R",
            "chunk_days": CHUNK_DAYS,
            "bounded_envelope_note": "dates intentionally bracket the full season; game_type R is the binding regular-season filter",
        },
        "upstream": {
            "package": "sportsdataverse",
            "package_version": installed,
            "search_function": "mlb_statcast_search",
            "range_function": "mlb_fielding_oaa",
        },
        "feature_contract": {
            "formula": "tracked_oaa_per_100 = 100 * oaa / opportunities",
            "positions": ["1B", "2B", "3B", "SS", "LF", "CF", "RF"],
            "minimum_opportunities": 100,
            "standardization": "2024 x MLB x position mean 0 / population SD 1",
            "minimum_eligible_players_per_position": 20,
            "degenerate_or_small_cell_behavior": "feature unavailable; no pooling across position or level",
        },
        "diagnostics": {
            "pitch_row_count": int(pitches.height),
            "column_count": len(pitches.columns),
            "bip_row_count": int(bip.height),
            "proxy_player_position_row_count": int(proxy.height),
            "proxy_total_opportunities": float(proxy.get_column("opportunities").sum() or 0.0),
            "eligible_raw_player_position_count": int(eligible.height),
            "scored_tracked_z_player_position_count": int(scored.height),
            "scored_unique_player_count": int(scored.get_column("player_id").n_unique()),
            "unavailable_positions": unavailable_positions,
            "position_cells": moments.to_dicts(),
        },
        "storage": {
            "raw_bip": _storage(raw_bip_path, "defense_v1_2024_mlb_statcast_bip", bip.height),
            "range_proxy": _storage(proxy_path, "defense_v1_2024_mlb_tracked_range_proxy", proxy.height),
            "tracked_range_z": _storage(z_path, "defense_v1_2024_mlb_tracked_range_z", scored.height),
            "moments": _storage(moments_path, "defense_v1_2024_mlb_tracked_range_moments", moments.height),
        },
        "decision": {
            "2024_mlb_tracking_confirmation_predictor_materialized": True,
            "2025_defensive_target_source_materialized": False,
            "confirmation_scoring_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_source_accessed": False,
            "2025_defensive_targets_accessed": False,
            "model_parameters_loaded": False,
            "model_fit": False,
            "model_scoring_performed": False,
            "source_filters_changed_from_contract": False,
            "tracked_milb_2024_accessed": False,
            "tracked_framing_2024_derived": False,
            "run_value_conversion_performed": False,
        },
    }

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "pitch_rows": report["diagnostics"]["pitch_row_count"],
                "bip_rows": report["diagnostics"]["bip_row_count"],
                "eligible_raw_rows": report["diagnostics"]["eligible_raw_player_position_count"],
                "tracked_z_rows": report["diagnostics"]["scored_tracked_z_player_position_count"],
                "unavailable_positions": unavailable_positions,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
