#!/usr/bin/env python3
"""Materialize one execution-only 2024 MLB Statcast segment for framing recovery.

This script changes only execution geometry. It queries non-overlapping pieces of
the already-authorized 2024 MLB regular-season envelope and performs no framing
calculation, fitting, scoring, or 2025 access.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path

import polars as pl

from sportsdataverse.mlb.mlb_statcast_extra import mlb_statcast_search

PACKAGE_VERSION = "0.0.75"
SEASON = 2024
CHUNK_DAYS = 7
WINDOWS = {
    "mar": ("2024-03-01", "2024-03-31"),
    "apr": ("2024-04-01", "2024-04-30"),
    "may": ("2024-05-01", "2024-05-31"),
    "jun": ("2024-06-01", "2024-06-30"),
    "jul": ("2024-07-01", "2024-07-31"),
    "aug": ("2024-08-01", "2024-08-31"),
    "sep": ("2024-09-01", "2024-09-30"),
    "oct": ("2024-10-01", "2024-10-15"),
}
REQUIRED = {
    "game_pk",
    "at_bat_number",
    "pitch_number",
    "game_date",
    "description",
    "plate_x",
    "plate_z",
    "sz_top",
    "sz_bot",
    "stand",
    "balls",
    "strikes",
    "delta_run_exp",
    "fielder_2",
}


def _sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segment", choices=sorted(WINDOWS), required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected sportsdataverse {PACKAGE_VERSION}, observed {installed}")
    start, end = WINDOWS[args.segment]
    print(f"Fetching 2024 MLB framing segment {args.segment}: {start}..{end}", flush=True)
    pitches = mlb_statcast_search(
        start,
        end,
        season=SEASON,
        game_type="R",
        chunk_days=CHUNK_DAYS,
    )
    if pitches.is_empty():
        raise RuntimeError(f"empty 2024 framing source segment {args.segment}")
    missing = sorted(REQUIRED - set(pitches.columns))
    if missing:
        raise RuntimeError(f"segment {args.segment} missing columns: {missing}")
    if "game_year" in pitches.columns:
        years = {
            int(value)
            for value in pitches.get_column("game_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        }
        if years != {SEASON}:
            raise RuntimeError(f"segment {args.segment} unexpected game_year values: {sorted(years)}")
    if "game_type" in pitches.columns:
        game_types = {
            str(value)
            for value in pitches.get_column("game_type").cast(pl.Utf8).drop_nulls().unique().to_list()
        }
        if game_types and game_types != {"R"}:
            raise RuntimeError(f"segment {args.segment} unexpected game_type values: {sorted(game_types)}")

    keep = sorted(REQUIRED | ({"game_year", "game_type"} & set(pitches.columns)))
    source = pitches.select(keep)
    key = ["game_pk", "at_bat_number", "pitch_number"]
    if source.group_by(key).len().filter(pl.col("len") > 1).height:
        raise RuntimeError(f"segment {args.segment} contains duplicate pitch keys")

    root = args.output_root
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"statcast-framing-2024-{args.segment}.parquet"
    source.write_parquet(path, compression="zstd")
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_2024_framing_predictor_segment",
        "status": "segment_materialized",
        "segment": args.segment,
        "query": {
            "season": SEASON,
            "start": start,
            "end": end,
            "game_type": "R",
            "chunk_days": CHUNK_DAYS,
        },
        "package_version": installed,
        "row_count": int(source.height),
        "column_count": len(source.columns),
        "storage": {
            "path": str(path).replace("\\", "/"),
            "sha256": _sha_file(path),
            "file_size_bytes": path.stat().st_size,
        },
        "boundary": {
            "2025_source_accessed": False,
            "framing_derived": False,
            "model_parameters_loaded": False,
            "model_fit": False,
            "model_scoring_performed": False,
            "war_calculated": False,
        },
    }
    (root / f"report-{args.segment}.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"segment": args.segment, "rows": source.height}, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())