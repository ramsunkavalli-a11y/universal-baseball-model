from pathlib import Path
import sys

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from render_current_talent_batted_ball_development_checkpoint import (  # noqa: E402
    render_checkpoint,
)


def _report(*, eligible: bool) -> dict[str, object]:
    checks = {
        "lower_equal_fold_mean_log_loss": eligible,
        "no_worse_equal_fold_mean_brier": True,
        "log_loss_wins_at_least_2_of_3": True,
        "identical_scored_coverage": True,
        "non_mlb_evidence_cohort_supported_and_improves_log_loss": True,
        "no_meaningful_non_mlb_capability_tier_worse_on_both_in_2_folds": True,
        "all_component_calibration_fits_converged": True,
        "calibration_intercept_within_25pct_guardrail": True,
        "calibration_slope_within_25pct_guardrail": True,
    }
    return {
        "gate": "current_talent_batted_ball_quality_2022_development",
        "confirmation_data_present": False,
        "training_cutoff": "2021-07-15",
        "development_cutoffs": ["2022-07-15", "2022-08-01", "2022-09-01"],
        "comparator": "translated_multiseason_recency_empirical_bayes_v1",
        "challenger": "baseline2_plus_ev_sweet_spot_contact_residual_v1",
        "tracked_bbe_definition": "result_producing_type_X_terminal_event_complete_EV_LA_non_bunt_pitch_grain",
        "primary_min_complete_tracked_bbe": 20,
        "fixed_l2_penalty": 0.01,
        "eligible_for_fixed_2023_confirmation": eligible,
        "proper_score_summary": {
            "baseline2_equal_fold_mean_log_loss": 2.25,
            "richer_equal_fold_mean_log_loss": 2.24 if eligible else 2.26,
            "richer_minus_baseline2_equal_fold_mean_log_loss": -0.01 if eligible else 0.01,
            "baseline2_equal_fold_mean_brier": 0.87,
            "richer_equal_fold_mean_brier": 0.869,
            "richer_minus_baseline2_equal_fold_mean_brier": -0.001,
            "richer_log_loss_fold_wins": 3,
        },
        "calibration_summary": {
            "baseline2_mean_abs_intercept_error": 0.30,
            "richer_mean_abs_intercept_error": 0.29,
            "baseline2_mean_abs_slope_error": 0.12,
            "richer_mean_abs_slope_error": 0.11,
        },
        "non_mlb_transport": {
            "combined_any_milb_evidence_future_core_events": 5000,
            "combined_any_milb_evidence_equal_fold_mean_log_loss_delta": -0.005,
            "combined_any_milb_evidence_supported_and_improves": True,
            "failed_capability_tiers": [],
        },
        "promotion_checks": checks,
        "residual_fit_metrics": {
            "training_player_count": 100,
            "training_future_contact_events": 10000,
            "initial_mean_contact_log_loss": 2.0,
            "final_mean_contact_log_loss": 1.9,
            "iterations": 20,
            "converged": True,
        },
    }


def test_renderer_marks_pass_without_authorizing_reselection() -> None:
    markdown, result = render_checkpoint(_report(eligible=True), report_sha256="abc")

    assert "DEVELOPMENT PASSED" in markdown
    assert "No feature, BBE, threshold, penalty, date, or model-form search is authorized" in markdown
    assert result["eligible_for_fixed_2023_confirmation"] is True
    assert result["confirmation_data_present"] is False
    assert result["source_report_sha256"] == "abc"


def test_renderer_marks_failure_and_retains_b2() -> None:
    markdown, result = render_checkpoint(_report(eligible=False), report_sha256="def")

    assert "DEVELOPMENT FAILED" in markdown
    assert "Retain Baseline 2" in markdown
    assert result["eligible_for_fixed_2023_confirmation"] is False


def test_renderer_rejects_confirmation_contamination() -> None:
    report = _report(eligible=True)
    report["confirmation_data_present"] = True

    with pytest.raises(ValueError, match="cannot contain confirmation data"):
        render_checkpoint(report, report_sha256="abc")
