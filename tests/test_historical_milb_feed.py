from __future__ import annotations

import pytest

from universal_baseball.historical_milb_feed import project_historical_milb_game_feed


def _feed() -> dict:
    batting = {
        "plateAppearances": 4,
        "atBats": 3,
        "hits": 1,
        "doubles": 1,
        "triples": 0,
        "homeRuns": 0,
        "baseOnBalls": 1,
        "intentionalWalks": 0,
        "hitByPitch": 0,
        "strikeOuts": 1,
        "sacFlies": 0,
        "sacBunts": 0,
        "catchersInterference": 0,
        "groundIntoDoublePlay": 0,
        "groundIntoTriplePlay": 0,
    }
    return {
        "gameData": {
            "game": {"pk": 539815, "season": "2018", "type": "R"},
            "datetime": {"officialDate": "2018-04-05"},
            "venue": {"id": 2520, "name": "Roger Dean Chevrolet Stadium"},
            "teams": {
                "away": {"id": 479, "league": {"id": 123}},
                "home": {"id": 279, "league": {"id": 123}},
            },
        },
        "liveData": {
            "boxscore": {
                "teams": {
                    "away": {
                        "players": {
                            "ID675649": {
                                "person": {"id": 675649},
                                "stats": {"batting": batting},
                            }
                        }
                    },
                    "home": {
                        "players": {
                            "ID670651": {
                                "person": {"id": 670651},
                                "stats": {"batting": batting},
                            }
                        }
                    },
                }
            }
        },
    }


def test_projects_player_game_authority_and_context() -> None:
    players, context = project_historical_milb_game_feed(
        _feed(), expected_game_id=539815
    )

    assert players.height == 2
    assert players.filter(players["player_id"] == 675649).row(0, named=True) == {
        "game_id": 539815,
        "game_date": "2018-04-05",
        "game_type": "R",
        "league_id": 123,
        "team_id": 479,
        "player_id": 675649,
        "side": "away",
        "batting_PA": 4,
        "batting_AB": 3,
        "batting_H": 1,
        "batting_2B": 1,
        "batting_3B": 0,
        "batting_HR": 0,
        "batting_BB": 1,
        "batting_IBB": 0,
        "batting_HBP": 0,
        "batting_SO": 1,
        "batting_SF": 0,
        "batting_SH": 0,
        "batting_CI": 0,
        "batting_GiDP": 0,
        "batting_GiTP": 0,
    }
    assert context.row(0, named=True)["venue_id"] == 2520


def test_rejects_wrong_game() -> None:
    with pytest.raises(ValueError, match="id mismatch"):
        project_historical_milb_game_feed(_feed(), expected_game_id=1)


def test_rejects_missing_league_authority() -> None:
    payload = _feed()
    payload["gameData"]["teams"]["away"].pop("league")
    with pytest.raises(ValueError, match="team or league identity"):
        project_historical_milb_game_feed(payload)


def test_accepts_historical_short_season_suffix() -> None:
    payload = _feed()
    payload["gameData"]["game"]["season"] = "2018.1"

    _, context = project_historical_milb_game_feed(payload)

    assert context["season"].item() == 2018


def test_collapses_duplicate_roster_entry_to_positive_team() -> None:
    payload = _feed()
    shadow = {
        "person": {"id": 675649},
        "stats": {
            "batting": {
                field: 0
                for field in {
                    "plateAppearances",
                    "atBats",
                    "hits",
                    "doubles",
                    "triples",
                    "homeRuns",
                    "baseOnBalls",
                    "intentionalWalks",
                    "hitByPitch",
                    "strikeOuts",
                    "sacFlies",
                    "sacBunts",
                    "catchersInterference",
                    "groundIntoDoublePlay",
                    "groundIntoTriplePlay",
                }
            }
        },
    }
    payload["liveData"]["boxscore"]["teams"]["home"]["players"]["ID675649"] = shadow

    players, _ = project_historical_milb_game_feed(payload)
    row = players.filter(players["player_id"] == 675649).row(0, named=True)

    assert players.filter(players["player_id"] == 675649).height == 1
    assert row["team_id"] == 479
    assert row["batting_PA"] == 4


def test_sums_suspended_game_stints_for_both_teams() -> None:
    payload = _feed()
    second = {
        "person": {"id": 675649},
        "stats": {
            "batting": {
                "plateAppearances": 1,
                "atBats": 1,
                "hits": 1,
                "doubles": 0,
                "triples": 0,
                "homeRuns": 0,
                "baseOnBalls": 0,
                "intentionalWalks": 0,
                "hitByPitch": 0,
                "strikeOuts": 0,
                "sacFlies": 0,
                "sacBunts": 0,
                "catchersInterference": 0,
                "groundIntoDoublePlay": 0,
                "groundIntoTriplePlay": 0,
            }
        },
    }
    payload["liveData"]["boxscore"]["teams"]["home"]["players"]["ID675649"] = second

    players, _ = project_historical_milb_game_feed(payload)
    row = players.filter(players["player_id"] == 675649).row(0, named=True)

    assert row["team_id"] is None
    assert row["side"] is None
    assert row["batting_PA"] == 5
    assert row["batting_H"] == 2
