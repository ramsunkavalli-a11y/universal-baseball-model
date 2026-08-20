#!/usr/bin/env python3
"""Aggregate the four frozen Defense-v1 tracked-source segments."""

from __future__ import annotations

import argparse
from importlib.metadata import version
import json
from pathlib import Path

import polars as pl

from materialize_defense_v1_tracked_source import PACKAGE_VERSION, _file_sha
from materialize_defense_v1_tracked_source_segment import SEGMENTS


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--segment-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/defense-v1-tracked-source"),
    )
    return parser.parse_args()


def _one(segment_root: Path, segment: str, filename: str) -> Path:
    matches = sorted(
        path
        for path in segment_root.rglob(filename)
        if path.is_file() and segment in path.parts
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one {filename} for {segment}, found {len(matches)}: {matches}"
        )
    return matches[0]


def main() -> int:
    args = _args()
    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected sportsdataverse {PACKAGE_VERSION}, observed {installed}")

    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    range_frames: list[pl.DataFrame] = []
    framing_frames: list[pl.DataFrame] = []
    diagnostics: list[dict[str, object]] = []
    queries: list[dict[str, object]] = []
    segment_inputs: list[dict[str, object]] = []

    for segment in SEGMENTS:
        report_path = _one(args.segment_root, segment, "report.json")
        report = json.loads(report_path.read_text())
        if report.get("segment") != segment:
            raise RuntimeError(f"segment report mismatch for {segment}")
        if report.get("sportsdataverse_version") != PACKAGE_VERSION:
            raise RuntimeError(f"segment package-version mismatch for {segment}")
        range_path = _one(args.segment_root, segment, "tracked_range_proxy.parquet")
        framing_path = _one(args.segment_root, segment, "tracked_framing_proxy.parquet")
        expected_range_sha = report["storage"]["range"]["sha256"]
        expected_framing_sha = report["storage"]["framing"]["sha256"]
        if _file_sha(range_path) != expected_range_sha:
            raise RuntimeError(f"range hash mismatch for {segment}")
        if _file_sha(framing_path) != expected_framing_sha:
            raise RuntimeError(f"framing hash mismatch for {segment}")
        range_frames.append(pl.read_parquet(range_path))
        framing_frames.append(pl.read_parquet(framing_path))
        diagnostics.extend(report.get("diagnostics", []))
        queries.extend(report.get("queries", []))
        segment_inputs.append(
            {
                "segment": segment,
                "range_sha256": expected_range_sha,
                "framing_sha256": expected_framing_sha,
            }
        )

    range_all = pl.concat(range_frames, how="vertical_relaxed").sort(
        ["season", "level_group", "player_id", "position"]
    )
    framing_all = pl.concat(framing_frames, how="vertical_relaxed").sort(
        ["season", "level_group", "player_id"]
    )
    range_key = ["season", "level_group", "player_id", "position"]
    framing_key = ["season", "level_group", "player_id"]
    if range_all.group_by(range_key).len().filter(pl.col("len") != 1).height:
        raise RuntimeError("aggregated tracked range source violates frozen grain")
    if framing_all.group_by(framing_key).len().filter(pl.col("len") != 1).height:
        raise RuntimeError("aggregated tracked framing source violates frozen grain")

    observed = {
        (int(row["season"]), str(row["level_group"]))
        for row in range_all.select("season", "level_group").unique().iter_rows(named=True)
    }
    required = {(2021, "MLB"), (2022, "MLB"), (2023, "MLB"), (2023, "AAA"), (2023, "TRACKED_NON_AAA")}
    if observed != required:
        raise RuntimeError(f"aggregated tracked source coverage mismatch: {sorted(observed)}")

    range_path = table_root / "tracked_range_proxy_2021_2023.parquet"
    framing_path = table_root / "tracked_framing_proxy_2021_2023.parquet"
    range_all.write_parquet(range_path, compression="zstd")
    framing_all.write_parquet(framing_path, compression="zstd")
    report = {
        "report_schema_version": "0.2",
        "gate": "defense_v1_tracked_source_materialization",
        "contract": "docs/defense-v1-tracked-challenger-contract.md",
        "execution_shape": "four_parallel_frozen_source_segments_then_hash_verified_aggregation",
        "upstream": {
            "package": "sportsdataverse",
            "package_version": installed,
            "range_function": "mlb_fielding_oaa",
            "framing_function": "mlb_catcher_framing",
        },
        "segment_inputs": segment_inputs,
        "queries": queries,
        "diagnostics": diagnostics,
        "storage": {
            "range": {
                "path": str(range_path),
                "row_count": range_all.height,
                "file_size_bytes": range_path.stat().st_size,
                "sha256": _file_sha(range_path),
            },
            "framing": {
                "path": str(framing_path),
                "row_count": framing_all.height,
                "file_size_bytes": framing_path.stat().st_size,
                "sha256": _file_sha(framing_path),
            },
        },
        "decision": {
            "tracked_source_materialized": True,
            "tracked_challenger_scoring_authorized_next": True,
            "2025_confirmation_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_source_accessed": False,
            "2025_defensive_targets_accessed": False,
            "model_fit": False,
            "source_filters_changed_from_contract": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        f"Aggregated tracked source: range={range_all.height:,}, framing={framing_all.height:,}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
