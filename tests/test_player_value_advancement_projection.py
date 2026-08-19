from __future__ import annotations

from dataclasses import replace

import pytest

from universal_baseball.player_value_advancement_projection import (
    AdvancementCandidate,
    AdvancementCandidateScore,
    AdvancementScoreCell,
    PlayerSeasonAdvancementSummary,
    advancement_candidates,
    confirmation_passes,
    projected_advancement_rate,
    score_candidate,
    select_development_candidate,
)


def _row(
    player_id: int,
    season: int,
    runs: float,
    opportunities: float,
) -> PlayerSeasonAdvancementSummary:
    return PlayerSeasonAdvancementSummary(
        player_id=player_id,
        season=season,
        runs_xb=runs,
        opportunities_xb=opportunities,
    )


def _candidate(candidate_id: str) -> AdvancementCandidate:
    return next(
        candidate
        for candidate in advancement_candidates()
        if candidate.candidate_id == candidate_id
    )


def _score(candidate_id: str, y2022: float, y2023: float) -> AdvancementCandidateScore:
    return AdvancementCandidateScore(
        candidate_id=candidate_id,
        yearly={
            2022: AdvancementScoreCell(
                score=y2022,
                exposure=100.0,
                observation_count=10,
                weighted_mae=0.1,
                player_rmse=0.1,
                correlation=None,
            ),
            2023: AdvancementScoreCell(
                score=y2023,
                exposure=100.0,
                observation_count=10,
                weighted_mae=0.1,
                player_rmse=0.1,
                correlation=None,
            ),
        },
        equal_year_mean_primary=(y2022 + y2023) / 2,
    )


def test_advancement_candidate_grid_is_frozen() -> None:
    assert [candidate.candidate_id for candidate in advancement_candidates()] == [
        "A0_neutral",
        "A1_k25",
        "A1_k75",
        "A1_k225",
        "A2_k25",
        "A2_k75",
        "A2_k225",
    ]


def test_projected_advancement_rate_uses_only_allowed_prior_history() -> None:
    target = _row(1, 2024, 0.0, 100.0)
    history = [
        _row(1, 2021, 4.0, 100.0),
        _row(1, 2022, 6.0, 100.0),
        _row(1, 2023, 8.0, 100.0),
        _row(1, 2024, 100.0, 100.0),
        _row(2, 2023, 100.0, 100.0),
    ]

    assert projected_advancement_rate(target, history, _candidate("A0_neutral")) == 0.0
    assert projected_advancement_rate(
        target,
        history,
        _candidate("A1_k25"),
    ) == pytest.approx(8.0 / 125.0)
    assert projected_advancement_rate(
        target,
        history,
        _candidate("A2_k25"),
    ) == pytest.approx((8.0 + 0.5 * 6.0 + 0.25 * 4.0) / (25.0 + 175.0))


def test_projected_advancement_rate_is_neutral_without_history() -> None:
    target = _row(1, 2024, 1.0, 50.0)
    history = [_row(2, 2023, 5.0, 100.0)]
    assert projected_advancement_rate(
        target,
        history,
        _candidate("A2_k75"),
    ) == 0.0


def test_score_candidate_keeps_identical_target_coverage_with_missing_history() -> None:
    rows = [
        _row(1, 2021, 4.0, 100.0),
        _row(1, 2022, 5.0, 100.0),
        _row(2, 2022, -1.0, 50.0),
    ]
    score = score_candidate(
        rows,
        _candidate("A1_k25"),
        target_years=(2022,),
    )

    assert score.yearly[2022].observation_count == 2
    assert score.yearly[2022].exposure == 150.0
    assert score.yearly[2022].score >= 0
    assert score.yearly[2022].weighted_mae >= 0


def test_selection_rejects_catastrophic_development_year_reversal() -> None:
    baseline = _score("A0_neutral", 1.0, 1.0)
    bad_2022 = _score("A1_k25", 1.11, 0.1)
    stable = _score("A2_k75", 0.8, 0.8)

    selection = select_development_candidate([baseline, bad_2022, stable])

    assert selection.selected_candidate_id == "A2_k75"
    assert selection.development_passed is True


def test_selection_tie_prefers_a1_then_stronger_shrinkage() -> None:
    baseline = _score("A0_neutral", 1.0, 1.0)
    a1_25 = _score("A1_k25", 0.8, 0.8)
    a1_225 = _score("A1_k225", 0.8, 0.8)
    a2_225 = _score("A2_k225", 0.8, 0.8)

    selection = select_development_candidate(
        [baseline, a1_25, a1_225, a2_225]
    )

    assert selection.selected_candidate_id == "A1_k225"


def test_confirmation_only_compares_preselected_candidate_with_neutral() -> None:
    baseline = AdvancementCandidateScore(
        candidate_id="A0_neutral",
        yearly={
            2024: AdvancementScoreCell(
                score=1.0,
                exposure=100.0,
                observation_count=10,
                weighted_mae=0.1,
                player_rmse=0.1,
                correlation=None,
            )
        },
        equal_year_mean_primary=1.0,
    )
    winner = replace(
        baseline,
        candidate_id="A2_k75",
        yearly={
            2024: replace(baseline.yearly[2024], score=0.9)
        },
        equal_year_mean_primary=0.9,
    )
    loser = replace(
        winner,
        yearly={2024: replace(winner.yearly[2024], score=1.1)},
        equal_year_mean_primary=1.1,
    )

    assert confirmation_passes("A2_k75", [baseline, winner]) is True
    assert confirmation_passes("A2_k75", [baseline, loser]) is False
    assert confirmation_passes("A0_neutral", [baseline]) is True


def test_advancement_summary_rejects_invalid_source_values() -> None:
    with pytest.raises(ValueError, match="positive"):
        _row(0, 2024, 1.0, 10.0)
    with pytest.raises(ValueError, match="nonnegative"):
        _row(1, 2024, 1.0, -1.0)
