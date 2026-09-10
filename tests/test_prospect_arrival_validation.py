import numpy as np
import pytest

from universal_baseball.prospect_arrival_validation import (
    ForecastExperimentProtocol,
    calibration_diagnostics,
    common_cohort_fingerprint,
    common_continuous_cohort_fingerprint,
    completed_evaluation_years,
    continuous_promotion_gate,
    continuous_scores,
    paired_bootstrap_difference,
    paired_continuous_bootstrap_difference,
    promotion_gate,
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


def test_experiment_protocol_freezes_family_and_observable_chronology() -> None:
    protocol = ForecastExperimentProtocol(
        name="arrival-angle-search",
        target="two-year MLB arrival",
        player_universe="all pre-MLB affiliated players",
        horizon=2,
        incumbent_id="core",
        candidate_ids=("core", "hand", "origin"),
        selection_origins=(2018, 2021),
        outer_origin=2023,
        outcome_available_through=2025,
    )
    assert protocol.as_dict()["candidate_count"] == 3
    assert len(protocol.fingerprint) == 64

    with pytest.raises(ValueError, match="fully observable"):
        ForecastExperimentProtocol(
            name="leaky",
            target="arrival",
            player_universe="prospects",
            horizon=3,
            incumbent_id="core",
            candidate_ids=("core",),
            selection_origins=(2021,),
            outer_origin=2023,
            outcome_available_through=2025,
        ).validate()


def test_common_cohort_fingerprint_rejects_row_mismatch_and_duplicates() -> None:
    ids = np.array([11, 12, 13])
    observed = np.array([0.0, 1.0, 0.0])
    predictions = {
        "core": np.array([0.1, 0.6, 0.2]),
        "candidate": np.array([0.2, 0.7, 0.1]),
    }
    assert len(common_cohort_fingerprint(ids, observed, predictions)) == 64
    with pytest.raises(ValueError, match="common evaluation cohort"):
        common_cohort_fingerprint(
            ids, observed, {"candidate": np.array([0.2, 0.7])}
        )
    with pytest.raises(ValueError, match="unique"):
        common_cohort_fingerprint(
            np.array([11, 11, 13]), observed, predictions
        )


def test_promotion_requires_both_scores_and_fresh_supported_confirmation() -> None:
    favorable = {
        "log_loss": {"difference": -0.01, "ci_high": -0.001},
        "brier": {"difference": -0.005, "ci_high": -0.0001},
    }
    assert promotion_gate(
        favorable,
        calibration_review_passed=True,
        subgroup_review_passed=True,
        fresh_confirmation=True,
    )["promote"]
    held = promotion_gate(
        favorable,
        calibration_review_passed=True,
        subgroup_review_passed=True,
        fresh_confirmation=False,
    )
    assert not held["promote"]
    assert held["reasons"] == ["fresh confirmation is still required"]


def test_continuous_guardrails_reward_better_common_cohort_forecast() -> None:
    ids = np.arange(200)
    observed = np.tile(np.array([0.0, 1.0, 2.0, 3.0]), 50)
    incumbent = observed + np.tile(np.array([1.0, -1.0]), 100)
    candidate = observed + np.tile(np.array([0.25, -0.25]), 100)
    fingerprint = common_continuous_cohort_fingerprint(
        ids,
        observed,
        {"incumbent": incumbent, "candidate": candidate},
    )
    assert len(fingerprint) == 64
    incumbent_scores = continuous_scores(observed, incumbent)
    candidate_scores = continuous_scores(observed, candidate)
    paired = paired_continuous_bootstrap_difference(
        observed, incumbent, candidate, resamples=200, seed=9
    )
    assert paired["mse"]["ci_high"] < 0
    assert paired["mae"]["ci_high"] < 0
    assert continuous_promotion_gate(
        incumbent_scores,
        candidate_scores,
        paired,
        subgroup_review_passed=True,
        fresh_confirmation=True,
    )["promote"]


def test_continuous_gate_rejects_bias_damage_and_missing_confirmation() -> None:
    incumbent = {"bias": 0.05}
    candidate = {"bias": 0.10}
    paired = {
        "mse": {"difference": -0.1, "ci_high": -0.01},
        "mae": {"difference": -0.1, "ci_high": -0.01},
    }
    result = continuous_promotion_gate(
        incumbent,
        candidate,
        paired,
        subgroup_review_passed=True,
        fresh_confirmation=False,
    )
    assert not result["promote"]
    assert "absolute forecast bias worsened" in result["reasons"]
    assert "fresh confirmation is still required" in result["reasons"]
