from __future__ import annotations

import pytest

from universal_baseball.player_value_mlb_run_environment import (
    count_completed_regular_season_games,
    innings_pitched_to_outs,
)


def test_baseball_innings_notation_parses_to_outs() -> None:
    assert innings_pitched_to_outs("0.0") == 0
    assert innings_pitched_to_outs("1.0") == 3
    assert innings_pitched_to_outs("12.1") == 37
    assert innings_pitched_to_outs("12.2") == 38


@pytest.mark.parametrize("value", ["1.3", "-1.0", "", None])
def test_invalid_baseball_innings_notation_is_rejected(value: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        innings_pitched_to_outs(value)


def test_completed_regular_season_games_counts_only_regular_final_games() -> None:
    payload = {
        "dates": [
            {
                "games": [
                    {"gameType": "R", "status": {"abstractGameState": "Final"}},
                    {"gameType": "R", "status": {"abstractGameState": "Final"}},
                    {"gameType": "S", "status": {"abstractGameState": "Final"}},
                ]
            }
        ]
    }
    assert count_completed_regular_season_games(payload) == 2


def test_incomplete_regular_season_schedule_is_rejected() -> None:
    payload = {
        "dates": [
            {
                "games": [
                    {"gameType": "R", "status": {"abstractGameState": "Final"}},
                    {"gameType": "R", "status": {"abstractGameState": "Preview"}},
                ]
            }
        ]
    }
    with pytest.raises(RuntimeError, match="not complete"):
        count_completed_regular_season_games(payload)


def test_schedule_without_regular_season_games_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="no regular-season games"):
        count_completed_regular_season_games({"dates": []})
