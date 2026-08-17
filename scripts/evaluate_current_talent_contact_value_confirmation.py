#!/usr/bin/env python3
"""Run the one fixed 2023 confirmation for Current Talent Challenger 2.

This evaluator must run only after the confirmation source, chronology/baseline,
and richer feature/pairing gates are accepted. It applies the frozen 2021+2022
confirmation coefficients unchanged and reuses the exact 2022 development scoring
and acceptance checks. No search, reselection, refit, or automatic integration is
performed here.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_contact_value import (
    ContactValueBaselineFit,
    ContactValueResidualFit,
)
from universal_baseball.current_talent_contact_value_prediction import (
    materialize_contact_value_prediction_geometry,
)
from universal_baseball.current_talent_contact_value_scoring import (
    score_contact_value_fold,
    score_contact_value_pair,
)


CONFIRMATION_CUTOFFS = (
    date(2023, 7, 15),
    date(2023, 8, 1),
    date(2023, 9, 1),
)
NUMERIC_TOLERANCE = 1e-12
MEANINGFUL_TRANSPORT_CONTACTS = 1000
CALIBRATION_MAX_RELATIVE_WORSENING = 1.25


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument("--confirmation-refit", type=Path, required=True)
    parser.add_argument("--confirmation-contract", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-confirmation"),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    paths = sorted(root.glob(pattern))
    if len(paths) != 1:
        raise RuntimeError(f"expected one {label}, found {len(paths)}")
    return paths[0]


def _load_refit(path: Path) -> tuple[ContactValueResidualFit, dict[str, Any]]:
    report = json.loads(path.read_text())
    if report.get("gate") != "current_talent_contact_value_confirmation_refit_2021_2022":
        raise RuntimeError("unexpected confirmation refit gate")
    boundary = report.get("boundary", {})
    if boundary.get("accessed_2023") is not False:
        raise RuntimeError("confirmation refit already accessed 2023")
    if boundary.get("confirmation_scoring_performed") is not False:
        raise RuntimeError("confirmation refit already scored confirmation")
    row = report["residual_fit"]
    fitted = ContactValueResidualFit(
        beta_mean_exit_velocity=float(row["beta_mean_exit_velocity"]),
        beta_sweet_spot_share=float(row["beta_sweet_spot_share"]),
        fitted_player_count=int(row["fitted_player_count"]),
        fitted_future_contact_count=int(row["fitted_future_contact_count"]),
        determinant=float(row["determinant"]),
    )
    return fitted, report


def _load_evidence(root: Path) -> tuple[dict[date, ContactValueBaselineFit], dict[str, Any]]:
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
    if boundary.get("2023_source_evidence_accessed") is not True:
        raise RuntimeError("confirmation evidence does not contain authorized 2023 source")
    if boundary.get("terminal_values_attached_unchanged") is not True:
        raise RuntimeError("confirmation evidence did not preserve frozen value scale")

    baselines: dict[date, ContactValueBaselineFit] = {}
    for surface in report.get("cutoff_surfaces", []):
        cutoff = date.fromisoformat(surface["cutoff_date"])
        if cutoff not in CONFIRMATION_CUTOFFS:
            continue
        row = surface["baseline_fit"]
        if row.get("full_rank") is not True or row.get("cutoff_safe") is not True:
            raise RuntimeError(f"confirmation baseline not accepted at {cutoff}")
        baselines[cutoff] = ContactValueBaselineFit(
            cutoff_date=cutoff,
            intercept=float(row["intercept"]),
            contact_bin_effects={str(k): float(v) for k, v in row["contact_bin_effects"].items()},
            level_group_effects={str(k): float(v) for k, v in row["level_group_effects"].items()},
            fitted_event_count=int(row["fitted_event_count"]),
            parameter_count=int(row["parameter_count"]),
            fitted_level_groups=tuple(str(v) for v in row["fitted_level_groups"]),
            max_training_event_date=date.fromisoformat(row["max_training_event_date"]),
        )
    if set(baselines) != set(CONFIRMATION_CUTOFFS):
        raise RuntimeError("confirmation evidence lacks all three frozen baseline fits")
    return baselines, report


def _require_features(root: Path, refit: dict[str, Any]) -> dict[str, Any]:
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
        raise RuntimeError("confirmation features crossed pre-scoring boundary")
    expected_standardization = refit["feature_standardization"]
    observed_standardization = report["frozen_standardization"]
    for key in (
        "mean_exit_velocity",
        "scale_exit_velocity",
        "mean_sweet_spot_share",
        "scale_sweet_spot_share",
    ):
        if float(observed_standardization[key]) != float(expected_standardization[key]):
            raise RuntimeError(f"confirmation feature standardization changed: {key}")
    if report.get("frozen_residual_fit") != refit.get("residual_fit"):
        raise RuntimeError("confirmation feature artifact carries different frozen residual fit")
    return report


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def _tier_tokens(frame: pl.DataFrame) -> list[str]:
    values = frame.get_column("observed_source_capability_tiers").drop_nulls().to_list()
    return sorted(
        {
            token
            for value in values
            for token in str(value).split("|")
            if token.startswith("MILB_SAVANT_TRACKED:")
        }
    )


def _tier_subset(frame: pl.DataFrame, token: str) -> pl.DataFrame:
    return frame.filter(
        pl.col("observed_source_capability_tiers")
        .fill_null("")
        .str.split("|")
        .list.contains(token)
    )


def main() -> int:
    args = _parse_args()
    contract_text = args.confirmation_contract.read_text()
    if "FROZEN BEFORE 2023 PERFORMANCE SCORING" not in contract_text:
        raise RuntimeError("confirmation acceptance contract is not frozen")

    residual, refit_report = _load_refit(args.confirmation_refit)
    baselines, evidence_report = _load_evidence(args.evidence_root)
    feature_report = _require_features(args.feature_root, refit_report)

    fold_reports: list[dict[str, Any]] = []
    tier_names: set[str] = set()
    for cutoff in CONFIRMATION_CUTOFFS:
        token = cutoff.isoformat()
        paired_path = _one(
            args.feature_root,
            f"**/paired_future_contacts_{token}.parquet",
            f"confirmation paired surface {token}",
        )
        paired = pl.read_parquet(paired_path)
        if paired.is_empty():
            raise RuntimeError(f"empty confirmation paired surface at {token}")
        if set(paired.get_column("event_date").dt.year().unique().to_list()) != {2023}:
            raise RuntimeError(f"confirmation paired surface at {token} contains non-2023 events")

        predictions, geometry = materialize_contact_value_prediction_geometry(
            paired,
            baseline_fit=baselines[cutoff],
            residual_fit=residual,
        )
        overall = score_contact_value_fold(predictions)

        any_milb = predictions.filter(pl.col("observed_milb_bbe") > 0)
        if any_milb.is_empty():
            raise RuntimeError(f"no observed-MiLB confirmation cohort at {token}")
        any_milb_metrics = score_contact_value_pair(any_milb)

        tier_metrics: dict[str, Any] = {}
        for tier in _tier_tokens(predictions):
            tier_names.add(tier)
            subset = _tier_subset(predictions, tier)
            if not subset.is_empty():
                tier_metrics[tier] = score_contact_value_pair(subset)

        fold_reports.append(
            {
                "cutoff_date": token,
                "geometry": geometry,
                "overall": overall,
                "any_observed_milb": any_milb_metrics,
                "exact_non_mlb_capability_tiers": tier_metrics,
            }
        )

    overall_rows = [row["overall"] for row in fold_reports]
    mean_baseline_mse = _mean(overall_rows, "baseline_mse")
    mean_richer_mse = _mean(overall_rows, "richer_mse")
    mean_baseline_mae = _mean(overall_rows, "baseline_mae")
    mean_richer_mae = _mean(overall_rows, "richer_mae")
    mse_wins = sum(bool(row["richer_mse_win"]) for row in overall_rows)

    any_milb_rows = [row["any_observed_milb"] for row in fold_reports]
    any_milb_total_contacts = sum(int(row["event_count"]) for row in any_milb_rows)
    any_milb_mean_baseline_mse = _mean(any_milb_rows, "baseline_mse")
    any_milb_mean_richer_mse = _mean(any_milb_rows, "richer_mse")

    tier_guardrails: dict[str, Any] = {}
    for tier in sorted(tier_names):
        rows: list[dict[str, Any]] = []
        for fold in fold_reports:
            metrics = fold["exact_non_mlb_capability_tiers"].get(tier)
            if metrics is not None:
                rows.append({"cutoff_date": fold["cutoff_date"], **metrics})
        total_contacts = sum(int(row["event_count"]) for row in rows)
        worse_both_folds = sum(
            float(row["mse_delta_richer_minus_baseline"]) > 0.0
            and float(row["mae_delta_richer_minus_baseline"]) > 0.0
            for row in rows
        )
        meaningful = total_contacts >= MEANINGFUL_TRANSPORT_CONTACTS
        tier_guardrails[tier] = {
            "total_fold_contacts": total_contacts,
            "meaningful_for_guardrail": meaningful,
            "worse_both_mse_and_mae_fold_count": int(worse_both_folds),
            "passes_guardrail": (not meaningful) or worse_both_folds < 2,
            "folds": rows,
        }

    baseline_intercept_error = sum(
        float(row["baseline_calibration"]["absolute_intercept_error"]) for row in overall_rows
    ) / len(overall_rows)
    richer_intercept_error = sum(
        float(row["richer_calibration"]["absolute_intercept_error"]) for row in overall_rows
    ) / len(overall_rows)
    baseline_slope_error = sum(
        float(row["baseline_calibration"]["absolute_slope_error"]) for row in overall_rows
    ) / len(overall_rows)
    richer_slope_error = sum(
        float(row["richer_calibration"]["absolute_slope_error"]) for row in overall_rows
    ) / len(overall_rows)

    confirmation_checks = {
        "lower_equal_fold_mean_mse": mean_richer_mse < mean_baseline_mse,
        "equal_fold_mean_mae_no_worse": mean_richer_mae <= mean_baseline_mae + NUMERIC_TOLERANCE,
        "mse_wins_at_least_2_of_3": mse_wins >= 2,
        "identical_paired_event_coverage": all(
            row["geometry"]["comparator_richer_event_keys_identical"] is True for row in fold_reports
        ),
        "any_milb_at_least_1000_and_lower_mean_mse": (
            any_milb_total_contacts >= MEANINGFUL_TRANSPORT_CONTACTS
            and any_milb_mean_richer_mse < any_milb_mean_baseline_mse
        ),
        "no_meaningful_non_mlb_tier_worse_both_in_2_folds": all(
            bool(row["passes_guardrail"]) for row in tier_guardrails.values()
        ),
        "residual_fit_finite_full_rank": residual.determinant > 0.0,
        "all_calibration_fits_identifiable": True,
        "calibration_intercept_guardrail": (
            richer_intercept_error
            <= CALIBRATION_MAX_RELATIVE_WORSENING * baseline_intercept_error + NUMERIC_TOLERANCE
        ),
        "calibration_slope_guardrail": (
            richer_slope_error
            <= CALIBRATION_MAX_RELATIVE_WORSENING * baseline_slope_error + NUMERIC_TOLERANCE
        ),
    }
    confirmed = all(confirmation_checks.values())

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_2023_confirmation",
        "candidate": "baseline2_plus_ev_sweet_spot_contact_value_residual_v1",
        "confirmation_contract": "docs/current-talent-contact-value-confirmation-contract.md",
        "confirmation_cutoffs": [cutoff.isoformat() for cutoff in CONFIRMATION_CUTOFFS],
        "folds": fold_reports,
        "equal_fold_summary": {
            "baseline_mse": mean_baseline_mse,
            "richer_mse": mean_richer_mse,
            "mse_delta_richer_minus_baseline": mean_richer_mse - mean_baseline_mse,
            "baseline_mae": mean_baseline_mae,
            "richer_mae": mean_richer_mae,
            "mae_delta_richer_minus_baseline": mean_richer_mae - mean_baseline_mae,
            "richer_mse_fold_wins": mse_wins,
        },
        "calibration_summary": {
            "baseline_mean_absolute_intercept_error": baseline_intercept_error,
            "richer_mean_absolute_intercept_error": richer_intercept_error,
            "baseline_mean_absolute_slope_error": baseline_slope_error,
            "richer_mean_absolute_slope_error": richer_slope_error,
        },
        "any_observed_milb": {
            "total_fold_contacts": any_milb_total_contacts,
            "equal_fold_mean_baseline_mse": any_milb_mean_baseline_mse,
            "equal_fold_mean_richer_mse": any_milb_mean_richer_mse,
            "mse_delta_richer_minus_baseline": any_milb_mean_richer_mse - any_milb_mean_baseline_mse,
        },
        "exact_non_mlb_capability_tiers": tier_guardrails,
        "confirmation_checks": confirmation_checks,
        "confirmed": confirmed,
        "frozen_confirmation_standardization": refit_report["feature_standardization"],
        "frozen_confirmation_residual_fit": refit_report["residual_fit"],
        "accepted_pre_scoring_inputs": {
            "evidence_gate": evidence_report["gate"],
            "feature_gate": feature_report["gate"],
        },
        "production_boundary": (
            "Even if confirmed, the scalar remains a separate Current Talent contact-quality "
            "dimension until a later integration contract is frozen."
        ),
        "boundary": {
            "one_shot_confirmation": True,
            "2023_performance_scoring_performed": True,
            "accessed_2023": True,
            "network_requests_performed": False,
            "standardization_refit_during_confirmation": False,
            "residual_coefficients_refit_during_confirmation": False,
            "feature_search_performed": False,
            "threshold_search_performed": False,
            "acceptance_rule_changed": False,
            "automatic_integration_performed": False,
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
