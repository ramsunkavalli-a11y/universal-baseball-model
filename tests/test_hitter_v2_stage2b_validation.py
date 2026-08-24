import polars as pl
import pytest

from universal_baseball.hitter_v2_stage2b_validation import (
    calibration_distance,
    calibration_improvement_gate,
    pooled_prediction_gate,
    pooled_woba_calibration,
    proper_score_gate,
    richer_ablation_gate,
    supported_level_reversal_gate,
)


def _metrics(**updates: float) -> dict[str, float]:
    values = {
        "terminal_log_loss": 1.0,
        "terminal_brier_score": 0.7,
        "woba_rmse": 0.04,
        "runs_per_600_rmse": 20.0,
        "woba_calibration_intercept": 0.002,
        "woba_calibration_slope": 0.95,
    }
    values.update(updates)
    return values


def test_proper_score_gate_requires_both_metrics_to_strictly_improve() -> None:
    b0 = _metrics()
    b1 = _metrics(terminal_log_loss=1.01, terminal_brier_score=0.69)
    candidate = _metrics(terminal_log_loss=0.99, terminal_brier_score=0.695)

    gate = proper_score_gate(candidate, b0, b1)
    assert gate["pass"] is False
    assert gate["comparisons"]["terminal_log_loss"]["baseline_id"] == "B0_ONE_YEAR_EB"
    assert gate["comparisons"]["terminal_brier_score"]["baseline_id"] == "B1_MARCEL_345_K1200"


def test_pooled_gate_requires_rate_rmse_as_well_as_proper_scores() -> None:
    baseline = _metrics()
    candidate = _metrics(
        terminal_log_loss=0.99,
        terminal_brier_score=0.69,
        woba_rmse=0.041,
        runs_per_600_rmse=19.0,
    )

    assert pooled_prediction_gate(candidate, baseline, baseline)["pass"] is False


def test_calibration_distance_and_gate_use_both_views() -> None:
    ideal = _metrics(woba_calibration_intercept=0.0, woba_calibration_slope=1.0)
    c0 = _metrics(woba_calibration_intercept=0.003, woba_calibration_slope=0.90)

    assert calibration_distance(ideal) == pytest.approx(0.0)
    assert calibration_improvement_gate(
        {"player": ideal, "pa": ideal}, {"player": c0, "pa": c0}
    )["pass"] is True


def test_pooled_calibration_recovers_known_line() -> None:
    surface = pl.DataFrame(
        {
            "predicted_woba": [0.25, 0.30, 0.35, 0.40],
            "actual_woba": [0.225, 0.275, 0.325, 0.375],
            "hitter_talent_pa": [100, 200, 300, 400],
        }
    )

    result = pooled_woba_calibration(surface, weighting="pa")
    assert result["woba_calibration_intercept"] == pytest.approx(-0.025)
    assert result["woba_calibration_slope"] == pytest.approx(1.0)


def test_supported_level_reversal_uses_joint_materiality_thresholds() -> None:
    baseline = _metrics()
    only_woba_worse = _metrics(woba_rmse=0.043, runs_per_600_rmse=20.4)
    both_rate_worse = _metrics(woba_rmse=0.043, runs_per_600_rmse=20.6)

    assert supported_level_reversal_gate(only_woba_worse, baseline, baseline)["pass"] is True
    assert supported_level_reversal_gate(both_rate_worse, baseline, baseline)["pass"] is False


def test_richer_ablation_requires_both_views_and_limits_rmse_worsening() -> None:
    d0 = {"player": _metrics(), "pa": _metrics()}
    richer = {
        "player": _metrics(
            terminal_log_loss=0.99,
            terminal_brier_score=0.69,
            woba_rmse=0.04005,
        ),
        "pa": _metrics(
            terminal_log_loss=0.99,
            terminal_brier_score=0.69,
            woba_rmse=0.04005,
        ),
    }

    assert richer_ablation_gate(richer, d0)["pass"] is True
    richer["pa"]["woba_rmse"] = 0.0402
    assert richer_ablation_gate(richer, d0)["pass"] is False
