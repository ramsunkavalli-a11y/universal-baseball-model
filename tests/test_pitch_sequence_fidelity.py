from __future__ import annotations

from universal_baseball.pitch_sequence_fidelity import (
    summarize_game_pitch_sequences,
    summarize_league,
)


def _pitch(number: int, *, ball: bool = False, strike: bool = False, code: str = "C") -> dict:
    return {
        "isPitch": True,
        "pitchNumber": number,
        "details": {"isBall": ball, "isStrike": strike, "code": code},
        "pitchData": {"startSpeed": 92.0},
    }


def test_detects_outcome_minimal_synthetic_sequences() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 0,
                "result": {"eventType": "strikeout", "description": "K"},
                "playEvents": [
                    _pitch(1, strike=True),
                    _pitch(2, strike=True),
                    _pitch(3, strike=True),
                ],
            },
            {
                "atBatIndex": 1,
                "result": {"eventType": "walk", "description": "BB"},
                "playEvents": [
                    _pitch(1, ball=True, code="B"),
                    _pitch(2, ball=True, code="B"),
                    _pitch(3, ball=True, code="B"),
                    _pitch(4, ball=True, code="B"),
                ],
            },
            {
                "atBatIndex": 2,
                "result": {"eventType": "field_out", "description": "out"},
                "playEvents": [_pitch(1, code="X")],
            },
        ]
    }

    rows = summarize_game_pitch_sequences(1, payload, league_name="ACL")
    assert len(rows) == 3
    assert all(row["outcome_minimal_clean_signature"] for row in rows)

    league = summarize_league(rows)
    assert league["outcomes"]["strikeout"]["exact_minimum_pitch_count_rate"] == 1.0
    assert league["outcomes"]["walk"]["exact_minimum_pitch_count_rate"] == 1.0
    assert league["outcomes"]["batted_ball"]["exact_minimum_pitch_count_rate"] == 1.0


def test_pitch_number_gap_exposes_omitted_events() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 0,
                "result": {"eventType": "strikeout", "description": "K after missing pitches"},
                "playEvents": [
                    _pitch(1, strike=True),
                    _pitch(4, strike=True),
                    _pitch(6, strike=True),
                ],
            }
        ]
    }

    row = summarize_game_pitch_sequences(2, payload)[0]
    assert row["recorded_pitch_event_count"] == 3
    assert row["max_pitch_number"] == 6
    assert row["pitch_number_gap"] == 3
    assert row["exact_minimum_pitch_count"] is True


def test_normal_mixed_sequences_are_not_minimal_clean() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 0,
                "result": {"eventType": "strikeout", "description": "five-pitch K"},
                "playEvents": [
                    _pitch(1, ball=True, code="B"),
                    _pitch(2, strike=True),
                    _pitch(3, strike=True),
                    _pitch(4, strike=False, code="F"),
                    _pitch(5, strike=True),
                ],
            },
            {
                "atBatIndex": 1,
                "result": {"eventType": "walk", "description": "six-pitch walk"},
                "playEvents": [
                    _pitch(1, strike=True),
                    _pitch(2, ball=True, code="B"),
                    _pitch(3, ball=True, code="B"),
                    _pitch(4, strike=True),
                    _pitch(5, ball=True, code="B"),
                    _pitch(6, ball=True, code="B"),
                ],
            },
        ]
    }

    rows = summarize_game_pitch_sequences(3, payload)
    assert rows[0]["outcome_minimal_clean_signature"] is False
    assert rows[1]["outcome_minimal_clean_signature"] is False
    assert rows[0]["pitch_number_gap"] == 0
    assert rows[1]["pitch_number_gap"] == 0
