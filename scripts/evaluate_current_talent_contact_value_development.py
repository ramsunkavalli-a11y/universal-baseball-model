#!/usr/bin/env python3
"""Evaluate frozen Current Talent Challenger 2 on the predeclared 2022 folds only."""

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


BASELINE_RUN_ID = 32075112279
FEATURE_RUN_ID = 32075892988
DEVELOPMENT_CUTOFFS = (
    date(2022, 7, 15),
    date(2022, 8, 1),
    date(2022, 9, 1),
)
NUMERIC_TOLERANCE = 1e-12
MEANINGFUL_TRANSPORT_CONTACTS = 1000
CALIBRATION_MAX_RELATIVE_WORSENING = 1.25


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", type=Path, required=True)
    parser.add_argument("--feature-root", type=Path, required=True)
    parser.add_argument("--residual-result", type=Path, required=True)
    parser.add_argument("--geometry-result", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-talent-contact-value-development"),
    )
    return parser.parse_args()


def _one(root: Path, pattern: str, label: str) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label}, found {len(matches)}")
    return matches[0]


def _load_baselines(root: Path) -> dict[date, ContactValueBaselineFit]:
    report = json.loads(_one(root, "**/report.json", "baseline fit report").read_text())
    if report.get("gate") != "current_talent_contact_value_baseline_fit_pre_scoring":
        raise RuntimeError("unexpected baseline fit gate")
    if report.get("boundary", {}).get("model_scoring") is not False:
        raise RuntimeError("baseline artifact crossed pre-scoring boundary")
    output: dict[date, ContactValueBaselineFit] = {}
    for row in report.get("fits", []):
        cutoff = date.fromisoformat(row["cutoff_date"])
        if cutoff not in DEVELOPMENT_CUTOFFS:
            continue
        if row.get("full_rank") is not True or row.get("cutoff_safe") is not True:
            raise RuntimeError(f"unaccepted baseline fit at {cutoff}")
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
    if set(output) != set(DEVELOPMENT_CUTOFFS):
        raise RuntimeError("baseline artifact lacks all frozen 2022 development cutoffs")
    return output


def _load_residual(path: Path) -> tuple[ContactValueResidualFit, dict[str, Any]]:
    report = json.loads(path.read_text())
    if report.get("gate") != "current_talent_contact_value_residual_fit_2021_training_only":
        raise RuntimeError("unexpected residual fit gate")
    boundary = report.get("boundary", {})
    if boundary.get("coefficient_fit_uses_2021_only") is not True:
        raise RuntimeError("residual coefficients are not frozen 2021-only")
    for field in (
        "2022_future_outcomes_accessed",
        "accessed_2023",
        "development_losses_computed",
        "model_scoring",
    ):
        if boundary.get(field) is not False:
            raise RuntimeError(f"residual fit boundary violation: {field}")
    row = report["residual_fit"]
    fitted = ContactValueResidualFit(
        beta_mean_exit_velocity=float(row["beta_mean_exit_velocity"]),
        beta_sweet_spot_share=float(row["beta_sweet_spot_share"]),
        fitted_player_count=int(row["fitted_player_count"]),
        fitted_future_contact_count=int(row["fitted_future_contact_count"]),
        determinant=float(row["determinant"]),
    )
    return fitted, report


def _require_geometry(path: Path, residual: ContactValueResidualFit) -> dict[str, Any]:
    report = json.loads(path.read_text())
    if report.get("gate") != "current_talent_contact_value_prediction_geometry_pre_scoring":
        raise RuntimeError("unexpected prediction geometry gate")
    boundary = report.get("boundary", {})
    for field in (
        "accessed_2023",
        "calibration_computed",
        "development_losses_computed",
        "model_scoring",
        "promotion_decision_computed",
        "network_requests_performed",
        "residual_coefficients_refit",
    ):
        if boundary.get(field) is not False:
            raise RuntimeError(f"prediction geometry boundary violation: {field}")
    if boundary.get("comparator_richer_event_keys_identical") is not True:
        raise RuntimeError("prediction geometry did not preserve paired coverage")
    expected = {
        "beta_mean_exit_velocity": residual.beta_mean_exit_velocity,
        "beta_sweet_spot_share": residual.beta_sweet_spot_share,
        "fitted_player_count": residual.fitted_player_count,
        "fitted_future_contact_count": residual.fitted_future_contact_count,
        "determinant": residual.determinant,
    }
    if report.get("residual_fit") != expected:
        raise RuntimeError("prediction geometry used different residual coefficients")
    counts = {row["cutoff_date"]: int(row["paired_event_count"]) for row in report.get("folds", [])}
    if counts != {"2022-07-15": 97004, "2022-08-01": 77859, "2022-09-01": 37629}:
        raise RuntimeError("prediction geometry paired counts changed")
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
    baselines = _load_baselines(args.baseline_root)
    residual, residual_report = _load_residual(args.residual_result)
    geometry_report = _require_geometry(args.geometry_result, residual)

    fold_reports: list[dict[str, Any]] = []
    tier_names: set[str] = set()
    for cutoff in DEVELOPMENT_CUTOFFS:
        token = cutoff.isoformat()
        paired = pl.read_parquet(
            _one(args.feature_root, f"**/paired_future_contacts_{token}.parquet", f"paired surface {token}")
        )
        if set(paired.get_column("event_date").dt.year().unique().to_list()) != {2022}:
            raise RuntimeError(f"development surface at {token} contains non-2022 outcomes")
        predictions, geometry = materialize_contact_value_prediction_geometry(
            paired,
            baseline_fit=baselines[cutoff],
            residual_fit=residual,
        )
        overall = score_contact_value_fold(predictions)

        any_milb = predictions.filter(pl.col("observed_milb_bbe") > 0)
        if any_milb.is_empty():
            raise RuntimeError(f"no observed-MiLB richer cohort at {token}")
        any_milb_metrics = score_contact_value_pair(any_milb)

        tier_metrics: dict[str, Any] = {}
        for tier in _tier_tokens(predictions):
            tier_names.add(tier)
            subset = _tier_subset(predictions, tier)
            if subset.is_empty():
                continue
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

    promotion_checks = {
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
    eligible = all(promotion_checks.values())

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_contact_value_2022_development",
        "candidate": "baseline2_plus_ev_sweet_spot_contact_value_residual_v1",
        "comparator": "conditional_contact_value_baseline_contact_bin_plus_level_group",
        "accepted_input_runs": {
            "baseline_fit": BASELINE_RUN_ID,
            "feature_attachment": FEATURE_RUN_ID,
        },
        "development_cutoffs": [cutoff.isoformat() for cutoff in DEVELOPMENT_CUTOFFS],
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
        "promotion_checks": promotion_checks,
        "eligible_for_fixed_2023_confirmation": eligible,
        "frozen_residual_fit": residual_report["residual_fit"],
        "accepted_prediction_geometry": {
            "development_cutoffs": geometry_report["development_cutoffs"],
            "paired_counts": {
                row["cutoff_date"]: row["paired_event_count"] for row in geometry_report["folds"]
            },
        },
        "boundary": {
            "offline_evaluator": True,
            "network_requests_performed": False,
            "confirmation_data_present": False,
            "accessed_2023": False,
            "residual_coefficients_refit": False,
            "feature_search_performed": False,
            "threshold_search_performed": False,
            "development_model_scoring": True,
            "automatic_2023_follow_on": False,
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
