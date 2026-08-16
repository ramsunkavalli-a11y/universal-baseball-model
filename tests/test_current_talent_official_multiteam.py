import pytest

from universal_baseball.current_talent_official_outcomes import (
    project_official_hitting_game_log,
)


def _split(*, team_id: int, pa: int, ab: int, bb: int = 0) -> dict:
    return {
        "date": "2021-07-11",
        "gameType": "R",
        "game": {"gamePk": 648832},
        "league": {"id": 123},
        "team": {"id": team_id},
        "sport": {"id": 14},
        "stat": {
            "plateAppearances": pa,
            "atBats": ab,
            "baseOnBalls": bb,
            "hitByPitch": 0,
            "strikeOuts": 0,
            "sacFlies": 0,
            "sacBunts": 0,
            "catchersInterference": 0,
        },
    }


def test_projection_collapses_distinct_team_splits_for_same_official_game() -> None:
    payload = {
        "stats": [
            {
                "splits": [
                    _split(team_id=566, pa=5, ab=3, bb=2),
                    _split(team_id=3390, pa=1, ab=1),
                ]
            }
        ]
    }

    result = project_official_hitting_game_log(
        payload,
        player_id=670868,
        sport_id=14,
    )

    assert result.height == 1
    row = result.row(0, named=True)
    assert row["game_id"] == 648832
    assert row["league_id"] == 123
    assert row["team_id"] is None
    assert row["batting_PA"] == 6
    assert row["batting_AB"] == 4
    assert row["batting_BB"] == 2


def test_projection_keeps_same_team_duplicates_fail_closed() -> None:
    payload = {
        "stats": [
            {
                "splits": [
                    _split(team_id=566, pa=5, ab=3, bb=2),
                    _split(team_id=566, pa=1, ab=1),
                ]
            }
        ]
    }

    with pytest.raises(ValueError, match="not distinct-team splits"):
        project_official_hitting_game_log(
            payload,
            player_id=670868,
            sport_id=14,
        )
