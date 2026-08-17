#!/usr/bin/env python3
"""Audit frozen Challenger-2 richer feature attachment before any score exists.

Inputs are only already-accepted artifacts:

- combined valued 2021-22 contact targets from chronology run 32074805618;
- reconciled 2021-22 tracked BBE from materialization run 32046012977.

The gate reuses challenger-1 feature construction, fits standardization once from
eligible 2021-07-15 player features, applies those moments unchanged to 2022,
and materializes the exact richer-eligible paired future-event tables.  It does
not fit richer coefficients, apply baseline/richer predictions, compute losses or
calibration, or access 2023.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_batted_ball_reconciliation import (
    RECONCILED_TRACKED_BBE_SCHEMA,
)
from universal_baseball.current_talent_contact_value_evidence import (
    CONTACT_VALUE_TARGET_KEY,
)
from universal_baseball.current_talent_contact_value_features import (
    CONTACT_VALUE_FEATURE_CUTOFFS,
    CONTACT_VALUE_FEATURE_TRAINING_CUTOFF,
    attach_contact_value_features_to_future_contacts,
    prepare_contact_value_feature_snapshots,
)
from universal_baseball.current_talent_validation import PRIMARY_FUTURE_HORIZON, future_window
from universal_baseball.storage import write_canonical_parquet


TRACKING_RUN_ID = 32046012977
CHRONOLOGY_RUN_ID = 32074805618


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-root", type=Path, required=True)
    parser.add_argument("--chronology-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-features"),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    paths = sorted(root.glob(pattern))
    if len(paths) != 1:
        raise RuntimeError(f"expected one {label}, found {len(paths)}")
    return paths[0]


def _load_tracking(root: Path, season: int) -> pl.DataFrame:
    path = _one(
        root,
        f"**/{season}/combined/reconciled_tracked_bbe_{season}.parquet",
        f"{season} reconciled tracked BBE parquet",
    )
    frame = pl.read_parquet(path)
    missing = sorted(set(RECONCILED_TRACKED_BBE_SCHEMA) - set(frame.columns))
    if missing:
        raise RuntimeError(f"{season} tracking parquet missing fields: {missing}")
    if frame.is_empty():
        raise RuntimeError(f"{season} tracking parquet is empty")
    return frame.select(*RECONCILED_TRACKED_BBE_SCHEMA).cast(
        RECONCILED_TRACKED_BBE_SCHEMA, strict=True
    )


def _load_tracking_checkpoint(root: Path) -> dict[str, Any]:
    path = _one(root, "**/checkpoint.json", "tracking checkpoint")
    report = json.loads(path.read_text())
    if report.get("gate") != "current_talent_batted_ball_tracking_materialization":
        raise RuntimeError("tracking artifact has wrong checkpoint gate")
    if report.get("canonical_model_bbe_contract") != "result_producing_non_bunt_pitch_grain_v1":
        raise RuntimeError("tracking artifact has wrong canonical BBE contract")
    if report.get("development_tracking_ready") is not True:
        raise RuntimeError("tracking artifact is not development-ready")
    if set(report.get("seasons", {})) != {"2021", "2022"}:
        raise RuntimeError("tracking checkpoint does not contain exactly 2021/2022")
    return report


def _load_valued_contacts(root: Path) -> pl.DataFrame:
    path = _one(
        root,
        "**/current_talent_contact_value_combined_2021_2022.parquet",
        "accepted combined valued contact parquet",
    )
    frame = pl.read_parquet(path)
    required = {
        "event_date",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "player_id",
        "terminal_value",
        "contact_bin",
        "level_group",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"accepted valued contacts missing fields: {missing}")
    if frame.is_empty():
        raise RuntimeError("accepted combined valued contacts are empty")
    years = set(frame.get_column("event_date").dt.year().unique().to_list())
    if years != {2021, 2022}:
        raise RuntimeError(f"valued contacts contain unauthorized years: {sorted(years)}")
    return frame


def _future(valued: pl.DataFrame, cutoff: date) -> pl.DataFrame:
    start, end = future_window(cutoff, PRIMARY_FUTURE_HORIZON)
    frame = valued.filter(
        (pl.col("event_date") >= pl.lit(start))
        & (pl.col("event_date") < pl.lit(end))
    ).sort(["event_date", *CONTACT_VALUE_TARGET_KEY])
    if frame.is_empty():
        raise RuntimeError(f"future target is empty at {cutoff}")
    if frame.get_column("event_date").min() < cutoff:
        raise RuntimeError(f"future target leaked pre-cutoff events at {cutoff}")
    if frame.get_column("event_date").max() >= end:
        raise RuntimeError(f"future target exceeded exclusive end at {cutoff}")
    return frame


def main() -> int:
    args = _parse_args()
    checkpoint = _load_tracking_checkpoint(args.tracking_root)
    tracking_2021 = _load_tracking(args.tracking_root, 2021)
    tracking_2022 = _load_tracking(args.tracking_root, 2022)
    if int(tracking_2021.height) != int(checkpoint["seasons"]["2021"]["model_bbe"]):
        raise RuntimeError("2021 tracking row count disagrees with source checkpoint")
    if int(tracking_2022.height) != int(checkpoint["seasons"]["2022"]["model_bbe"]):
        raise RuntimeError("2022 tracking row count disagrees with source checkpoint")

    valued = _load_valued_contacts(args.chronology_root)
    prepared = prepare_contact_value_feature_snapshots(tracking_2021, tracking_2022)

    output_root = args.output_root
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    snapshot_reports: list[dict[str, Any]] = []
    for cutoff in CONTACT_VALUE_FEATURE_CUTOFFS:
        snapshot = prepared.snapshots[cutoff]
        future = _future(valued, cutoff)
        attached, attachment_metrics = attach_contact_value_features_to_future_contacts(
            future, snapshot
        )
        paired = attached.filter(pl.col("contact_value_residual_applies"))
        if paired.is_empty():
            raise RuntimeError(f"no richer-eligible paired contacts at {cutoff}")

        key_columns = list(CONTACT_VALUE_TARGET_KEY)
        expected_keys = future.select(key_columns).sort(key_columns)
        attached_keys = attached.select(key_columns).sort(key_columns)
        if not attached_keys.equals(expected_keys):
            raise RuntimeError(f"feature attachment changed target keys at {cutoff}")
        paired_keys = paired.select(key_columns).sort(key_columns)
        if paired_keys.group_by(key_columns).len().filter(pl.col("len") != 1).height:
            raise RuntimeError(f"paired target has duplicate keys at {cutoff}")

        slug = cutoff.isoformat()
        feature_storage = write_canonical_parquet(
            snapshot.raw_features,
            table_dir / f"raw_features_{slug}.parquet",
            table_name=f"current_talent_contact_value_raw_features_{slug}",
        ).as_record()
        standardized_storage = write_canonical_parquet(
            snapshot.standardized_features,
            table_dir / f"standardized_features_{slug}.parquet",
            table_name=f"current_talent_contact_value_standardized_features_{slug}",
        ).as_record()
        capability_storage = write_canonical_parquet(
            snapshot.capability,
            table_dir / f"capability_{slug}.parquet",
            table_name=f"current_talent_contact_value_capability_{slug}",
        ).as_record()
        paired_storage = write_canonical_parquet(
            paired,
            table_dir / f"paired_future_contacts_{slug}.parquet",
            table_name=f"current_talent_contact_value_paired_future_contacts_{slug}",
        ).as_record()

        snapshot_reports.append(
            {
                "cutoff_date": cutoff.isoformat(),
                "feature_snapshot": snapshot.metrics,
                "future_attachment": attachment_metrics,
                "storage": {
                    "raw_features": feature_storage,
                    "standardized_features": standardized_storage,
                    "capability": capability_storage,
                    "paired_future_contacts": paired_storage,
                },
            }
        )

    training_snapshot = prepared.snapshots[CONTACT_VALUE_FEATURE_TRAINING_CUTOFF]
    training_standardized = training_snapshot.standardized_features
    training_eligible = training_standardized.filter(
        pl.col("tracked_bbe_eligible")
        & pl.col("z_mean_exit_velocity").is_not_null()
        & pl.col("z_sweet_spot_share").is_not_null()
    )
    if training_eligible.height != prepared.standardization.fitted_player_count:
        raise RuntimeError("standardization fitted-player count changed after preparation")

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_richer_feature_attachment_pre_scoring",
        "accepted_input_runs": {
            "tracking": TRACKING_RUN_ID,
            "chronology": CHRONOLOGY_RUN_ID,
        },
        "tracking_checkpoint": {
            "canonical_model_bbe_contract": checkpoint["canonical_model_bbe_contract"],
            "development_tracking_ready": checkpoint["development_tracking_ready"],
            "2021_model_bbe": int(checkpoint["seasons"]["2021"]["model_bbe"]),
            "2022_model_bbe": int(checkpoint["seasons"]["2022"]["model_bbe"]),
        },
        "standardization": asdict(prepared.standardization),
        "preparation": prepared.metrics,
        "snapshots": snapshot_reports,
        "boundary": {
            "network_requests_performed": False,
            "model_scoring": False,
            "baseline_predictions_applied": False,
            "richer_coefficients_fitted": False,
            "richer_predictions_applied": False,
            "losses_computed": False,
            "calibration_computed": False,
            "accessed_2023": False,
            "zero_fallback_encoded": True,
            "paired_target_rows_materialized": True,
        },
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
