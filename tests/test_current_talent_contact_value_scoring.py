from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_contact_value_scoring import (
    fit_contact_value_calibration,
    score_contact_value_fold,
    score_contact_value_pair,
)


def _surface() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "terminal_value": [0.0, 1.0, 2.0, 3.0],
            "comparator_contact_value_prediction": [0.0, 0.8, 1.8, 2.8],
            "richer_contact_value_prediction": [0.0, 1.0, 2.0, 3.0],
        }
    )


def test_pair_scores_event_weighted_losses() -> None:
    metrics = score_contact_value_pair(_surface())
    assert metrics["event_count"] == 4
    assert metrics["baseline_mse"] == pytest.approx(0.03)
    assert metrics["richer_mse"] == pytest.approx(0.0)
    assert metrics["mse_delta_richer_minus_baseline"] == pytest.approx(-0.03)
    assert metrics["richer_mse_win"] is True
    assert metrics["baseline_mae"] == pytest.approx(0.15)
    assert metrics["richer_mae"] == pytest.approx(0.0)


def test_calibration_recovers_identity_for_perfect_predictions() -> None:
    fitted = fit_contact_value_calibration(
        _surface(), prediction_column="richer_contact_value_prediction"
    )
    assert fitted["intercept"] == pytest.approx(0.0)
    assert fitted["slope"] == pytest.approx(1.0)
    assert fitted["absolute_intercept_error"] == pytest.approx(0.0)
    assert fitted["absolute_slope_error"] == pytest.approx(0.0)


def test_fold_scores_both_calibrations() -> None:
    result = score_contact_value_fold(_surface())
    assert result["event_count"] == 4
    assert result["baseline_calibration"]["event_count"] == 4
    assert result["richer_calibration"]["event_count"] == 4


def test_calibration_fails_closed_on_zero_prediction_variance() -> None:
    frame = pl.DataFrame(
        {
            "terminal_value": [0.0, 1.0, 2.0],
            "constant_prediction": [0.5, 0.5, 0.5],
        }
    )
    with pytest.raises(ValueError, match="variance is not identifiable"):
        fit_contact_value_calibration(frame, prediction_column="constant_prediction")


def test_pair_scoring_rejects_nonfinite_values() -> None:
    frame = _surface().with_columns(
        pl.when(pl.arange(0, pl.len()) == 0)
        .then(pl.lit(float("nan")))
        .otherwise(pl.col("richer_contact_value_prediction"))
        .alias("richer_contact_value_prediction")
    )
    with pytest.raises(ValueError, match="invalid values"):
        score_contact_value_pair(frame)
