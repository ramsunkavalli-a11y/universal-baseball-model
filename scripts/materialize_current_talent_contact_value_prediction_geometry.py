#!/usr/bin/env python3
"""Apply frozen Challenger-2 fits to the three 2022 paired surfaces without scoring.

This gate is deliberately pre-scoring. It consumes only:
- accepted additive baseline fits;
- accepted richer feature/paired-target surfaces;
- the persisted 2021-only residual fit.

It materializes comparator and richer predictions on identical paired event rows,
checks finite/unchanged geometry, and writes no MSE, MAE, calibration, transport
selection, or 2023 evidence.
"""

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


BASELINE_RUN_ID = 32075112279
FEATURE_RUN_ID = 32075892988
DEVELOPMENT_CUTOFFS = (
    date(2022, 7, 15),
    date(2022, 8, 1),
    date(2022, 9, 1),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument("--residual-result", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-prediction-geometry"),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label}, found {len(matches)}")
    return matches[0]


def _baseline_fits(root: Path) -> dict[date, ContactValueBaselineFit]:
    report = json.loads(_one(root, "**/report.json", "baseline report").read_text())
    if report.get("gate") != "current_talent_contact_value_baseline_fit_pre_scoring":
        raise RuntimeError("unexpected baseline gate")
    boundary = report.get("boundary", {})
    if boundary.get("model_scoring") is not False or boundary.get("accessed_2023") is not False:
        raise RuntimeError("baseline artifact crossed pre-scoring boundary")

    output: dict[date, ContactValueBaselineFit] = {}
    for row in report.get("fits", []):
        cutoff = date.fromisoformat(row["cutoff_date"])
        if cutoff not in DEVELOPMENT_CUTOFFS:
            continue
        if row.get("full_rank") is not True or row.get("cutoff_safe") is not True:
            raise RuntimeError(f"baseline fit is not accepted at {cutoff}")
        coefficients = row["coefficients"]
        output[cutoff] = ContactValueBaselineFit(
            cutoff_date=cutoff,
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
    if set(output) != set(DEVELOPMENT_CUTOFFS):
        raise RuntimeError("baseline artifact lacks all three frozen 2022 cutoffs")
    return output


def _residual_fit(path: Path) -> ContactValueResidualFit:
    report = json.loads(path.read_text())
    if report.get("gate") != "current_talent_contact_value_residual_fit_2021_training_only":
        raise RuntimeError("unexpected residual-fit gate")
    boundary = report.get("boundary", {})
    required_false = (
        "2022_future_outcomes_accessed",
        "accessed_2023",
        "calibration_computed",
        "development_losses_computed",
        "model_scoring",
        "network_requests_performed",
    )
    if any(boundary.get(field) is not False for field in required_false):
        raise RuntimeError("residual fit crossed frozen pre-development boundary")
    if boundary.get("coefficient_fit_uses_2021_only") is not True:
        raise RuntimeError("residual fit is not certified 2021-only")
    if int(report.get("training_event_count", 0)) != 69382:
        raise RuntimeError("unexpected frozen residual training event count")
    if int(report.get("training_player_count", 0)) != 621:
        raise RuntimeError("unexpected frozen residual training player count")
    row = report["residual_fit"]
    return ContactValueResidualFit(
        beta_mean_exit_velocity=float(row["beta_mean_exit_velocity"]),
        beta_sweet_spot_share=float(row["beta_sweet_spot_share"]),
        fitted_player_count=int(row["fitted_player_count"]),
        fitted_future_contact_count=int(row["fitted_future_contact_count"]),
        determinant=float(row["determinant"]),
    )


def main() -> int:
    args = _parse_args()
    baselines = _baseline_fits(args.baseline_root)
    residual = _residual_fit(args.residual_result)

    output_root = args.output_root
    table_dir = output_root / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    fold_reports: list[dict[str, object]] = []
    for cutoff in DEVELOPMENT_CUTOFFS:
        token = cutoff.isoformat()
        paired_path = _one(
            args.feature_root,
            f"**/paired_future_contacts_{token}.parquet",
            f"paired future contacts {token}",
        )
        paired = pl.read_parquet(paired_path)
        if paired.is_empty():
            raise RuntimeError(f"empty paired surface at {token}")
        if set(paired.get_column("event_date").dt.year().unique().to_list()) != {2022}:
            raise RuntimeError(f"prediction surface at {token} contains non-2022 events")

        predictions, metrics = materialize_contact_value_prediction_geometry(
            paired,
            baseline_fit=baselines[cutoff],
            residual_fit=residual,
        )
        storage = write_canonical_parquet(
            predictions,
            table_dir / f"prediction_geometry_{token}.parquet",
            table_name=f"current_talent_contact_value_prediction_geometry_{token}",
        ).as_record()
        fold_reports.append(
            {
                "cutoff_date": token,
                "baseline_fitted_event_count": baselines[cutoff].fitted_event_count,
                "baseline_max_training_event_date": baselines[cutoff].max_training_event_date.isoformat(),
                **metrics,
                "storage": storage,
            }
        )

    expected_counts = {
        "2022-07-15": 97004,
        "2022-08-01": 77859,
        "2022-09-01": 37629,
    }
    observed_counts = {
        str(row["cutoff_date"]): int(row["paired_event_count"])
        for row in fold_reports
    }
    if observed_counts != expected_counts:
        raise RuntimeError(
            f"prediction geometry paired counts changed: observed={observed_counts}, expected={expected_counts}"
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_prediction_geometry_pre_scoring",
        "accepted_input_runs": {
            "baseline_fit": BASELINE_RUN_ID,
            "feature_attachment": FEATURE_RUN_ID,
        },
        "residual_fit": {
            "beta_mean_exit_velocity": residual.beta_mean_exit_velocity,
            "beta_sweet_spot_share": residual.beta_sweet_spot_share,
            "fitted_player_count": residual.fitted_player_count,
            "fitted_future_contact_count": residual.fitted_future_contact_count,
            "determinant": residual.determinant,
        },
        "development_cutoffs": [cutoff.isoformat() for cutoff in DEVELOPMENT_CUTOFFS],
        "folds": fold_reports,
        "boundary": {
            "network_requests_performed": False,
            "residual_coefficients_refit": False,
            "comparator_richer_event_keys_identical": True,
            "development_losses_computed": False,
            "calibration_computed": False,
            "promotion_decision_computed": False,
            "model_scoring": False,
            "accessed_2023": False,
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
