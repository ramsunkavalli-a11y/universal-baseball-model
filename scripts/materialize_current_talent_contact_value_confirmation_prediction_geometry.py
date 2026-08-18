#!/usr/bin/env python3
"""Apply frozen Challenger-2 confirmation fits to 2023 paired surfaces without scoring."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_contact_value import (
    ContactValueBaselineFit,
    ContactValueResidualFit,
)
from universal_baseball.current_talent_contact_value_prediction import (
    materialize_contact_value_prediction_geometry,
)
from universal_baseball.storage import write_canonical_parquet


CONFIRMATION_CUTOFFS = (
    date(2023, 7, 15),
    date(2023, 8, 1),
    date(2023, 9, 1),
)
EXPECTED_PAIRED_COUNTS = {
    "2023-07-15": 118984,
    "2023-08-01": 90949,
    "2023-09-01": 40885,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument("--confirmation-refit", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(
            "reports/generated/current-talent-contact-value-confirmation-prediction-geometry"
        ),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label}, found {len(matches)}")
    return matches[0]


def _baseline_fits(root: Path) -> dict[date, ContactValueBaselineFit]:
    report = json.loads(_one(root, "**/report.json", "confirmation evidence report").read_text())
    if report.get("gate") != "current_talent_contact_value_confirmation_evidence_pre_scoring":
        raise RuntimeError("unexpected confirmation evidence gate")
    boundary = report.get("boundary", {})
    required_false = (
        "richer_features_attached",
        "confirmation_coefficients_changed",
        "future_predictions_computed",
        "confirmation_losses_computed",
        "calibration_computed",
        "confirmation_decision_computed",
        "model_scoring",
        "network_requests_performed",
    )
    if any(boundary.get(field) is not False for field in required_false):
        raise RuntimeError("confirmation evidence crossed pre-scoring boundary")

    output: dict[date, ContactValueBaselineFit] = {}
    for row in report.get("cutoffs", []):
        cutoff = date.fromisoformat(row["cutoff_date"])
        if cutoff not in CONFIRMATION_CUTOFFS:
            continue
        fit = row["baseline_fit"]
        if fit.get("full_rank") is not True or fit.get("cutoff_safe") is not True:
            raise RuntimeError(f"confirmation baseline not accepted at {cutoff}")
        if date.fromisoformat(fit["max_training_event_date"]) >= cutoff:
            raise RuntimeError(f"confirmation baseline leaks cutoff at {cutoff}")
        output[cutoff] = ContactValueBaselineFit(
            cutoff_date=cutoff,
            intercept=float(fit["intercept"]),
            contact_bin_effects={
                str(key): float(value)
                for key, value in fit["contact_bin_effects"].items()
            },
            level_group_effects={
                str(key): float(value)
                for key, value in fit["level_group_effects"].items()
            },
            fitted_event_count=int(fit["fitted_event_count"]),
            parameter_count=int(fit["parameter_count"]),
            fitted_level_groups=tuple(str(value) for value in fit["fitted_level_groups"]),
            max_training_event_date=date.fromisoformat(fit["max_training_event_date"]),
        )
    if set(output) != set(CONFIRMATION_CUTOFFS):
        raise RuntimeError("confirmation evidence lacks all three frozen 2023 baselines")
    return output


def _residual_fit(path: Path) -> ContactValueResidualFit:
    report = json.loads(path.read_text())
    if report.get("gate") != "current_talent_contact_value_confirmation_refit_2021_2022":
        raise RuntimeError("unexpected confirmation refit gate")
    boundary = report.get("boundary", {})
    if boundary.get("accessed_2023") is not False:
        raise RuntimeError("confirmation refit accessed 2023")
    if boundary.get("confirmation_scoring_performed") is not False:
        raise RuntimeError("confirmation refit already scored confirmation")
    row = report["residual_fit"]
    fit = ContactValueResidualFit(
        beta_mean_exit_velocity=float(row["beta_mean_exit_velocity"]),
        beta_sweet_spot_share=float(row["beta_sweet_spot_share"]),
        fitted_player_count=int(row["fitted_player_count"]),
        fitted_future_contact_count=int(row["fitted_future_contact_count"]),
        determinant=float(row["determinant"]),
    )
    if fit.determinant <= 0:
        raise RuntimeError("frozen confirmation residual fit is not full-rank")
    return fit


def _feature_report(root: Path) -> dict[str, object]:
    report = json.loads(_one(root, "**/report.json", "confirmation feature report").read_text())
    if report.get("gate") != "current_talent_contact_value_confirmation_features_pre_scoring":
        raise RuntimeError("unexpected confirmation feature gate")
    boundary = report.get("boundary", {})
    required_false = (
        "standardization_refit",
        "richer_coefficients_refit",
        "richer_predictions_computed",
        "confirmation_losses_computed",
        "calibration_computed",
        "confirmation_decision_computed",
        "model_scoring",
        "network_requests_performed",
    )
    if any(boundary.get(field) is not False for field in required_false):
        raise RuntimeError("confirmation feature artifact crossed pre-scoring boundary")
    return report


def main() -> int:
    args = _parse_args()
    baselines = _baseline_fits(args.evidence_root)
    residual = _residual_fit(args.confirmation_refit)
    feature_report = _feature_report(args.feature_root)

    frozen = feature_report["frozen_residual_fit"]
    if abs(float(frozen["beta_mean_exit_velocity"]) - residual.beta_mean_exit_velocity) > 1e-15:
        raise RuntimeError("feature artifact beta EV differs from frozen confirmation refit")
    if abs(float(frozen["beta_sweet_spot_share"]) - residual.beta_sweet_spot_share) > 1e-15:
        raise RuntimeError("feature artifact beta sweet-spot differs from frozen confirmation refit")

    output_root = args.output_root
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    fold_reports: list[dict[str, object]] = []
    for cutoff in CONFIRMATION_CUTOFFS:
        token = cutoff.isoformat()
        paired_path = _one(
            args.feature_root,
            f"**/paired_future_contacts_{token}.parquet",
            f"paired future contacts {token}",
        )
        paired = pl.read_parquet(paired_path)
        if set(paired.get_column("event_date").dt.year().unique().to_list()) != {2023}:
            raise RuntimeError(f"confirmation geometry surface at {token} contains non-2023 events")
        if paired.height != EXPECTED_PAIRED_COUNTS[token]:
            raise RuntimeError(
                f"confirmation paired count changed at {token}: "
                f"{paired.height} != {EXPECTED_PAIRED_COUNTS[token]}"
            )

        predictions, metrics = materialize_contact_value_prediction_geometry(
            paired,
            baseline_fit=baselines[cutoff],
            residual_fit=residual,
        )
        storage = write_canonical_parquet(
            predictions,
            table_dir / f"prediction_geometry_{token}.parquet",
            table_name=f"current_talent_contact_value_confirmation_prediction_geometry_{token}",
        ).as_record()
        # The shared production helper reports accessed_2023=False because its original
        # development contract predates confirmation.  Record the true confirmation
        # boundary here without changing the shared math helper.
        metrics = dict(metrics)
        metrics["accessed_2023"] = True
        fold_reports.append(
            {
                "cutoff_date": token,
                "baseline_fitted_event_count": baselines[cutoff].fitted_event_count,
                "baseline_max_training_event_date": baselines[cutoff].max_training_event_date.isoformat(),
                **metrics,
                "storage": storage,
            }
        )

    observed_counts = {
        str(row["cutoff_date"]): int(row["paired_event_count"])
        for row in fold_reports
    }
    if observed_counts != EXPECTED_PAIRED_COUNTS:
        raise RuntimeError("confirmation prediction geometry changed paired event counts")

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_confirmation_prediction_geometry_pre_scoring",
        "confirmation_cutoffs": [cutoff.isoformat() for cutoff in CONFIRMATION_CUTOFFS],
        "residual_fit": {
            "beta_mean_exit_velocity": residual.beta_mean_exit_velocity,
            "beta_sweet_spot_share": residual.beta_sweet_spot_share,
            "fitted_player_count": residual.fitted_player_count,
            "fitted_future_contact_count": residual.fitted_future_contact_count,
            "determinant": residual.determinant,
        },
        "folds": fold_reports,
        "boundary": {
            "2023_evidence_accessed": True,
            "network_requests_performed": False,
            "residual_coefficients_refit": False,
            "comparator_richer_event_keys_identical": True,
            "prediction_values_finite": True,
            "confirmation_losses_computed": False,
            "calibration_computed": False,
            "confirmation_decision_computed": False,
            "model_scoring": False,
        },
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
