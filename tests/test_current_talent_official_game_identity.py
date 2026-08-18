from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_official_game_identity import (
    OfficialGameLeagueIdentity,
    augment_game_league_map_with_official_identity,
    project_official_game_league_identity,
)


def _feed(*, game_type: str = "R", league_id: int = 121, sport_id: int = 16):
    return {
        "gameData": {
            "game": {"type": game_type},
            "datetime": {"officialDate": "2024-07-03"},
            "teams": {
                "away": {
                    "id": 1,
                    "league": {"id": league_id},
                    "sport": {"id": sport_id},
                },
                "home": {
                    "id": 2,
                    "league": {"id": league_id},
                    "sport": {"id": sport_id},
                },
            },
        }
    }


def test_project_official_game_identity_requires_one_team_league_and_sport():
    identity = project_official_game_league_identity(774353, _feed())
    assert identity == OfficialGameLeagueIdentity(
        game_pk=774353,
        game_date=date(2024, 7, 3),
        game_type="R",
        league_id=121,
        sport_id=16,
        away_team_id=1,
        home_team_id=2,
    )


def test_project_official_game_identity_rejects_cross_league_ambiguity():
    payload = _feed()
    payload["gameData"]["teams"]["home"]["league"]["id"] = 124
    with pytest.raises(ValueError, match="one unambiguous team league"):
        project_official_game_league_identity(774353, payload)


def test_project_official_game_identity_rejects_non_regular_game():
    with pytest.raises(ValueError, match="not regular season"):
        project_official_game_league_identity(774353, _feed(game_type="S"))


def test_augment_same_game_map_adds_only_certified_expected_identity():
    existing = pl.DataFrame({"game_pk": [1], "league_id": [121]})
    identity = project_official_game_league_identity(774353, _feed(league_id=124))
    augmented, metrics = augment_game_league_map_with_official_identity(
        existing,
        [identity],
        expected_league_ids=frozenset({121, 124, 130}),
        expected_sport_id=16,
    )
    assert augmented.to_dicts() == [
        {"game_pk": 1, "league_id": 121},
        {"game_pk": 774353, "league_id": 124},
    ]
    assert metrics["official_exact_game_identity_added_count"] == 1
    assert metrics["filename_level_used_as_league_identity"] is False


def test_augment_same_game_map_rejects_wrong_sport_or_league():
    existing = pl.DataFrame({"game_pk": [1], "league_id": [121]})
    wrong_sport = project_official_game_league_identity(2, _feed(sport_id=14))
    with pytest.raises(ValueError, match="sport"):
        augment_game_league_map_with_official_identity(
            existing,
            [wrong_sport],
            expected_league_ids=frozenset({121, 124, 130}),
            expected_sport_id=16,
        )

    wrong_league = project_official_game_league_identity(3, _feed(league_id=117))
    with pytest.raises(ValueError, match="outside expected"):
        augment_game_league_map_with_official_identity(
            existing,
            [wrong_league],
            expected_league_ids=frozenset({121, 124, 130}),
            expected_sport_id=16,
        )


def test_augment_same_game_map_never_overrides_disagreement():
    existing = pl.DataFrame({"game_pk": [774353], "league_id": [121]})
    identity = project_official_game_league_identity(774353, _feed(league_id=124))
    with pytest.raises(ValueError, match="disagrees"):
        augment_game_league_map_with_official_identity(
            existing,
            [identity],
            expected_league_ids=frozenset({121, 124, 130}),
            expected_sport_id=16,
        )
