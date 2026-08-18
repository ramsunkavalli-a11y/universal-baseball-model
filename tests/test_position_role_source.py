from __future__ import annotations

import pytest

from universal_baseball.position_role_source import (
    baseball_innings_to_outs,
    project_fielding_usage_splits,
)


def _split(
    *,
    player_id: int = 1,
    team_id: int = 111,
    code: str = "8",
    abbreviation: str = "CF",
    name: str = "Outfielder",
    games: int = 10,
    games_started: int = 8,
    innings: str = "72.2",
) -> dict[str, object]:
    return {
        "season": "2024",
        "player": {"id": player_id, "fullName": "Test Player"},
        "team": {"id": team_id, "name": "Test Team"},
        "position": {
            "code": code,
            "abbreviation": abbreviation,
            "name": name,
            "type": "Hitter",
        },
        "stat": {
            "games": games,
            "gamesPlayed": games,
            "gamesStarted": games_started,
            "innings": innings,
        },
    }


def test_baseball_innings_to_outs_uses_out_not_decimal_semantics() -> None:
    assert baseball_innings_to_outs("0.0") == 0
    assert baseball_innings_to_outs("12.1") == 37
    assert baseball_innings_to_outs("12.2") == 38
    assert baseball_innings_to_outs("13") == 39


def test_baseball_innings_to_outs_rejects_impossible_fraction() -> None:
    with pytest.raises(ValueError, match="fractional-out suffix"):
        baseball_innings_to_outs("12.3")


def test_project_fielding_usage_preserves_explicit_dh_start_role() -> None:
    frame = project_fielding_usage_splits(
        [
            _split(
                code="10",
                abbreviation="DH",
                name="Designated Hitter",
                games=12,
                games_started=9,
                innings="0.0",
            )
        ],
        season=2024,
        league_id=103,
        level_group="MLB",
    )
    row = frame.row(0, named=True)
    assert row["position_abbreviation"] == "DH"
    assert row["games_started"] == 9
    assert row["fielding_outs"] == 0


def test_project_fielding_usage_rejects_games_disagreement() -> None:
    row = _split()
    row["stat"]["gamesPlayed"] = 11  # type: ignore[index]
    with pytest.raises(ValueError, match="games/gamesPlayed mismatch"):
        project_fielding_usage_splits(
            [row], season=2024, league_id=103, level_group="MLB"
        )


def test_project_fielding_usage_rejects_games_started_above_games() -> None:
    with pytest.raises(ValueError, match="gamesStarted exceeds gamesPlayed"):
        project_fielding_usage_splits(
            [_split(games=10, games_started=11)],
            season=2024,
            league_id=103,
            level_group="MLB",
        )


def test_project_fielding_usage_rejects_position_mapping_drift() -> None:
    with pytest.raises(ValueError, match="code/abbreviation mismatch"):
        project_fielding_usage_splits(
            [_split(code="8", abbreviation="RF")],
            season=2024,
            league_id=103,
            level_group="MLB",
        )


def test_project_fielding_usage_rejects_nonzero_dh_outs() -> None:
    with pytest.raises(ValueError, match="DH row has nonzero defensive outs"):
        project_fielding_usage_splits(
            [
                _split(
                    code="10",
                    abbreviation="DH",
                    name="Designated Hitter",
                    innings="0.1",
                )
            ],
            season=2024,
            league_id=103,
            level_group="MLB",
        )


def test_project_fielding_usage_rejects_duplicate_source_grain() -> None:
    row = _split()
    with pytest.raises(ValueError, match="violates season/league/team/player/position grain"):
        project_fielding_usage_splits(
            [row, row], season=2024, league_id=103, level_group="MLB"
        )
