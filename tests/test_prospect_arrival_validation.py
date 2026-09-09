import numpy as np
import pytest

from universal_baseball.prospect_arrival_validation import (
    calibration_diagnostics,
    completed_evaluation_years,
    paired_bootstrap_difference,
    proper_scores,
    select_nested_candidate,
)


def test_completed_evaluation_years_enforces_outcome_embargo() -> None:
    assert completed_evaluation_years(
        outer_year=2023, horizon=2, evaluation_years=(2021, 2022, 2023)
    ) == (2021,)


def test_nested_selection_uses_only_completed_years_and_brier_guardrail() -> None:
    rows = [
        {
            "evaluation_year": year,
            "model_id": model,
            "players": 100,
            "log_loss": log_loss,
            "brier": brier,
        }
        for year, model, log_loss, brier in (
            (2021, "core", 0.20, 0.05),
            (2021, "good", 0.19, 0.049),
            (2021, "bad_brier", 0.18, 0.051),
            (2022, "core", 0.20, 0.05),
            (2022, "good", 0.30, 0.07),
            (2022, "bad_brier", 0.10, 0.04),
        )
    ]
    assert select_nested_candidate(
        rows, eligible_years=(2021,), incumbent_id="core"
    ) == "good"


def test_paired_bootstrap_rewards_better_probabilities_deterministically() -> None:
    observed = np.array([0.0, 0.0, 1.0, 1.0] * 50)
    incumbent = np.full(observed.shape, 0.5)
    candidate = np.where(observed == 1.0, 0.8, 0.2)
    first = paired_bootstrap_difference(
        observed, incumbent, candidate, resamples=200, seed=7
    )
    second = paired_bootstrap_difference(
        observed, incumbent, candidate, resamples=200, seed=7
    )
    assert first == second
    assert first["brier"]["ci_high"] < 0
    assert first["log_loss"]["ci_high"] < 0


def test_proper_scores_reject_bad_probabilities() -> None:
    with pytest.raises(ValueError, match="inside"):
        proper_scores(np.array([0.0, 1.0]), np.array([0.2, 1.1]))


def test_calibration_diagnostics_preserve_every_row_in_bins() -> None:
    observed = np.array([0.0, 1.0] * 11)
    probability = np.linspace(0.05, 0.95, observed.size)
    result = calibration_diagnostics(observed, probability, bins=5)
    assert sum(cell["players"] for cell in result["reliability_bins"]) == 22
    assert result["intercept"] is not None
    assert result["slope"] is not None
