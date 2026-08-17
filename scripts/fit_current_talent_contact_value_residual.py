#!/usr/bin/env python3
"""Fit the frozen two-coefficient Challenger-2 residual from 2021 only.

This pre-development gate consumes:

- the accepted 2021-07-15 additive contact baseline coefficients;
- the accepted richer-eligible 2021-07-15 paired future contacts, whose feature
  standardization was fit strictly before that cutoff.

It forms the frozen contact-value residual target, aggregates to the mathematically
equivalent player-weighted WLS table, and fits exactly two no-intercept
coefficients.  It does not read a 2022 paired target table, score any development
fold, compute calibration, or access 2023.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_contact_value import (
    ContactValueBaselineFit,
    predict_contact_value_baseline,
    build_contact_value_residual_player_training,
    fit_contact_value_residual_wls,
)
from universal_baseball.current_talent_contact_value_features import (
    CONTACT_VALUE_FEATURE_TRAINING_CUTOFF,
)
from universal_baseball.current_talent_validation import PRIMARY_FUTURE_HORIZON, future_window
from universal_baseball.storage import write_canonical_parquet


BASELINE_RUN_ID = 32075112279
FEATURE_RUN_ID = 32075892988


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-residual-fit"),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label}, found {len(matches)}")
    return matches[0]


def _load_training_baseline(root: Path) -> ContactValueBaselineFit:
    report_path = _one(root, "**/report.json", "baseline fit report")
    report = json.loads(report_path.read_text())
    if report.get("gate") != "current_talent_contact_value_baseline_fit_pre_scoring":
        raise RuntimeError("unexpected baseline fit gate")
    if report.get("boundary", {}).get("model_scoring") is not False:
        raise RuntimeError("baseline artifact crossed scoring boundary")
    cutoff_text = CONTACT_VALUE_FEATURE_TRAINING_CUTOFF.isoformat()
    rows = [row for row in report.get("fits", []) if row.get("cutoff_date") == cutoff_text]
    if len(rows) != 1:
        raise RuntimeError("baseline artifact lacks unique 2021-07-15 fit")
    row = rows[0]
    if row.get("full_rank") is not True or row.get("cutoff_safe") is not True:
        raise RuntimeError("training baseline is not accepted full-rank/cutoff-safe")
    coefficients = row["coefficients"]
    return ContactValueBaselineFit(
        cutoff_date=CONTACT_VALUE_FEATURE_TRAINING_CUTOFF,
        intercept=float(coefficients["intercept"]),
        contact_bin_effects={
            str(key): float(value)
            for key, value in coefficients["contact_bin_effects"].items()
        },
        level_group_effects={
            str(key): float(value)
            for key, value in coefficients["level_group_effects"].items()
        },
        fitted_event_count=int(row["fitted_event_count"]),
        parameter_count=int(row["parameter_count"]),
        fitted_level_groups=tuple(str(value) for value in row["fitted_level_groups"]),
        max_training_event_date=date.fromisoformat(row["max_training_event_date"]),
    )


def _load_training_paired(root: Path) -> pl.DataFrame:
    path = _one(
        root,
        "**/paired_future_contacts_2021-07-15.parquet",
        "2021-07-15 paired future contacts",
    )
    frame = pl.read_parquet(path)
    required = {
        "event_date",
        "player_id",
        "contact_bin",
        "level_group",
        "terminal_value",
        "tracked_bbe_eligible",
        "z_mean_exit_velocity",
        "z_sweet_spot_share",
        "contact_value_residual_applies",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"paired training contacts missing fields: {missing}")
    if frame.is_empty():
        raise RuntimeError("paired training contacts are empty")
    if frame.filter(~pl.col("contact_value_residual_applies")).height:
        raise RuntimeError("paired training table contains ineligible richer rows")
    if frame.filter(~pl.col("tracked_bbe_eligible")).height:
        raise RuntimeError("paired training table contains tracked-BBE-ineligible rows")
    return frame


def main() -> int:
    args = _parse_args()
    cutoff = CONTACT_VALUE_FEATURE_TRAINING_CUTOFF
    baseline = _load_training_baseline(args.baseline_root)
    paired = _load_training_paired(args.feature_root)

    target_start, target_end = future_window(cutoff, PRIMARY_FUTURE_HORIZON)
    years = set(paired.get_column("event_date").dt.year().unique().to_list())
    if years != {2021}:
        raise RuntimeError(f"residual training target contains non-2021 years: {sorted(years)}")
    if paired.get_column("event_date").min() < target_start:
        raise RuntimeError("residual training target contains pre-cutoff outcomes")
    if paired.get_column("event_date").max() >= target_end:
        raise RuntimeError("residual training target exceeds exclusive 90-day window")

    event_training = predict_contact_value_baseline(
        paired,
        baseline,
        output_column="baseline_contact_value",
    ).with_columns(
        (pl.col("terminal_value") - pl.col("baseline_contact_value"))
        .cast(pl.Float64)
        .alias("contact_value_residual")
    )
    if event_training.filter(
        pl.col("baseline_contact_value").is_null()
        | ~pl.col("baseline_contact_value").is_finite()
        | pl.col("contact_value_residual").is_null()
        | ~pl.col("contact_value_residual").is_finite()
    ).height:
        raise RuntimeError("residual training event table contains invalid target values")

    player_training = build_contact_value_residual_player_training(event_training)
    fitted = fit_contact_value_residual_wls(player_training)
    if fitted.fitted_future_contact_count != event_training.height:
        raise RuntimeError("residual WLS weight does not equal supported paired training contacts")
    if fitted.fitted_player_count != player_training.height:
        raise RuntimeError("residual fit player count disagrees with training table")

    output_root = args.output_root
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    event_storage = write_canonical_parquet(
        event_training,
        table_dir / "residual_training_events_2021-07-15.parquet",
        table_name="current_talent_contact_value_residual_training_events_2021_07_15",
    ).as_record()
    player_storage = write_canonical_parquet(
        player_training,
        table_dir / "residual_player_training_2021-07-15.parquet",
        table_name="current_talent_contact_value_residual_player_training_2021_07_15",
    ).as_record()

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_residual_fit_2021_training_only",
        "accepted_input_runs": {
            "baseline_fit": BASELINE_RUN_ID,
            "feature_attachment": FEATURE_RUN_ID,
        },
        "training_cutoff": cutoff.isoformat(),
        "future_window_start": target_start.isoformat(),
        "future_window_end_exclusive": target_end.isoformat(),
        "training_event_count": int(event_training.height),
        "training_player_count": int(player_training.height),
        "first_training_target_date": event_training.get_column("event_date").min().isoformat(),
        "last_training_target_date": event_training.get_column("event_date").max().isoformat(),
        "baseline": {
            "cutoff_date": baseline.cutoff_date.isoformat(),
            "fitted_event_count": baseline.fitted_event_count,
            "max_training_event_date": baseline.max_training_event_date.isoformat(),
            "parameter_count": baseline.parameter_count,
        },
        "residual_fit": asdict(fitted),
        "storage": {
            "event_training": event_storage,
            "player_training": player_storage,
        },
        "boundary": {
            "network_requests_performed": False,
            "coefficient_fit_uses_2021_only": True,
            "2022_future_outcomes_accessed": False,
            "model_scoring": False,
            "development_losses_computed": False,
            "calibration_computed": False,
            "accessed_2023": False,
            "richer_coefficients_fitted": True,
            "model_form": "no_intercept_two_feature_event_equivalent_player_wls",
        },
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
