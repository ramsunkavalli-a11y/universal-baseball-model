#!/usr/bin/env python3
"""Build the fixed 2023 Challenger-2 confirmation chronology without scoring.

Reuses the already-accepted valued 2021-22 chronology, appends only the accepted
2023 target-contact source surface, attaches the unchanged frozen terminal-value
scale to 2023, and proves the three predeclared confirmation windows are
half-open and leakage-safe. No richer features, predictions, losses, calibration,
or coefficient fitting occurs here.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_contact_value import attach_frozen_terminal_values
from universal_baseball.current_talent_contact_value_evidence import (
    CONTACT_VALUE_REQUIRED_SOURCE_COLUMNS,
    CONTACT_VALUE_TARGET_KEY,
)
from universal_baseball.storage import write_canonical_parquet


CONFIRMATION_CUTOFFS = (date(2023, 7, 15), date(2023, 8, 1), date(2023, 9, 1))
HORIZON_DAYS = 90


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--development-chronology-root", type=Path, required=True)
    p.add_argument("--confirmation-source-root", type=Path, required=True)
    p.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-confirmation-chronology"),
    )
    return p.parse_args()


def one(paths: list[Path], label: str) -> Path:
    if len(paths) != 1:
        raise RuntimeError(f"expected one {label}, found {len(paths)}")
    return paths[0]


def main() -> int:
    args = parse_args()
    dev_path = one(
        sorted(args.development_chronology_root.rglob("current_talent_contact_value_combined_2021_2022.parquet")),
        "accepted 2021-22 valued chronology parquet",
    )
    dev = pl.read_parquet(dev_path)
    if set(dev.get_column("event_date").cast(pl.Date).dt.year().unique().to_list()) != {2021, 2022}:
        raise RuntimeError("development chronology is not exactly 2021-22")
    if "terminal_value" not in dev.columns:
        raise RuntimeError("development chronology is not already valued")

    source_paths = sorted(args.confirmation_source_root.rglob("contact_value_target_contacts_2023_*.parquet"))
    source_paths += sorted(args.confirmation_source_root.rglob("current_talent_contact_value_target_2023_mlb.parquet"))
    if len(source_paths) != 6:
        raise RuntimeError(f"expected six accepted 2023 source tables, found {len(source_paths)}")

    frames = []
    for path in source_paths:
        frame = pl.read_parquet(path)
        missing = sorted(set(CONTACT_VALUE_REQUIRED_SOURCE_COLUMNS) - set(frame.columns))
        if missing:
            raise RuntimeError(f"2023 source table missing columns {missing}: {path}")
        frames.append(frame.select(*CONTACT_VALUE_REQUIRED_SOURCE_COLUMNS))
    source_2023 = pl.concat(frames, how="vertical_relaxed").with_columns(
        pl.col("event_date").cast(pl.Date, strict=False)
    )
    if set(source_2023.get_column("event_date").dt.year().unique().to_list()) != {2023}:
        raise RuntimeError("confirmation source is not exactly 2023")
    key = list(CONTACT_VALUE_TARGET_KEY)
    if source_2023.group_by(key).len().filter(pl.col("len") > 1).height:
        raise RuntimeError("2023 confirmation source contains duplicate target keys")
    valued_2023 = attach_frozen_terminal_values(source_2023, require_supported=True)
    if valued_2023.get_column("terminal_value").null_count():
        raise RuntimeError("frozen terminal-value attachment incomplete for 2023")

    common = [*CONTACT_VALUE_REQUIRED_SOURCE_COLUMNS, "terminal_value"]
    combined = pl.concat(
        [dev.select(common), valued_2023.select(common)], how="vertical_relaxed"
    ).sort(["event_date", *key])
    if set(combined.get_column("event_date").dt.year().unique().to_list()) != {2021, 2022, 2023}:
        raise RuntimeError("combined confirmation chronology does not contain exactly 2021-23")
    if combined.group_by(key).len().filter(pl.col("len") > 1).height:
        raise RuntimeError("combined confirmation chronology contains duplicate target keys")

    windows = []
    for cutoff in CONFIRMATION_CUTOFFS:
        end = cutoff + timedelta(days=HORIZON_DAYS)
        baseline = combined.filter(pl.col("event_date") < pl.lit(cutoff))
        future = combined.filter(
            (pl.col("event_date") >= pl.lit(cutoff)) & (pl.col("event_date") < pl.lit(end))
        )
        if baseline.is_empty() or future.is_empty():
            raise RuntimeError(f"empty confirmation chronology surface at {cutoff}")
        bmax = baseline.get_column("event_date").max()
        fmin = future.get_column("event_date").min()
        fmax = future.get_column("event_date").max()
        if bmax >= cutoff:
            raise RuntimeError(f"baseline leakage at {cutoff}: {bmax}")
        if fmin < cutoff or fmax >= end:
            raise RuntimeError(f"future leakage at {cutoff}: {fmin}..{fmax} vs end {end}")
        future_keys = future.select(key)
        if future_keys.group_by(key).len().filter(pl.col("len") > 1).height:
            raise RuntimeError(f"duplicate future keys at {cutoff}")
        windows.append({
            "cutoff_date": cutoff.isoformat(),
            "baseline_contact_count": int(baseline.height),
            "baseline_last_event_date": bmax.isoformat(),
            "future_window_start": cutoff.isoformat(),
            "future_window_end_exclusive": end.isoformat(),
            "future_target_contact_count": int(future.height),
            "future_first_event_date": fmin.isoformat(),
            "future_last_event_date": fmax.isoformat(),
            "future_target_key_count": int(future_keys.height),
            "paired_target_row_contract": "single_future_target_key_surface_for_comparator_and_richer",
        })

    args.output_root.mkdir(parents=True, exist_ok=True)
    table_dir = args.output_root / "tables"
    table_dir.mkdir(exist_ok=True)
    storage = write_canonical_parquet(
        combined,
        table_dir / "current_talent_contact_value_combined_2021_2023.parquet",
        table_name="current_talent_contact_value_combined_2021_2023",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_confirmation_chronology_2023",
        "authorized_by": "current_talent_contact_value_confirmation_refit_2021_2022",
        "accepted_confirmation_source_run": 32082637028,
        "development_chronology_run": 32074805618,
        "combined_contact_count": int(combined.height),
        "confirmation_2023_contact_count": int(valued_2023.height),
        "cutoff_surfaces": windows,
        "storage": storage,
        "boundary": {
            "2023_source_evidence_accessed": True,
            "terminal_values_attached": True,
            "baseline_fitted": False,
            "richer_features_attached": False,
            "richer_coefficients_changed": False,
            "confirmation_scoring_performed": False,
            "losses_computed": False,
            "feature_search_performed": False,
        },
    }
    (args.output_root / "checkpoint.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
