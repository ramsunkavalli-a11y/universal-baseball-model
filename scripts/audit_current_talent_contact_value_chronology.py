#!/usr/bin/env python3
"""Audit combined accepted Challenger-2 contact-value evidence before scoring.

The workflow that calls this script seeds only already-accepted 2021-22 MLB and
MiLB target artifacts.  This audit performs no network requests, no richer
feature attachment, no residual/baseline prediction, and no MSE/MAE scoring.

It validates the common source schema, attaches the frozen terminal-value scale,
and proves the actual source surface supports the four frozen chronology windows:
baseline strictly before cutoff and future target in [cutoff, cutoff+90 days).
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_contact_value_evidence import (
    CONTACT_VALUE_FROZEN_CUTOFFS,
    CONTACT_VALUE_TARGET_KEY,
    prepare_contact_value_evidence,
)
from universal_baseball.current_talent_validation import PRIMARY_FUTURE_HORIZON, future_window
from universal_baseball.performance_season import CONTACT_CORE_BINS
from universal_baseball.storage import write_canonical_parquet


EXPECTED_MILB_TABLE_COUNT = 10
EXPECTED_MLB_TABLE_COUNT = 2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--milb-root", type=Path, required=True)
    parser.add_argument("--mlb-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-chronology"),
    )
    return parser.parse_args()


def _milb_target_tables(root: Path) -> list[Path]:
    return sorted(root.glob("**/tables/contact_value_target_contacts_*.parquet"))


def _mlb_target_tables(root: Path) -> list[Path]:
    return sorted(root.glob("**/tables/current_talent_contact_value_target_*_mlb.parquet"))


def _read_sources(paths: list[Path]) -> list[pl.DataFrame]:
    frames: list[pl.DataFrame] = []
    for path in paths:
        frame = pl.read_parquet(path)
        if frame.is_empty():
            raise RuntimeError(f"accepted contact-value target table is empty: {path}")
        frames.append(frame)
    return frames


def _counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(row[column]): int(row["count"])
        for row in frame.group_by(column)
        .agg(pl.len().cast(pl.Int64).alias("count"))
        .sort(column)
        .to_dicts()
    }


def _window_metrics(valued: pl.DataFrame, cutoff: date) -> dict[str, Any]:
    start, end = future_window(cutoff, PRIMARY_FUTURE_HORIZON)
    baseline = valued.filter(pl.col("event_date") < pl.lit(cutoff))
    future = valued.filter(
        (pl.col("event_date") >= pl.lit(start))
        & (pl.col("event_date") < pl.lit(end))
    )
    if baseline.is_empty() or future.is_empty():
        raise RuntimeError(f"empty baseline/future surface at cutoff {cutoff}")

    baseline_max = baseline.get_column("event_date").max()
    future_min = future.get_column("event_date").min()
    future_max = future.get_column("event_date").max()
    if baseline_max >= cutoff:
        raise RuntimeError(f"baseline leakage at cutoff {cutoff}: {baseline_max}")
    if future_min < cutoff or future_max >= end:
        raise RuntimeError(
            f"future-window leakage at cutoff {cutoff}: min={future_min}, max={future_max}, end={end}"
        )

    baseline_bins = set(baseline.get_column("contact_bin").unique().to_list())
    future_bins = set(future.get_column("contact_bin").unique().to_list())
    missing_bins = sorted(set(CONTACT_CORE_BINS) - baseline_bins)
    if missing_bins:
        raise RuntimeError(f"baseline {cutoff} lacks frozen contact bins: {missing_bins}")
    if future_bins - baseline_bins:
        raise RuntimeError(
            f"future {cutoff} has contact bins absent from baseline: {sorted(future_bins - baseline_bins)}"
        )

    baseline_levels = set(baseline.get_column("level_group").unique().to_list())
    future_levels = set(future.get_column("level_group").unique().to_list())
    if "MLB" not in baseline_levels:
        raise RuntimeError(f"baseline {cutoff} lacks MLB reference level")
    if future_levels - baseline_levels:
        raise RuntimeError(
            f"future {cutoff} has levels absent from baseline: {sorted(future_levels - baseline_levels)}"
        )

    key_columns = list(CONTACT_VALUE_TARGET_KEY)
    baseline_keys = baseline.select(key_columns)
    future_keys = future.select(key_columns)
    if baseline_keys.group_by(key_columns).len().filter(pl.col("len") > 1).height:
        raise RuntimeError(f"baseline {cutoff} contains duplicate event keys")
    if future_keys.group_by(key_columns).len().filter(pl.col("len") > 1).height:
        raise RuntimeError(f"future {cutoff} contains duplicate event keys")
    overlap = baseline_keys.join(future_keys, on=key_columns, how="inner")
    if not overlap.is_empty():
        raise RuntimeError(f"baseline/future key overlap at cutoff {cutoff}")

    # These cell sufficient statistics are the exact information needed for the
    # frozen event-weighted additive baseline.  They are persisted so the next
    # batch can prove/optimize the fit without rereading raw source artifacts.
    cells = (
        baseline.group_by("contact_bin", "level_group")
        .agg(
            pl.len().cast(pl.Int64).alias("event_count"),
            pl.col("terminal_value").sum().alias("terminal_value_sum"),
        )
        .sort("contact_bin", "level_group")
    )
    observed_cell_pairs = int(cells.height)

    return {
        "cutoff_date": cutoff.isoformat(),
        "future_window_start": start.isoformat(),
        "future_window_end_exclusive": end.isoformat(),
        "future_window_calendar_days": int(PRIMARY_FUTURE_HORIZON.calendar_days),
        "baseline_contact_count": int(baseline.height),
        "baseline_first_event_date": baseline.get_column("event_date").min().isoformat(),
        "baseline_last_event_date": baseline_max.isoformat(),
        "future_target_contact_count": int(future.height),
        "future_first_event_date": future_min.isoformat(),
        "future_last_event_date": future_max.isoformat(),
        "baseline_contact_bins": sorted(str(value) for value in baseline_bins),
        "future_contact_bins": sorted(str(value) for value in future_bins),
        "baseline_level_groups": sorted(str(value) for value in baseline_levels),
        "future_level_groups": sorted(str(value) for value in future_levels),
        "baseline_contact_bin_level_cell_count": observed_cell_pairs,
        "future_target_key_count": int(future_keys.height),
        "paired_target_row_contract": "single_future_target_key_surface_for_comparator_and_richer",
        "baseline_fitted": False,
        "model_scoring": False,
        "richer_features_attached": False,
        "richer_residual_fitted": False,
        "accessed_2023": False,
    }


def main() -> int:
    args = _parse_args()
    milb_paths = _milb_target_tables(args.milb_root)
    mlb_paths = _mlb_target_tables(args.mlb_root)
    if len(milb_paths) != EXPECTED_MILB_TABLE_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_MILB_TABLE_COUNT} accepted MiLB target tables, found {len(milb_paths)}"
        )
    if len(mlb_paths) != EXPECTED_MLB_TABLE_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_MLB_TABLE_COUNT} accepted MLB target tables, found {len(mlb_paths)}"
        )

    source_frames = _read_sources([*milb_paths, *mlb_paths])
    valued, prepare_metrics = prepare_contact_value_evidence(source_frames)
    if set(valued.get_column("event_date").dt.year().unique().to_list()) != {2021, 2022}:
        raise RuntimeError("combined valued evidence does not contain exactly 2021 and 2022")

    output_root = args.output_root
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        valued,
        table_dir / "current_talent_contact_value_combined_2021_2022.parquet",
        table_name="current_talent_contact_value_combined_2021_2022",
    ).as_record()

    windows = [_window_metrics(valued, cutoff) for cutoff in CONTACT_VALUE_FROZEN_CUTOFFS]
    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_combined_chronology",
        "accepted_source_runs": {
            "milb": 32070152452,
            "mlb": 32074097045,
        },
        "source_table_counts": {
            "milb": len(milb_paths),
            "mlb": len(mlb_paths),
            "total": len(source_frames),
        },
        "source_table_paths": [str(path) for path in [*milb_paths, *mlb_paths]],
        "combined": {
            **prepare_metrics,
            "terminal_outcome_group_counts": _counts(valued, "terminal_outcome_group"),
            "contact_bin_counts": _counts(valued, "contact_bin"),
            "level_group_counts": _counts(valued, "level_group"),
        },
        "cutoff_surfaces": windows,
        "storage": storage,
        "boundary": {
            "network_requests_performed": False,
            "model_scoring": False,
            "richer_features_attached": False,
            "richer_residual_fitted": False,
            "accessed_2023": False,
            "terminal_values_attached": True,
            "baseline_fitted": False,
        },
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
