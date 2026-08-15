from __future__ import annotations

from universal_baseball.official import (
    project_official_boxscore,
    project_official_play_by_play,
)


def test_projection_keeps_zero_pitch_pa_and_tolerates_unknown_pitch_type() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 69,
                "result": {
                    "type": "atBat",
                    "event": "Intent Walk",
                    "eventType": "intent_walk",
                    "description": "Pitcher intentionally walks Batter.",
                },
                "about": {"halfInning": "top"},
                "matchup": {
                    "batter": {"id": 10},
                    "pitcher": {"id": 20},
                    "batSide": {"code": "L"},
                    "pitchHand": {"code": "R"},
                },
                "playEvents": [],
            },
            {
                "atBatIndex": 70,
                "result": {
                    "type": "atBat",
                    "event": "Single",
                    "eventType": "single",
                    "description": "Batter singles.",
                },
                "about": {"halfInning": "bottom"},
                "matchup": {
                    "batter": {"id": 30},
                    "pitcher": {"id": 40},
                    "batSide": {"code": "R"},
                    "pitchHand": {"code": "L"},
                },
                "playEvents": [
                    {
                        "index": 0,
                        "isPitch": True,
                        "pitchNumber": 1,
                        "details": {
                            "code": "X",
                            "description": "In play, no out",
                            "isInPlay": True,
                            "type": {"description": "Unknown"},
                        },
                        "pitchData": {"startSpeed": 88.0},
                        "hitData": {
                            "trajectory": "line_drive",
                            "location": "8",
                            "totalDistance": 286,
                            "launchSpeed": 101.4,
                            "launchAngle": 17,
                            "coordinates": {"coordX": 124.2, "coordY": 87.6},
                        },
                    }
                ],
            },
        ]
    }

    pa_frame, pitch_frame = project_official_play_by_play(780856, payload)

    assert pa_frame.height == 2
    assert pa_frame.get_column("official_pitch_count").to_list() == [0, 1]
    assert pa_frame.get_column("event_type").to_list() == ["intent_walk", "single"]
    assert pa_frame.get_column("batting_side").to_list() == ["away", "home"]
    assert pa_frame.get_column("batter_id").to_list() == [10, 30]
    assert pa_frame.get_column("pitcher_id").to_list() == [20, 40]
    assert pa_frame.get_column("batter_side").to_list() == ["L", "R"]
    assert pa_frame.get_column("pitcher_hand").to_list() == ["R", "L"]
    assert pitch_frame.height == 1
    assert pitch_frame.get_column("pitch_type_code").to_list() == [None]
    assert pitch_frame.get_column("code").to_list() == ["X"]
    assert pitch_frame.get_column("batter_side").to_list() == ["R"]
    assert pitch_frame.get_column("is_in_play").to_list() == [True]
    assert pitch_frame.get_column("hit_trajectory").to_list() == ["line_drive"]
    assert pitch_frame.get_column("hit_location").to_list() == ["8"]
    assert pitch_frame.get_column("hit_coord_x").to_list() == [124.2]
    assert pitch_frame.get_column("hit_coord_y").to_list() == [87.6]
    assert pitch_frame.get_column("hit_total_distance").to_list() == [286.0]
    assert pitch_frame.get_column("hit_launch_speed").to_list() == [101.4]
    assert pitch_frame.get_column("hit_launch_angle").to_list() == [17.0]


def test_projection_keeps_in_play_event_even_when_hit_data_is_missing() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 1,
                "result": {"type": "atBat", "eventType": "field_out"},
                "about": {"halfInning": "top"},
                "matchup": {"batSide": {"code": "L"}},
                "playEvents": [
                    {
                        "index": 0,
                        "isPitch": True,
                        "pitchNumber": 1,
                        "details": {
                            "code": "X",
                            "description": "In play, out(s)",
                            "isInPlay": True,
                        },
                    }
                ],
            }
        ]
    }

    _, pitch_frame = project_official_play_by_play(1, payload)

    row = pitch_frame.to_dicts()[0]
    assert row["is_in_play"] is True
    assert row["batter_side"] == "L"
    assert row["hit_trajectory"] is None
    assert row["hit_coord_x"] is None
    assert row["hit_launch_speed"] is None


def test_boxscore_projection_reads_only_required_team_batting_fields() -> None:
    payload = {
        "teams": {
            "away": {
                "teamStats": {
                    "batting": {
                        "plateAppearances": 39,
                        "atBats": 34,
                        "hits": 9,
                        "doubles": 2,
                        "triples": 1,
                        "homeRuns": 1,
                        "baseOnBalls": 3,
                        "intentionalWalks": 1,
                        "hitByPitch": 1,
                        "strikeOuts": 8,
                        "sacBunts": 0,
                        "sacFlies": 1,
                        "catchersInterference": 0,
                        "avg": ".265",
                    }
                }
            },
            "home": {
                "teamStats": {
                    "batting": {
                        "plateAppearances": 36,
                        "atBats": 32,
                        "hits": 7,
                        "doubles": 1,
                        "triples": 0,
                        "homeRuns": 0,
                        "baseOnBalls": 2,
                        "intentionalWalks": 0,
                        "hitByPitch": 1,
                        "strikeOuts": 10,
                        "sacBunts": 1,
                        "sacFlies": 0,
                        "catchersInterference": 0,
                    }
                }
            },
        }
    }

    frame = project_official_boxscore(123, payload)

    assert frame.height == 2
    away = frame.filter(frame["batting_side"] == "away").to_dicts()[0]
    home = frame.filter(frame["batting_side"] == "home").to_dicts()[0]
    assert away["plate_appearances"] == 39
    assert away["at_bats"] == 34
    assert away["intentional_walks"] == 1
    assert away["catchers_interference"] == 0
    assert home["plate_appearances"] == 36
    assert home["sac_bunts"] == 1
