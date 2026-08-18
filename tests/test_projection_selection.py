from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.projection_ridge import (
    PROJECTION_FORM_AGE,
    PROJECTION_FORM_AGE_LEVEL,
)
from universal_baseball.projection_selection import select_projection_configuration


def _results(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows)


def test_selection_uses_log_loss_then_brier_then_simplicity_then_larger_lambda() -> None:
    baseline_ll = 2.0
    baseline_brier = 0.8
    result = select_projection_configuration(
        _results(
            [
                {
                    "form": PROJECTION_FORM_AGE_LEVEL,
                    "ridge_lambda": 0.1,
                    "candidate_log_loss": 1.900000,
                    "candidate_brier": 0.700000,
                    "baseline0_log_loss": baseline_ll,
                    "baseline0_brier": baseline_brier,
                },
                {
                    "form": PROJECTION_FORM_AGE,
                    "ridge_lambda": 0.1,
                    "candidate_log_loss": 1.900005,
                    "candidate_brier": 0.6999995,
                    "baseline0_log_loss": baseline_ll,
                    "baseline0_brier": baseline_brier,
                },
                {
                    "form": PROJECTION_FORM_AGE,
                    "ridge_lambda": 1.0,
                    "candidate_log_loss": 1.900005,
                    "candidate_brier": 0.7000000,
                    "baseline0_log_loss": baseline_ll,
                    "baseline0_brier": baseline_brier,
                },
            ]
        )
    )
    assert result.selected_form == PROJECTION_FORM_AGE
    assert result.selected_lambda == pytest.approx(1.0)
    assert result.early_reject is False


def test_selection_does_not_let_brier_override_log_loss_beyond_tolerance() -> None:
    result = select_projection_configuration(
        _results(
            [
                {
                    "form": PROJECTION_FORM_AGE,
                    "ridge_lambda": 0.1,
                    "candidate_log_loss": 1.90,
                    "candidate_brier": 0.75,
                    "baseline0_log_loss": 2.0,
                    "baseline0_brier": 0.8,
                },
                {
                    "form": PROJECTION_FORM_AGE_LEVEL,
                    "ridge_lambda": 0.1,
                    "candidate_log_loss": 1.91,
                    "candidate_brier": 0.60,
                    "baseline0_log_loss": 2.0,
                    "baseline0_brier": 0.8,
                },
            ]
        )
    )
    assert result.selected_form == PROJECTION_FORM_AGE


def test_selection_early_rejects_candidate_that_does_not_beat_carry_forward_log_loss() -> None:
    result = select_projection_configuration(
        _results(
            [
                {
                    "form": PROJECTION_FORM_AGE,
                    "ridge_lambda": 1.0,
                    "candidate_log_loss": 2.000001,
                    "candidate_brier": 0.79,
                    "baseline0_log_loss": 2.0,
                    "baseline0_brier": 0.8,
                }
            ]
        )
    )
    assert result.early_reject is True
    assert result.advances_to_out_of_time_validation is False


def test_selection_rejects_baseline_score_drift_across_configs() -> None:
    with pytest.raises(ValueError, match="Baseline 0 log loss differs"):
        select_projection_configuration(
            _results(
                [
                    {
                        "form": PROJECTION_FORM_AGE,
                        "ridge_lambda": 0.1,
                        "candidate_log_loss": 1.9,
                        "candidate_brier": 0.7,
                        "baseline0_log_loss": 2.0,
                        "baseline0_brier": 0.8,
                    },
                    {
                        "form": PROJECTION_FORM_AGE_LEVEL,
                        "ridge_lambda": 0.1,
                        "candidate_log_loss": 1.89,
                        "candidate_brier": 0.7,
                        "baseline0_log_loss": 2.0001,
                        "baseline0_brier": 0.8,
                    },
                ]
            )
        )
