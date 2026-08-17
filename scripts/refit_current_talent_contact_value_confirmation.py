#!/usr/bin/env python3
"""Freeze Challenger-2 confirmation coefficients from 2021+2022 training snapshots.

This is authorized only after the fixed 2022 development gate passes. It uses the
annual 2021-07-15 and 2022-07-15 training snapshots, refits feature
standardization across eligible player-snapshot rows, and refits the unchanged
no-intercept two-feature WLS. It accesses no 2023 evidence and computes no
confirmation score.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
from math import isfinite
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_batted_ball_standardization import (
    fit_batted_ball_feature_standardization,
    standardize_batted_ball_quality_features,
)
from universal_baseball.current_talent_contact_value import (
    ContactValueBaselineFit,
    ContactValueResidualFit,
    build_contact_value_residual_player_training,
    predict_contact_value_baseline,
)


TRAINING_CUTOFFS = (date(2021, 7, 15), date(2022, 7, 15))
BASELINE_RUN_ID = 32075112279
FEATURE_RUN_ID = 32075892988


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument("--development-result", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-confirmation-refit"),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label}, found {len(matches)}")
    return matches[0]


def _require_development_pass(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text())
    if report.get("gate") != "current_talent_contact_value_2022_development":
        raise RuntimeError("unexpected Challenger 2 development result")
    if report.get("eligible_for_fixed_2023_confirmation") is not True:
        raise RuntimeError("2022 development did not authorize confirmation refit")
    if not all(report.get("promotion_checks", {}).values()):
        raise RuntimeError("not all frozen 2022 promotion checks passed")
    boundary = report.get("boundary", {})
    if boundary.get("accessed_2023") is not False or boundary.get("confirmation_data_present") is not False:
        raise RuntimeError("development result contains confirmation evidence")
    return report


def _load_baselines(root: Path) -> dict[date, ContactValueBaselineFit]:
    report = json.loads(_one(root, "**/report.json", "baseline report").read_text())
    output: dict[date, ContactValueBaselineFit] = {}
    for row in report.get("fits", []):
        cutoff = date.fromisoformat(row["cutoff_date"])
        if cutoff not in TRAINING_CUTOFFS:
            continue
        if row.get("full_rank") is not True or row.get("cutoff_safe") is not True:
            raise RuntimeError(f"unaccepted training baseline at {cutoff}")
        coefficients = row["coefficients"]
        output[cutoff] = ContactValueBaselineFit(
            cutoff_date=cutoff,
            intercept=float(coefficients["intercept"]),
            contact_bin_effects={str(k): float(v) for k, v in coefficients["contact_bin_effects"].items()},
            level_group_effects={str(k): float(v) for k, v in coefficients["level_group_effects"].items()},
            fitted_event_count=int(row["fitted_event_count"]),
            parameter_count=int(row["parameter_count"]),
            fitted_level_groups=tuple(str(v) for v in row["fitted_level_groups"]),
            max_training_event_date=date.fromisoformat(row["max_training_event_date"]),
        )
    if set(output) != set(TRAINING_CUTOFFS):
        raise RuntimeError("baseline artifact lacks both annual training snapshots")
    return output


def _fit_pooled_snapshot_wls(rows: pl.DataFrame) -> ContactValueResidualFit:
    required = {
        "as_of_date",
        "player_id",
        "z_mean_exit_velocity",
        "z_sweet_spot_share",
        "mean_future_contact_value_residual",
        "supported_future_target_contacts",
    }
    missing = sorted(required - set(rows.columns))
    if missing:
        raise RuntimeError(f"pooled player-snapshot WLS table missing fields: {missing}")
    duplicate = rows.group_by(["as_of_date", "player_id"]).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise RuntimeError("pooled confirmation WLS violates as_of_date + player_id grain")

    s11 = s12 = s22 = t1 = t2 = 0.0
    total_weight = 0
    for row in rows.iter_rows(named=True):
        x1 = float(row["z_mean_exit_velocity"])
        x2 = float(row["z_sweet_spot_share"])
        y = float(row["mean_future_contact_value_residual"])
        weight = int(row["supported_future_target_contacts"])
        if not all(isfinite(v) for v in (x1, x2, y)) or weight <= 0:
            raise RuntimeError("invalid pooled confirmation WLS row")
        total_weight += weight
        s11 += weight * x1 * x1
        s12 += weight * x1 * x2
        s22 += weight * x2 * x2
        t1 += weight * x1 * y
        t2 += weight * x2 * y
    determinant = s11 * s22 - s12 * s12
    scale = max(abs(s11 * s22), abs(s12 * s12), 1.0)
    if not isfinite(determinant) or determinant <= 1e-12 * scale:
        raise RuntimeError("pooled confirmation residual WLS is not full rank")
    beta_ev = (t1 * s22 - t2 * s12) / determinant
    beta_ss = (s11 * t2 - s12 * t1) / determinant
    return ContactValueResidualFit(
        beta_mean_exit_velocity=float(beta_ev),
        beta_sweet_spot_share=float(beta_ss),
        fitted_player_count=int(rows.height),
        fitted_future_contact_count=int(total_weight),
        determinant=float(determinant),
    )


def main() -> int:
    args = _parse_args()
    development = _require_development_pass(args.development_result)
    baselines = _load_baselines(args.baseline_root)

    raw_frames: list[pl.DataFrame] = []
    for cutoff in TRAINING_CUTOFFS:
        token = cutoff.isoformat()
        raw = pl.read_parquet(_one(args.feature_root, f"**/raw_features_{token}.parquet", f"raw features {token}"))
        if "as_of_date" not in raw.columns:
            raw = raw.with_columns(pl.lit(cutoff).cast(pl.Date).alias("as_of_date"))
        raw_frames.append(raw)
    pooled_raw = pl.concat(raw_frames, how="vertical_relaxed")
    standardization = fit_batted_ball_feature_standardization(pooled_raw)

    snapshot_reports: list[dict[str, Any]] = []
    pooled_player_training: list[pl.DataFrame] = []
    for cutoff, raw in zip(TRAINING_CUTOFFS, raw_frames, strict=True):
        token = cutoff.isoformat()
        standardized = standardize_batted_ball_quality_features(raw, standardization)
        paired = pl.read_parquet(
            _one(args.feature_root, f"**/paired_future_contacts_{token}.parquet", f"paired training contacts {token}")
        )
        paired = paired.drop(["z_mean_exit_velocity", "z_sweet_spot_share"]).join(
            standardized.select(
                "player_id",
                "tracked_bbe_eligible",
                "z_mean_exit_velocity",
                "z_sweet_spot_share",
            ),
            on="player_id",
            how="left",
            validate="m:1",
            suffix="_refit",
        )
        if paired.filter(
            ~pl.col("contact_value_residual_applies")
            | ~pl.col("tracked_bbe_eligible_refit")
            | pl.col("z_mean_exit_velocity").is_null()
            | pl.col("z_sweet_spot_share").is_null()
        ).height:
            raise RuntimeError(f"pooled standardization changed richer eligibility at {token}")

        event_training = predict_contact_value_baseline(
            paired,
            baselines[cutoff],
            output_column="baseline_contact_value",
        ).with_columns(
            (pl.col("terminal_value") - pl.col("baseline_contact_value"))
            .cast(pl.Float64)
            .alias("contact_value_residual")
        )
        player_training = build_contact_value_residual_player_training(event_training).with_columns(
            pl.lit(cutoff).cast(pl.Date).alias("as_of_date")
        )
        pooled_player_training.append(player_training)
        snapshot_reports.append(
            {
                "cutoff_date": token,
                "eligible_standardization_rows": int(raw.filter(pl.col("tracked_bbe_eligible")).height),
                "training_event_count": int(event_training.height),
                "training_player_snapshot_count": int(player_training.height),
                "baseline_fitted_event_count": baselines[cutoff].fitted_event_count,
                "baseline_max_training_event_date": baselines[cutoff].max_training_event_date.isoformat(),
            }
        )

    pooled_training = pl.concat(pooled_player_training, how="vertical_relaxed")
    fitted = _fit_pooled_snapshot_wls(pooled_training)
    expected_contacts = 69382 + 97004
    expected_player_snapshots = 621 + 976
    if fitted.fitted_future_contact_count != expected_contacts:
        raise RuntimeError("confirmation refit contact weight changed")
    if fitted.fitted_player_count != expected_player_snapshots:
        raise RuntimeError("confirmation refit player-snapshot count changed")

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_confirmation_refit_2021_2022",
        "authorized_by_development_gate": development["gate"],
        "accepted_input_runs": {
            "baseline_fit": BASELINE_RUN_ID,
            "feature_attachment": FEATURE_RUN_ID,
        },
        "training_cutoffs": [cutoff.isoformat() for cutoff in TRAINING_CUTOFFS],
        "feature_standardization": {
            "mean_exit_velocity": standardization.mean_exit_velocity,
            "scale_exit_velocity": standardization.scale_exit_velocity,
            "mean_sweet_spot_share": standardization.mean_sweet_spot_share,
            "scale_sweet_spot_share": standardization.scale_sweet_spot_share,
            "fitted_player_snapshot_count": standardization.fitted_player_count,
        },
        "training_snapshots": snapshot_reports,
        "residual_fit": asdict(fitted),
        "boundary": {
            "network_requests_performed": False,
            "uses_only_2021_2022_training_snapshots": True,
            "confirmation_scoring_performed": False,
            "accessed_2023": False,
            "feature_search_performed": False,
            "model_form_changed": False,
            "terminal_value_scale_changed": False,
        },
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
