from __future__ import annotations

from universal_baseball.official import project_official_play_by_play


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
                "playEvents": [
                    {
                        "index": 0,
                        "isPitch": True,
                        "pitchNumber": 1,
                        "details": {
                            "code": "X",
                            "description": "In play, no out",
                            "type": {"description": "Unknown"},
                        },
                        "pitchData": {"startSpeed": 88.0},
                    }
                ],
            },
        ]
    }

    pa_frame, pitch_frame = project_official_play_by_play(780856, payload)

    assert pa_frame.height == 2
    assert pa_frame.get_column("official_pitch_count").to_list() == [0, 1]
    assert pa_frame.get_column("event_type").to_list() == ["intent_walk", "single"]
    assert pitch_frame.height == 1
    assert pitch_frame.get_column("pitch_type_code").to_list() == [None]
    assert pitch_frame.get_column("code").to_list() == ["X"]
