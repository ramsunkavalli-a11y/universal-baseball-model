#!/usr/bin/env python3
"""Assemble fixed 2023 Challenger-2 confirmation evidence before scoring.

This gate combines the accepted valued 2021-22 history with the authorized 2023
contact-value source, attaches the unchanged frozen terminal-value scale to 2023,
and fits the same additive contact-bin + level baseline at the three fixed 2023
cutoffs. It materializes future target rows but performs no richer feature
attachment, prediction loss, calibration, transport decision, or confirmation
acceptance calculation.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any

import polars as pl

import universal_baseball.current_talent_contact_value_evidence as evidence
from universal_baseball.current_talent_contact_value_baseline import (
    fit_contact_value_baseline_sufficient_statistics,
)
from universal_baseball.current_talent_validation import PRIMARY_FUTURE_HORIZON, future_window
from universal_baseball.performance_season import CONTACT_CORE_BINS
from universal_baseball.storage import write_canonical_parquet


CONFIRMATION_CUTOFFS = (
    date(2023, 7, 15),
    date(2023, 8, 1),
    date(2023, 9, 1),
)
EXPECTED_LEVELS = {"MLB", "AAA", "AA", "HIGH_A", "SINGLE_A", "ROOKIE_COMPLEX"}
DEVELOPMENT_CHRONOLOGY_RUN_ID = 32074805618


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-chronology-root", type=Path, required=True)
    parser.add_argument("--confirmation-source-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-confirmation-evidence"),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    paths = sorted(root.glob(pattern))
    if len(paths) != 1:
        raise RuntimeError(f"expected one {label}, found {len(paths)}")
    return paths[0]


def _source_tables(root: Path) -> list[Path]:
    milb = sorted(root.glob("**/tables/contact_value_target_contacts_2023_*.parquet"))
    mlb = sorted(root.glob("**/tables/current_talent_contact_value_target_2023_mlb.parquet"))
    if len(milb) != 5:
        raise RuntimeError(f"expected five 2023 MiLB target tables, found {len(milb)}")
    if len(mlb) != 1:
        raise RuntimeError(f"expected one 2023 MLB target table, found {len(mlb)}")
    return [*milb, *mlb]


def _count(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(row[column]): int(row["event_count"])
        for row in frame.group_by(column)
        .agg(pl.len().cast(pl.Int64).alias("event_count"))
        .sort(column)
        .to_dicts()
    }


def _cutoff_surface(
    combined: pl.DataFrame,
    *,
    cutoff: date,
    table_dir: Path,
) -> dict[str, Any]:
    start, end = future_window(cutoff, PRIMARY_FUTURE_HORIZON)
    baseline = combined.filter(pl.col("event_date") < pl.lit(cutoff))
    future = combined.filter(
        (pl.col("event_date") >= pl.lit(start))
        & (pl.col("event_date") < pl.lit(end))
    ).sort(["event_date", *evidence.CONTACT_VALUE_TARGET_KEY])
    if baseline.is_empty() or future.is_empty():
        raise RuntimeError(f"empty confirmation baseline/future surface at {cutoff}")
    if baseline.get_column("event_date").max() >= cutoff:
        raise RuntimeError(f"confirmation baseline leakage at {cutoff}")
    if future.get_column("event_date").min() < cutoff or future.get_column("event_date").max() >= end:
        raise RuntimeError(f"confirmation future-window leakage at {cutoff}")

    baseline_bins = set(baseline.get_column("contact_bin").unique().to_list())
    future_bins = set(future.get_column("contact_bin").unique().to_list())
    baseline_levels = set(baseline.get_column("level_group").unique().to_list())
    future_levels = set(future.get_column("level_group").unique().to_list())
    if baseline_bins != set(CONTACT_CORE_BINS):
        raise RuntimeError(f"confirmation baseline {cutoff} lost contact-bin support")
    if baseline_levels != EXPECTED_LEVELS:
        raise RuntimeError(f"confirmation baseline {cutoff} lost level support: {sorted(baseline_levels)}")
    if future_bins - baseline_bins or future_levels - baseline_levels:
        raise RuntimeError(f"confirmation future {cutoff} has unsupported bin/level")

    keys = list(evidence.CONTACT_VALUE_TARGET_KEY)
    if future.group_by(keys).len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"confirmation future {cutoff} has duplicate target keys")

    fitted, cells = fit_contact_value_baseline_sufficient_statistics(
        combined,
        cutoff_date=cutoff,
    )
    if cells.height != len(CONTACT_CORE_BINS) * len(EXPECTED_LEVELS):
        raise RuntimeError(f"confirmation baseline {cutoff} lacks all 60 cells")
    if fitted.max_training_event_date >= cutoff:
        raise RuntimeError(f"confirmation fitted baseline leakage at {cutoff}")
    if fitted.fitted_event_count != int(baseline.height):
        raise RuntimeError(f"confirmation baseline {cutoff} fitted event count mismatch")

    token = cutoff.isoformat()
    cells.write_csv(table_dir / f"baseline_cells_{token}.csv")
    future_storage = write_canonical_parquet(
        future,
        table_dir / f"future_contacts_{token}.parquet",
        table_name=f"current_talent_contact_value_confirmation_future_{token}",
    ).as_record()
    return {
        "cutoff_date": token,
        "future_window_start": start.isoformat(),
        "future_window_end_exclusive": end.isoformat(),
        "baseline_contact_count": int(baseline.height),
        "baseline_first_event_date": baseline.get_column("event_date").min().isoformat(),
        "baseline_last_event_date": baseline.get_column("event_date").max().isoformat(),
        "future_target_contact_count": int(future.height),
        "future_first_event_date": future.get_column("event_date").min().isoformat(),
        "future_last_event_date": future.get_column("event_date").max().isoformat(),
        "future_target_key_count": int(future.height),
        "future_contact_bins": sorted(str(value) for value in future_bins),
        "future_level_groups": sorted(str(value) for value in future_levels),
        "baseline_cell_count": int(cells.height),
        "baseline_fit": {
            "intercept": fitted.intercept,
            "contact_bin_effects": fitted.contact_bin_effects,
            "level_group_effects": fitted.level_group_effects,
            "fitted_event_count": fitted.fitted_event_count,
            "parameter_count": fitted.parameter_count,
            "fitted_level_groups": list(fitted.fitted_level_groups),
            "max_training_event_date": fitted.max_training_event_date.isoformat(),
            "full_rank": True,
            "cutoff_safe": True,
        },
        "future_storage": future_storage,
    }


def main() -> int:
    args = _parse_args()
    development_path = _one(
        args.development_chronology_root,
        "**/current_talent_contact_value_combined_2021_2022.parquet",
        "accepted 2021-22 combined valued evidence",
    )
    prior = pl.read_parquet(development_path)
    if prior.is_empty() or "terminal_value" not in prior.columns:
        raise RuntimeError("accepted 2021-22 chronology is empty or unvalued")
    if set(prior.get_column("event_date").dt.year().unique().to_list()) != {2021, 2022}:
        raise RuntimeError("accepted prior chronology does not contain exactly 2021-22")

    source_paths = _source_tables(args.confirmation_source_root)
    source_frames = [pl.read_parquet(path) for path in source_paths]
    if any(frame.is_empty() for frame in source_frames):
        raise RuntimeError("2023 confirmation source contains an empty target table")

    # The development evidence helper is deliberately default-closed to 2021-22.
    # Confirmation is now formally authorized, so widen only this process-local
    # source-year guard; all terminal/bin/level/value semantics remain unchanged.
    evidence.CONTACT_VALUE_ALLOWED_SOURCE_YEARS = frozenset({2021, 2022, 2023})
    valued_2023, metrics_2023 = evidence.prepare_contact_value_evidence(source_frames)
    if set(valued_2023.get_column("event_date").dt.year().unique().to_list()) != {2023}:
        raise RuntimeError("confirmation source did not produce exactly 2023 valued contacts")

    combined = pl.concat([prior, valued_2023], how="vertical_relaxed").sort(
        ["event_date", *evidence.CONTACT_VALUE_TARGET_KEY]
    )
    if set(combined.get_column("event_date").dt.year().unique().to_list()) != {2021, 2022, 2023}:
        raise RuntimeError("confirmation combined valued evidence year mismatch")
    keys = list(evidence.CONTACT_VALUE_TARGET_KEY)
    duplicates = combined.group_by(keys).len().filter(pl.col("len") != 1)
    if not duplicates.is_empty():
        raise RuntimeError(f"confirmation combined evidence has {duplicates.height} duplicate target keys")

    output_root = args.output_root
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    combined_storage = write_canonical_parquet(
        combined,
        table_dir / "current_talent_contact_value_combined_2021_2022_2023.parquet",
        table_name="current_talent_contact_value_combined_2021_2022_2023",
    ).as_record()
    surfaces = [
        _cutoff_surface(combined, cutoff=cutoff, table_dir=table_dir)
        for cutoff in CONFIRMATION_CUTOFFS
    ]

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_confirmation_evidence_pre_scoring",
        "development_chronology_run_id": DEVELOPMENT_CHRONOLOGY_RUN_ID,
        "confirmation_cutoffs": [cutoff.isoformat() for cutoff in CONFIRMATION_CUTOFFS],
        "prior_valued_contact_count": int(prior.height),
        "confirmation_2023_source_frame_count": len(source_frames),
        "confirmation_2023_valued_contact_count": int(valued_2023.height),
        "combined_valued_contact_count": int(combined.height),
        "combined_first_event_date": combined.get_column("event_date").min().isoformat(),
        "combined_last_event_date": combined.get_column("event_date").max().isoformat(),
        "observed_years": sorted(combined.get_column("event_date").dt.year().unique().to_list()),
        "terminal_group_counts": _count(combined, "terminal_outcome_group"),
        "contact_bin_counts": _count(combined, "contact_bin"),
        "level_group_counts": _count(combined, "level_group"),
        "confirmation_source_metrics": metrics_2023,
        "cutoff_surfaces": surfaces,
        "combined_storage": combined_storage,
        "boundary": {
            "2023_source_evidence_accessed": True,
            "terminal_values_attached_unchanged": True,
            "baseline_fitted": True,
            "richer_features_attached": False,
            "confirmation_coefficients_changed": False,
            "future_predictions_computed": False,
            "confirmation_losses_computed": False,
            "calibration_computed": False,
            "confirmation_decision_computed": False,
            "model_scoring": False,
            "network_requests_performed": False,
        },
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
