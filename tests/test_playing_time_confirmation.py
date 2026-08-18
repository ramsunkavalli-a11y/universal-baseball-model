from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.playing_time_confirmation import (
    confirmation_decision,
    load_frozen_playing_time_fit,
)
from universal_baseball.playing_time_model import (
    PT_FORM_B0,
    PT_FORM_C,
    playing_time_continuous_features,
    playing_time_feature_names,
)


def _coefficients(form: str, *, alpha: float = 0.7) -> pl.DataFrame:
    features = playing_time_feature_names(form)
    rows = [
        {"component": "participation_logit", "feature": "intercept", "coefficient": -1.0}
    ]
    rows.extend(
        {
            "component": "participation_logit",
            "feature": feature,
            "coefficient": 0.01 * (index + 1),
        }
        for index, feature in enumerate(features)
    )
    rows.extend(
        {
            "component": "positive_truncated_nb2",
            "feature": feature,
            "coefficient": 0.02 * index,
        }
        for index, feature in enumerate(("intercept", *features))
    )
    rows.append(
        {
            "component": "positive_truncated_nb2",
            "feature": "alpha",
            "coefficient": alpha,
        }
    )
    return pl.DataFrame(rows)


def _standardization(form: str) -> pl.DataFrame:
    continuous = playing_time_continuous_features(form)
    if not continuous:
        return pl.DataFrame()
    return pl.DataFrame(
        [
            {"feature": feature, "mean": float(index), "scale": 1.0 + index}
            for index, feature in enumerate(continuous)
        ]
    )


def test_load_frozen_fit_reconstructs_exact_form_without_fitting() -> None:
    fit = load_frozen_playing_time_fit(
        _coefficients(PT_FORM_C),
        _standardization(PT_FORM_C),
        form=PT_FORM_C,
        expected_nb_alpha=0.7,
        participation_training_players=12727,
        positive_training_players=2000,
    )
    assert fit.form == PT_FORM_C
    assert fit.feature_names == playing_time_feature_names(PT_FORM_C)
    assert fit.continuous_features == playing_time_continuous_features(PT_FORM_C)
    assert fit.nb_alpha == pytest.approx(0.7)
    assert fit.metrics["loaded_from_frozen_pre_2025_parameters"] is True
    assert fit.metrics["model_refit"] is False


def test_load_frozen_b0_accepts_empty_standardization() -> None:
    fit = load_frozen_playing_time_fit(
        _coefficients(PT_FORM_B0, alpha=0.8),
        pl.DataFrame(),
        form=PT_FORM_B0,
        expected_nb_alpha=0.8,
        participation_training_players=12727,
        positive_training_players=2000,
    )
    assert fit.continuous_features == ()
    assert fit.standardization.means == {}
    assert fit.standardization.scales == {}


def test_load_frozen_fit_rejects_alpha_drift() -> None:
    with pytest.raises(ValueError, match="differs from binding refit"):
        load_frozen_playing_time_fit(
            _coefficients(PT_FORM_C, alpha=0.71),
            _standardization(PT_FORM_C),
            form=PT_FORM_C,
            expected_nb_alpha=0.70,
            participation_training_players=12727,
            positive_training_players=2000,
        )


def _metrics(*, full_nll: float, participation: float, positive: float, mae: float) -> dict[str, float]:
    return {
        "mean_full_negative_log_likelihood": full_nll,
        "participation_log_loss": participation,
        "positive_count_negative_log_likelihood": positive,
        "unconditional_mlb_pa_mae": mae,
    }


def _calibration() -> dict[str, object]:
    return {
        "identifiable": True,
        "converged": True,
        "finite_parameters": True,
        "intercept": 0.0,
        "slope": 1.0,
    }


def test_confirmation_requires_every_frozen_gate() -> None:
    baseline = _metrics(full_nll=1.20, participation=0.30, positive=5.0, mae=40.0)
    candidate = _metrics(full_nll=1.10, participation=0.28, positive=4.9, mae=40.5)
    result = confirmation_decision(
        baseline,
        candidate,
        baseline_calibration=_calibration(),
        candidate_calibration=_calibration(),
        coverage_identical=True,
    )
    assert result["confirmed"] is True
    assert all(result["gates"].values())

    candidate_primary_fail = dict(candidate)
    candidate_primary_fail["mean_full_negative_log_likelihood"] = 1.20
    failed = confirmation_decision(
        baseline,
        candidate_primary_fail,
        baseline_calibration=_calibration(),
        candidate_calibration=_calibration(),
        coverage_identical=True,
    )
    assert failed["confirmed"] is False
    assert failed["gates"]["candidate_full_nll_strictly_lower_than_b0"] is False


def test_confirmation_fails_when_mae_is_more_than_two_percent_worse() -> None:
    baseline = _metrics(full_nll=1.20, participation=0.30, positive=5.0, mae=40.0)
    candidate = _metrics(full_nll=1.10, participation=0.28, positive=4.9, mae=40.81)
    result = confirmation_decision(
        baseline,
        candidate,
        baseline_calibration=_calibration(),
        candidate_calibration=_calibration(),
        coverage_identical=True,
    )
    assert result["confirmed"] is False
    assert result["gates"]["candidate_unconditional_pa_mae_within_2pct_of_b0"] is False
