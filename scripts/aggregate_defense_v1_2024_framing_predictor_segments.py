#!/usr/bin/env python3
"""Aggregate non-overlapping 2024 framing source segments and derive the frozen predictor.

The full-season pitch population is reassembled before calling the exact same
SportsDataverse 0.0.75 framing function used in development. The segmentation
is execution-only; feature construction is unchanged.
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

from materialize_defense_v1_2024_framing_predictor_segment import WINDOWS
from sportsdataverse.mlb.mlb_catcher_framing import mlb_catcher_framing

PACKAGE_VERSION = "0.0.75"
SEASON = 2024
MIN_TAKES = 500
MIN_CELL = 15


def _sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _storage(path: Path, name: str, rows: int) -> dict[str, Any]:
    return {
        "table_name": name,
        "path": str(path).replace("\\", "/"),
        "row_count": int(rows),
        "file_size_bytes": path.stat().st_size,
        "sha256": _sha_file(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segments-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected sportsdataverse {PACKAGE_VERSION}, observed {installed}")

    frames: list[pl.DataFrame] = []
    segment_rows: dict[str, int] = {}
    segment_hashes: dict[str, str] = {}
    for segment in WINDOWS:
        matches = list(args.segments_root.rglob(f"statcast-framing-2024-{segment}.parquet"))
        if len(matches) != 1:
            raise RuntimeError(f"expected one source file for segment={segment}, observed={matches}")
        report_matches = list(args.segments_root.rglob(f"report-{segment}.json"))
        if len(report_matches) != 1:
            raise RuntimeError(f"expected one report for segment={segment}, observed={report_matches}")
        report = json.loads(report_matches[0].read_text())
        if report.get("status") != "segment_materialized" or report.get("segment") != segment:
            raise RuntimeError(f"invalid segment report {segment}")
        if report.get("package_version") != PACKAGE_VERSION:
            raise RuntimeError(f"segment package version changed {segment}")
        if report.get("boundary", {}).get("2025_source_accessed") is not False:
            raise RuntimeError(f"segment {segment} crossed 2025 boundary")
        path = matches[0]
        observed_sha = _sha_file(path)
        if observed_sha != report.get("storage", {}).get("sha256"):
            raise RuntimeError(f"segment {segment} artifact SHA mismatch")
        frame = pl.read_parquet(path)
        if frame.height != int(report.get("row_count", -1)):
            raise RuntimeError(f"segment {segment} row-count mismatch")
        frames.append(frame)
        segment_rows[segment] = int(frame.height)
        segment_hashes[segment] = observed_sha

    pitches = pl.concat(frames, how="diagonal_relaxed")
    key = ["game_pk", "at_bat_number", "pitch_number"]
    duplicate_count = pitches.group_by(key).len().filter(pl.col("len") > 1).height
    if duplicate_count:
        raise RuntimeError(f"reassembled 2024 source has duplicate pitch keys: {duplicate_count}")
    if "game_year" in pitches.columns:
        years = {
            int(value)
            for value in pitches.get_column("game_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        }
        if years != {SEASON}:
            raise RuntimeError(f"unexpected reassembled game_year values: {sorted(years)}")
    if "game_type" in pitches.columns:
        game_types = {
            str(value)
            for value in pitches.get_column("game_type").cast(pl.Utf8).drop_nulls().unique().to_list()
        }
        if game_types and game_types != {"R"}:
            raise RuntimeError(f"unexpected reassembled game_type values: {sorted(game_types)}")

    raw = mlb_catcher_framing(pitches)
    proxy = (
        raw.with_columns(
            pl.col("catcher_id").cast(pl.Int64, strict=False).alias("player_id"),
            pl.col("takes").cast(pl.Int64, strict=False),
            pl.col("framing_runs").cast(pl.Float64, strict=False),
            pl.col("strikes_gained").cast(pl.Float64, strict=False),
        )
        .filter(pl.col("player_id").is_not_null())
        .with_columns(
            pl.lit(SEASON).alias("season"),
            pl.lit("MLB").alias("level_group"),
            pl.when(pl.col("takes") > 0)
            .then(1000.0 * pl.col("framing_runs") / pl.col("takes"))
            .otherwise(None)
            .alias("tracked_framing_per_1000_takes"),
        )
        .select(
            "season",
            "level_group",
            "player_id",
            "takes",
            "strikes_gained",
            "framing_runs",
            "tracked_framing_per_1000_takes",
        )
        .sort("player_id")
    )
    if proxy.is_empty() or proxy.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise RuntimeError("invalid reassembled 2024 framing proxy")

    eligible = proxy.filter(
        (pl.col("takes") >= MIN_TAKES)
        & pl.col("tracked_framing_per_1000_takes").is_not_null()
        & pl.col("tracked_framing_per_1000_takes").is_finite()
    )
    if eligible.height < MIN_CELL:
        raise RuntimeError(f"insufficient 2024 MLB framing cell: {eligible.height} < {MIN_CELL}")
    mean = float(eligible.get_column("tracked_framing_per_1000_takes").mean())
    sd = float(eligible.get_column("tracked_framing_per_1000_takes").std(ddof=0))
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate reassembled framing moments: mean={mean} sd={sd}")
    scored = (
        eligible.with_columns(
            ((pl.col("tracked_framing_per_1000_takes") - mean) / sd).alias("tracked_framing_z")
        )
        .select(
            "season",
            "level_group",
            "player_id",
            "takes",
            "strikes_gained",
            "framing_runs",
            "tracked_framing_per_1000_takes",
            "tracked_framing_z",
        )
        .sort("player_id")
    )
    if scored.filter(~pl.col("tracked_framing_z").is_finite()).height:
        raise RuntimeError("nonfinite reassembled tracked_framing_z")
    moments = pl.DataFrame([{
        "season": SEASON,
        "level_group": "MLB",
        "mean": mean,
        "sd": sd,
        "eligible_catcher_count": int(eligible.height),
        "tracked_z_available": True,
    }])

    root = args.output_root
    table_root = root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    proxy_path = table_root / "tracked_framing_proxy_2024_mlb.parquet"
    z_path = table_root / "tracked_framing_z_2024_mlb.parquet"
    moments_path = table_root / "tracked_framing_moments_2024_mlb.parquet"
    proxy.write_parquet(proxy_path, compression="zstd")
    scored.write_parquet(z_path, compression="zstd")
    moments.write_parquet(moments_path, compression="zstd")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_2024_mlb_framing_confirmation_predictor_source",
        "status": "source_materialized",
        "contract": "docs/defense-v1-framing-2025-confirmation-contract.md",
        "execution": {
            "mode": "parallel_nonoverlapping_source_segments_reassembled_before_feature_derivation",
            "methodology_changed": False,
            "full_query_envelope": {"start": "2024-03-01", "end": "2024-10-15", "season": 2024, "game_type": "R", "chunk_days": 7},
            "segments": {name: {"start": window[0], "end": window[1], "row_count": segment_rows[name], "sha256": segment_hashes[name]} for name, window in WINDOWS.items()},
        },
        "upstream": {
            "package": "sportsdataverse",
            "package_version": installed,
            "search_function": "mlb_statcast_search",
            "framing_function": "mlb_catcher_framing",
        },
        "feature_contract": {
            "formula": "tracked_framing_per_1000_takes = 1000 * framing_runs / takes",
            "minimum_takes": MIN_TAKES,
            "standardization": "2024 x MLB mean 0 / population SD 1",
            "minimum_eligible_catchers": MIN_CELL,
            "source_level": "MLB_only",
        },
        "diagnostics": {
            "pitch_row_count": int(pitches.height),
            "framing_proxy_catcher_count": int(proxy.height),
            "framing_total_takes": int(proxy.get_column("takes").sum() or 0),
            "eligible_framing_catcher_count": int(eligible.height),
            "tracked_framing_z_catcher_count": int(scored.height),
            "mean": mean,
            "population_sd": sd,
            "duplicate_pitch_key_count": 0,
        },
        "storage": {
            "framing_proxy": _storage(proxy_path, "defense_v1_2024_mlb_tracked_framing_proxy", proxy.height),
            "tracked_framing_z": _storage(z_path, "defense_v1_2024_mlb_tracked_framing_z", scored.height),
            "moments": _storage(moments_path, "defense_v1_2024_mlb_tracked_framing_moments", moments.height),
        },
        "decision": {
            "2024_mlb_framing_confirmation_predictor_materialized": True,
            "2025_framing_target_source_materialized": False,
            "2025_framing_target_materialization_authorized_next": True,
            "confirmation_scoring_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_source_accessed": False,
            "2025_framing_target_accessed": False,
            "model_parameters_loaded": False,
            "model_fit": False,
            "model_scoring_performed": False,
            "tracked_milb_2024_accessed": False,
            "run_value_conversion_performed": False,
            "war_calculated": False,
        },
    }
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pitch_rows": pitches.height, "eligible_catchers": eligible.height, "mean": mean, "sd": sd}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())