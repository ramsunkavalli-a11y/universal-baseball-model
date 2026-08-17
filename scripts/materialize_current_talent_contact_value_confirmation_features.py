#!/usr/bin/env python3
"""Attach frozen richer features to 2023 Challenger-2 confirmation targets.

This is a pre-scoring gate. It uses the accepted 2021-23 confirmation tracking
history, the already-frozen 2021+2022 confirmation standardization, and the
accepted 2023 future target surfaces. It does not refit standardization or richer
coefficients and computes no prediction loss, calibration, or confirmation
decision.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_batted_ball_capability import (
    build_player_tracking_capability,
)
from universal_baseball.current_talent_batted_ball_quality import (
    build_batted_ball_quality_features,
)
from universal_baseball.current_talent_batted_ball_reconciliation import (
    RECONCILED_TRACKED_BBE_SCHEMA,
)
from universal_baseball.current_talent_batted_ball_standardization import (
    BattedBallFeatureStandardization,
    standardize_batted_ball_quality_features,
)
from universal_baseball.current_talent_contact_value_features import (
    ContactValueFeatureSnapshot,
    attach_contact_value_features_to_future_contacts,
)
from universal_baseball.storage import write_canonical_parquet


CONFIRMATION_CUTOFFS = (
    date(2023, 7, 15),
    date(2023, 8, 1),
    date(2023, 9, 1),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracking-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--confirmation-refit", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-confirmation-features"),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    paths = sorted(root.glob(pattern))
    if len(paths) != 1:
        raise RuntimeError(f"expected one {label}, found {len(paths)}")
    return paths[0]


def _load_tracking(root: Path) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for season in (2021, 2022, 2023):
        path = _one(
            root,
            f"**/{season}/combined/reconciled_tracked_bbe_{season}.parquet",
            f"combined tracking {season}",
        )
        frame = pl.read_parquet(path)
        missing = sorted(set(RECONCILED_TRACKED_BBE_SCHEMA) - set(frame.columns))
        if missing:
            raise RuntimeError(f"confirmation tracking {season} missing fields: {missing}")
        if set(frame.get_column("season").unique().to_list()) != {season}:
            raise RuntimeError(f"confirmation tracking season mismatch: {season}")
        frames.append(frame.select(*RECONCILED_TRACKED_BBE_SCHEMA))
    history = pl.concat(frames, how="vertical_relaxed").sort(
        ["game_date", "game_pk", "player_id", "at_bat_number", "pitch_number"]
    )
    duplicate = history.group_by(
        ["game_pk", "player_id", "at_bat_number", "pitch_number"]
    ).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise RuntimeError("confirmation tracking history has duplicate canonical BBE keys")
    return history


def _load_standardization(path: Path) -> tuple[BattedBallFeatureStandardization, dict[str, Any]]:
    report = json.loads(path.read_text())
    if report.get("gate") != "current_talent_contact_value_confirmation_refit_2021_2022":
        raise RuntimeError("unexpected confirmation refit gate")
    boundary = report.get("boundary", {})
    if boundary.get("accessed_2023") is not False:
        raise RuntimeError("confirmation refit already accessed 2023")
    if boundary.get("confirmation_scoring_performed") is not False:
        raise RuntimeError("confirmation refit already scored confirmation")
    state = report["feature_standardization"]
    fitted = BattedBallFeatureStandardization(
        mean_exit_velocity=float(state["mean_exit_velocity"]),
        scale_exit_velocity=float(state["scale_exit_velocity"]),
        mean_sweet_spot_share=float(state["mean_sweet_spot_share"]),
        scale_sweet_spot_share=float(state["scale_sweet_spot_share"]),
        fitted_player_count=int(state["fitted_player_snapshot_count"]),
    )
    return fitted, report


def main() -> int:
    args = _parse_args()
    tracking = _load_tracking(args.tracking_root)
    standardization, refit_report = _load_standardization(args.confirmation_refit)

    output_root = args.output_root
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    fold_reports: list[dict[str, Any]] = []

    for cutoff in CONFIRMATION_CUTOFFS:
        token = cutoff.isoformat()
        future_path = _one(
            args.evidence_root,
            f"**/future_contacts_{token}.parquet",
            f"confirmation future contacts {token}",
        )
        future = pl.read_parquet(future_path)
        if future.is_empty():
            raise RuntimeError(f"empty confirmation future target at {token}")

        raw = build_batted_ball_quality_features(tracking, cutoff=cutoff)
        standardized = standardize_batted_ball_quality_features(raw, standardization)
        capability = build_player_tracking_capability(tracking, cutoff=cutoff)
        if raw.is_empty() or standardized.height != raw.height or capability.height != raw.height:
            raise RuntimeError(f"confirmation feature/capability coverage mismatch at {token}")
        if set(raw.get_column("as_of_date").unique().to_list()) != {cutoff}:
            raise RuntimeError(f"confirmation raw feature date mismatch at {token}")
        if raw.filter(pl.col("last_tracked_bbe_date") >= pl.lit(cutoff)).height:
            raise RuntimeError(f"confirmation feature leakage at {token}")

        snapshot = ContactValueFeatureSnapshot(
            cutoff_date=cutoff,
            raw_features=raw,
            standardized_features=standardized,
            capability=capability,
            metrics={
                "cutoff_date": token,
                "standardization_refit": False,
                "accessed_2023": True,
                "model_scoring": False,
            },
        )
        attached, metrics = attach_contact_value_features_to_future_contacts(future, snapshot)
        paired = attached.filter(pl.col("contact_value_residual_applies"))
        if paired.is_empty():
            raise RuntimeError(f"no richer-eligible confirmation target rows at {token}")
        if attached.height != future.height:
            raise RuntimeError(f"confirmation feature attachment changed target coverage at {token}")
        if paired.filter(
            pl.col("z_mean_exit_velocity").is_null()
            | ~pl.col("z_mean_exit_velocity").is_finite()
            | pl.col("z_sweet_spot_share").is_null()
            | ~pl.col("z_sweet_spot_share").is_finite()
        ).height:
            raise RuntimeError(f"confirmation paired features are invalid at {token}")

        raw.write_parquet(table_dir / f"raw_features_{token}.parquet", compression="zstd")
        standardized.write_parquet(
            table_dir / f"standardized_features_{token}.parquet", compression="zstd"
        )
        capability.write_parquet(
            table_dir / f"tracking_capability_{token}.parquet", compression="zstd"
        )
        attached_storage = write_canonical_parquet(
            attached,
            table_dir / f"attached_future_contacts_{token}.parquet",
            table_name=f"current_talent_contact_value_confirmation_attached_{token}",
        ).as_record()
        paired_storage = write_canonical_parquet(
            paired,
            table_dir / f"paired_future_contacts_{token}.parquet",
            table_name=f"current_talent_contact_value_confirmation_paired_{token}",
        ).as_record()

        fold_reports.append(
            {
                "cutoff_date": token,
                "raw_feature_player_count": int(raw.height),
                "eligible_feature_player_count": int(
                    standardized.filter(
                        pl.col("tracked_bbe_eligible")
                        & pl.col("z_mean_exit_velocity").is_not_null()
                        & pl.col("z_sweet_spot_share").is_not_null()
                    ).height
                ),
                "latest_feature_event_date": raw.get_column("last_tracked_bbe_date").max().isoformat(),
                **metrics,
                "attached_storage": attached_storage,
                "paired_storage": paired_storage,
            }
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_confirmation_features_pre_scoring",
        "confirmation_cutoffs": [cutoff.isoformat() for cutoff in CONFIRMATION_CUTOFFS],
        "frozen_standardization": {
            "mean_exit_velocity": standardization.mean_exit_velocity,
            "scale_exit_velocity": standardization.scale_exit_velocity,
            "mean_sweet_spot_share": standardization.mean_sweet_spot_share,
            "scale_sweet_spot_share": standardization.scale_sweet_spot_share,
            "fitted_player_snapshot_count": standardization.fitted_player_count,
        },
        "frozen_residual_fit": refit_report["residual_fit"],
        "tracking_years": [2021, 2022, 2023],
        "tracking_row_count": int(tracking.height),
        "folds": fold_reports,
        "boundary": {
            "2023_tracking_evidence_accessed": True,
            "2023_target_evidence_accessed": True,
            "standardization_refit": False,
            "richer_coefficients_refit": False,
            "richer_predictions_computed": False,
            "confirmation_losses_computed": False,
            "calibration_computed": False,
            "confirmation_decision_computed": False,
            "model_scoring": False,
            "network_requests_performed": False,
        },
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
