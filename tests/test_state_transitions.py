from __future__ import annotations

import json

from universal_baseball.state_transitions import (
    build_official_state_transitions,
    transition_quality_flags,
)


SNAPSHOT = "a" * 64
NORMALIZATION = "b" * 64


def _runner(
    runner_id: int,
    *,
    play_index: int,
    origin: str | None,
    end: str | None,
    event_type: str,
    scoring: bool = False,
    is_out: bool = False,
) -> dict:
    return {
        "movement": {
            "originBase": origin,
            "start": origin,
            "end": end,
            "outBase": end if is_out else None,
            "isOut": is_out,
        },
        "details": {
            "playIndex": play_index,
            "eventType": event_type,
            "event": event_type,
            "runner": {"id": runner_id},
            "isScoringEvent": scoring,
            "isOut": is_out,
        },
    }


def _event(index: int, *, outs: int, event_type: str, is_pitch: bool = True) -> dict:
    return {
        "index": index,
        "isPitch": is_pitch,
        "pitchNumber": index + 1 if is_pitch else None,
        "count": {"outs": outs},
        "details": {"eventType": event_type},
    }


def _payload() -> dict:
    return {
        "allPlays": [
            {
                "atBatIndex": 0,
                "about": {"inning": 1, "halfInning": "top"},
                "result": {
                    "eventType": "single",
                    "isOut": False,
                    "awayScore": 0,
                    "homeScore": 0,
                },
                "matchup": {"postOnFirst": {"id": 10}},
                "playEvents": [_event(0, outs=0, event_type="single")],
                "runners": [
                    _runner(
                        10,
                        play_index=0,
                        origin=None,
                        end="1B",
                        event_type="single",
                    )
                ],
            },
            {
                "atBatIndex": 1,
                "about": {"inning": 1, "halfInning": "top"},
                "result": {
                    "eventType": "strikeout",
                    "isOut": True,
                    "awayScore": 0,
                    "homeScore": 0,
                },
                "matchup": {"postOnSecond": {"id": 10}},
                "playEvents": [
                    _event(0, outs=0, event_type="pitch"),
                    _event(1, outs=0, event_type="stolen_base_2b", is_pitch=False),
                    _event(2, outs=1, event_type="strikeout"),
                ],
                "runners": [
                    _runner(
                        10,
                        play_index=1,
                        origin="1B",
                        end="2B",
                        event_type="stolen_base_2b",
                    )
                ],
            },
            {
                "atBatIndex": 2,
                "about": {"inning": 1, "halfInning": "top"},
                "result": {
                    "eventType": "double",
                    "isOut": False,
                    "awayScore": 1,
                    "homeScore": 0,
                },
                "matchup": {"postOnSecond": {"id": 20}},
                "playEvents": [_event(0, outs=1, event_type="double")],
                "runners": [
                    _runner(
                        10,
                        play_index=0,
                        origin="2B",
                        end="score",
                        event_type="double",
                        scoring=True,
                    ),
                    _runner(
                        20,
                        play_index=0,
                        origin=None,
                        end="2B",
                        event_type="double",
                    ),
                ],
            },
        ]
    }


def test_replay_splits_preterminal_runner_event_from_terminal_pa() -> None:
    frame = build_official_state_transitions(
        1,
        _payload(),
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )
    rows = frame.to_dicts()
    assert len(rows) == 4
    assert transition_quality_flags(frame).is_empty()

    first = rows[0]
    assert first["event_type"] == "single"
    assert (first["start_bases_code"], first["end_bases_code"]) == (0, 1)

    steal = rows[1]
    assert steal["event_type"] == "stolen_base_2b"
    assert steal["is_terminal_sequence_result"] is False
    assert (steal["start_bases_code"], steal["end_bases_code"]) == (1, 2)
    assert (steal["start_outs"], steal["end_outs"]) == (0, 0)

    strikeout = rows[2]
    assert strikeout["event_type"] == "strikeout"
    assert strikeout["is_plate_appearance_result"] is True
    assert (strikeout["start_bases_code"], strikeout["end_bases_code"]) == (2, 2)
    assert (strikeout["start_outs"], strikeout["end_outs"]) == (0, 1)
    assert strikeout["event_outs"] == 1

    double = rows[3]
    assert double["event_type"] == "double"
    assert double["runs_scored"] == 1
    assert (double["start_bases_code"], double["end_bases_code"]) == (2, 2)
    assert (double["start_bat_score"], double["end_bat_score"]) == (0, 1)


def test_runner_event_types_are_preserved_as_structured_diagnostic() -> None:
    frame = build_official_state_transitions(
        1,
        _payload(),
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )
    steal = frame.filter(~frame["is_terminal_sequence_result"]).to_dicts()[0]
    assert json.loads(steal["runner_event_types_json"]) == ["stolen_base_2b"]
    assert steal["re24_state_event_candidate"] is True
