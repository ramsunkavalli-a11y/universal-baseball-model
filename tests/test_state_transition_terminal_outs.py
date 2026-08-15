from __future__ import annotations

import json

import polars as pl

from universal_baseball.state_transition_terminal_outs import apply_terminal_allplay_outs
from universal_baseball.state_transitions import build_official_state_transitions


SNAPSHOT = "a" * 64
NORMALIZATION = "b" * 64


def test_top_level_third_out_clears_terminal_bases_and_quality_flag() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 0,
                "about": {"inning": 1, "halfInning": "top"},
                "count": {"outs": 3},
                "result": {
                    "eventType": "field_out",
                    "isOut": True,
                    "awayScore": 0,
                    "homeScore": 0,
                },
                "matchup": {},
                # Terminal playEvent count can remain at the pre-third-out value.
                "playEvents": [
                    {
                        "index": 0,
                        "isPitch": True,
                        "pitchNumber": 1,
                        "count": {"outs": 2},
                        "details": {"eventType": "field_out"},
                    }
                ],
                # Runner on first is retired on the play; the batter is also out.
                "runners": [
                    {
                        "movement": {
                            "originBase": "1B",
                            "start": "1B",
                            "end": None,
                            "outBase": "2B",
                            "isOut": True,
                        },
                        "details": {
                            "playIndex": 0,
                            "eventType": "field_out",
                            "runner": {"id": 10},
                            "isScoringEvent": False,
                            "isOut": True,
                        },
                    }
                ],
            }
        ]
    }

    provisional = build_official_state_transitions(
        1,
        payload,
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )
    corrected = apply_terminal_allplay_outs(provisional, payload)
    row = corrected.to_dicts()[0]

    assert row["end_outs"] == 3
    assert row["end_bases_code"] == 0
    assert json.loads(row["quality_flags_json"]) == []


def test_non_inning_end_outs_disagreement_fails_loudly() -> None:
    frame = pl.DataFrame(
        {
            "normalization_id": [NORMALIZATION],
            "source_snapshot_id": [SNAPSHOT],
            "game_pk": [1],
            "inning": [1],
            "half_inning": ["top"],
            "at_bat_index": [0],
            "transition_index": [0],
            "play_event_index": [0],
            "is_terminal_sequence_result": [True],
            "is_plate_appearance_result": [True],
            "event_type": ["field_out"],
            "runner_event_types_json": ["[]"],
            "start_outs": [0],
            "end_outs": [0],
            "event_outs": [0],
            "start_bases_code": [0],
            "end_bases_code": [0],
            "runs_scored": [0],
            "start_bat_score": [0],
            "end_bat_score": [0],
            "state_changed": [False],
            "re24_state_event_candidate": [True],
            "quality_flags_json": ["[]"],
        }
    )
    payload = {
        "allPlays": [
            {
                "atBatIndex": 0,
                "count": {"outs": 1},
                "matchup": {},
            }
        ]
    }

    try:
        apply_terminal_allplay_outs(frame, payload)
    except ValueError as exc:
        assert "before inning end" in str(exc)
    else:
        raise AssertionError("expected non-third-out discrepancy to fail")
