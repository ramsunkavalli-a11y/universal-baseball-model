from universal_baseball.official import project_official_play_by_play


def test_official_projection_accepts_mixed_numeric_and_string_pitch_codes() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 1,
                "result": {
                    "type": "atBat",
                    "event": "Strikeout",
                    "eventType": "strikeout",
                    "description": "Batter strikes out.",
                },
                "about": {"halfInning": "top"},
                "matchup": {
                    "batter": {"id": 10},
                    "pitcher": {"id": 20},
                    "batSide": {"code": "R"},
                    "pitchHand": {"code": "L"},
                },
                "playEvents": [
                    {
                        "index": 0,
                        "pitchNumber": 1,
                        "isPitch": True,
                        "details": {"code": 1, "event": "Strike", "eventType": "strike"},
                    },
                    {
                        "index": 1,
                        "pitchNumber": 2,
                        "isPitch": True,
                        "details": {"code": "FF", "event": "Foul", "eventType": "foul"},
                    },
                ],
            }
        ]
    }

    pa, pitches = project_official_play_by_play(700001, payload)
    assert pa.height == 1
    assert pitches.get_column("code").to_list() == ["1", "FF"]
    assert pitches.get_column("pitch_number").to_list() == [1, 2]
