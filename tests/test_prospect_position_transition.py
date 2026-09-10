import numpy as np
import pytest

from universal_baseball.prospect_position_transition import (
    POSITION_GROUPS,
    adjust_war_rate_for_position,
    fit_transition_probabilities,
    multiclass_scores,
    position_group,
    predict_transition,
)


def test_position_group_uses_frozen_baseball_roles() -> None:
    assert position_group("C") == "C"
    assert position_group("SS") == "MIDDLE_INFIELD"
    assert position_group("3B") == "CORNER"
    assert position_group("CF") == "OUTFIELD"
    assert position_group("DH") == "OTHER"
    assert position_group("P") is None


def test_transition_fit_shrinks_sparse_rows_and_conserves_probability() -> None:
    origins = ["C", "C", "MIDDLE_INFIELD", "MIDDLE_INFIELD"]
    destinations = ["C", "CORNER", "MIDDLE_INFIELD", "OUTFIELD"]
    marginal, transition, counts = fit_transition_probabilities(
        origins, destinations, prior_weight=10.0
    )

    assert marginal.sum() == pytest.approx(1.0)
    assert np.allclose(transition.sum(axis=1), 1.0)
    assert counts.sum() == 4
    unused = POSITION_GROUPS.index("OTHER")
    assert transition[unused] == pytest.approx(marginal)


def test_multiclass_score_rewards_correct_destination_probability() -> None:
    marginal, transition, _ = fit_transition_probabilities(
        ["C"] * 8 + ["OUTFIELD"] * 8,
        ["C"] * 8 + ["OUTFIELD"] * 8,
        prior_weight=10.0,
    )
    baseline, candidate = predict_transition(
        ["C", "OUTFIELD"], marginal=marginal, transition=transition
    )

    assert multiclass_scores(["C", "OUTFIELD"], candidate)["log_loss"] < (
        multiclass_scores(["C", "OUTFIELD"], baseline)["log_loss"]
    )


def test_position_war_rate_replacement_is_identity_or_exact_run_delta() -> None:
    assert adjust_war_rate_for_position(
        3.0,
        current_position_runs_per_600=12.5,
        expected_position_runs_per_600=12.5,
        runs_per_win=10.0,
    ) == pytest.approx(3.0)
    assert adjust_war_rate_for_position(
        3.0,
        current_position_runs_per_600=12.5,
        expected_position_runs_per_600=2.5,
        runs_per_win=10.0,
    ) == pytest.approx(2.0)
