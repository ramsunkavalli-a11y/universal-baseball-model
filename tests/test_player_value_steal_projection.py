from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_steal_projection import (
    PlayerSeasonStealSummary,
    StealCandidate,
    attempt_multiplier,
    confirmation_passes,
    predict_success_probability,
    score_all_candidates,
    select_development_candidate,
    steal_candidates,
    success_log_odds_residual,
)


def _row(
    player_id: int,
    season: int,
    *,
    tier: str = "MLB",
    opportunity_proxy: float = 100.0,
    attempts: float = 10.0,
    successes: float = 8.0,
    expected_attempts: float = 5.0,
    expected_successes: float = 7.5,
) -> PlayerSeasonStealSummary:
    return PlayerSeasonStealSummary(
        player_id=player_id,
        season=season,
        tier=tier,
        opportunity_proxy=opportunity_proxy,
        attempts=attempts,
        successes=successes,
        expected_attempts=expected_attempts,
        expected_successes=expected_successes,
    )


def _candidate(candidate_id: str) -> StealCandidate:
    return next(candidate for candidate in steal_candidates() if candidate.candidate_id == candidate_id)


def test_candidate_grid_is_predeclared_seven_models() -> None:
    assert [candidate.candidate_id for candidate in steal_candidates()] == [
        "B0_neutral",
        "B1_k5",
        "B1_k15",
        "B1_k45",
        "B2_k5",
        "B2_k15",
        "B2_k45",
    ]


def test_attempt_multiplier_uses_environment_expected_attempts_and_shrinkage() -> None:
    target = _row(
        1,
        2023,
        attempts=4.0,
        successes=3.0,
        expected_attempts=4.0,
        expected_successes=3.0,
    )
    history = [_row(1, 2022, attempts=10.0, expected_attempts=5.0)]

    value = attempt_multiplier(target, history, _candidate("B1_k5"))

    assert value == pytest.approx((5.0 + 10.0) / (5.0 + 5.0))


def test_b1_ignores_two_year_old_history_b2_uses_fixed_half_weight() -> None:
    target = _row(1, 2023)
    history = [
        _row(1, 2022, attempts=10.0, expected_attempts=5.0),
        _row(1, 2021, attempts=20.0, expected_attempts=5.0),
    ]

    b1 = attempt_multiplier(target, history, _candidate("B1_k5"))
    b2 = attempt_multiplier(target, history, _candidate("B2_k5"))

    assert b1 == pytest.approx(1.5)
    assert b2 == pytest.approx((5.0 + 10.0 + 0.5 * 20.0) / (5.0 + 5.0 + 0.5 * 5.0))
    assert b2 > b1


def test_missing_player_history_resolves_to_neutral_attempt_multiplier() -> None:
    target = _row(2, 2023)
    history = [_row(1, 2022, attempts=20.0, expected_attempts=5.0)]

    assert attempt_multiplier(target, history, _candidate("B2_k5")) == 1.0


def test_success_zero_attempt_history_resolves_to_target_environment_baseline() -> None:
    target = _row(1, 2023, attempts=10.0, successes=8.0, expected_successes=7.0)
    history = [
        _row(
            1,
            2022,
            attempts=0.0,
            successes=0.0,
            expected_attempts=0.0,
            expected_successes=0.0,
        )
    ]

    assert success_log_odds_residual(target, history, _candidate("B1_k5")) == 0.0
    assert predict_success_probability(target, history, _candidate("B1_k5")) == pytest.approx(0.7)


def test_success_skill_is_carried_as_log_odds_residual_to_new_environment() -> None:
    target = _row(1, 2023, attempts=10.0, successes=8.0, expected_successes=6.0)
    history = [_row(1, 2022, attempts=10.0, successes=9.0, expected_successes=7.5)]

    probability = predict_success_probability(target, history, _candidate("B1_k5"))

    assert probability > 0.6
    assert probability < 1.0


def test_invalid_summary_rejects_successes_above_attempts() -> None:
    with pytest.raises(ValueError, match="successes cannot exceed attempts"):
        _row(1, 2023, attempts=3.0, successes=4.0, expected_successes=2.0)


def test_development_selection_prefers_predictive_player_specific_attempt_model() -> None:
    rows = []
    # Player 1 persistently attempts at twice environment expectation;
    # player 2 persistently attempts at half. This makes carry-forward informative.
    for season in (2021, 2022, 2023, 2024):
        rows.extend(
            [
                _row(
                    1,
                    season,
                    opportunity_proxy=100.0,
                    attempts=10.0,
                    successes=8.0,
                    expected_attempts=5.0,
                    expected_successes=7.5,
                ),
                _row(
                    2,
                    season,
                    opportunity_proxy=100.0,
                    attempts=2.0,
                    successes=1.0,
                    expected_attempts=5.0,
                    expected_successes=1.5,
                ),
            ]
        )

    development_scores = score_all_candidates(
        rows, channel="attempt", target_years=(2022, 2023)
    )
    selection = select_development_candidate(development_scores, channel="attempt")

    assert selection.development_passed is True
    assert selection.selected_candidate_id != "B0_neutral"

    confirmation_scores = score_all_candidates(rows, channel="attempt", target_years=(2024,))
    passes, reversals = confirmation_passes(
        selection.selected_candidate_id, confirmation_scores
    )
    assert passes is True
    assert reversals == tuple()


def test_success_scores_are_finite_for_zero_success_target() -> None:
    rows = [
        _row(1, 2022, attempts=4.0, successes=0.0, expected_successes=3.0),
        _row(1, 2021, attempts=5.0, successes=4.0, expected_successes=3.75),
    ]

    scores = score_all_candidates(rows, channel="success", target_years=(2022,))

    assert all(math.isfinite(score.equal_year_mean_primary) for score in scores)
