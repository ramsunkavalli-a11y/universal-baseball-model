from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.canonical_adapters import (
    current_event_semantics_snapshot_id,
    normalize_armstjc_pitch_observations,
    normalize_official_play_sequence_observations,
    stable_payload_hash,
)


SNAPSHOT = "a" * 64
NORMALIZATION = "b" * 64


def test_stable_payload_hash_is_key_order_independent() -> None:
    assert stable_payload_hash({"b": 2, "a": 1}) == stable_payload_hash({"a": 1, "b": 2})


def test_armstjc_adapter_compacts_exact_duplicates_and_preserves_source_identity() -> None:
    raw = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1"],
            "at_bat_number": ["0", "0", "0"],
            "pitch_number": ["1", "1", "2"],
            "batter": ["101", "101", "999"],
            "pitcher": ["201", "201", "201"],
            "stand": ["R", "R", "R"],
            "p_throws": ["L", "L", "L"],
            "type": ["B", "B", "X"],
            "bb_type": [None, None, "line_drive"],
            "hit_location": [None, None, "9.0"],
            "hc_x": [None, None, "125.42"],
            "hc_y": [None, None, "98.27"],
            "play_end_datetime": ["same", "same", "later"],
        },
        schema_overrides={
            "bb_type": pl.String,
            "hit_location": pl.String,
            "hc_x": pl.String,
            "hc_y": pl.String,
        },
    )

    result = normalize_armstjc_pitch_observations(
        raw,
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )

    assert result.height == 2
    first = result.filter(pl.col("pitch_number") == 1).to_dicts()[0]
    second = result.filter(pl.col("pitch_number") == 2).to_dicts()[0]
    assert first["duplicate_row_count"] == 2
    assert second["source_batter_mlbam_id"] == 999
    assert second["source_pitcher_mlbam_id"] == 201
    assert second["is_in_play"] is True
    assert second["hit_location"] == 9
    assert second["hc_x"] == 125.42


def test_armstjc_adapter_keeps_distinct_raw_payload_variants() -> None:
    raw = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "0"],
            "pitch_number": ["1", "1"],
            "type": ["B", "B"],
            "play_start_datetime": ["v1", "v2"],
        }
    )

    result = normalize_armstjc_pitch_observations(
        raw,
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )

    assert result.height == 2
    assert result.get_column("payload_hash").n_unique() == 2
    assert result.get_column("pitch_code").to_list() == ["B", "B"]


def test_official_adapter_keeps_true_pa_and_non_pa_sequences() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 26,
                "result": {
                    "type": "atBat",
                    "event": "Caught Stealing 2B",
                    "eventType": "caught_stealing_2b",
                    "description": "Runner caught stealing second.",
                },
                "about": {
                    "inning": 4,
                    "halfInning": "top",
                    "startTime": "2023-08-01T19:00:00Z",
                    "endTime": "2023-08-01T19:01:00Z",
                },
                "matchup": {
                    "batter": {"id": 101},
                    "pitcher": {"id": 201},
                    "batSide": {"code": "R"},
                    "pitchHand": {"code": "L"},
                },
                "playEvents": [
                    {"index": 0, "isPitch": True, "pitchNumber": 1},
                    {"index": 1, "isPitch": False},
                ],
            },
            {
                "atBatIndex": 27,
                "result": {
                    "type": "atBat",
                    "event": "Single",
                    "eventType": "single",
                    "description": "Batter singles.",
                },
                "about": {"inning": 5, "halfInning": "top"},
                "matchup": {
                    "batter": {"id": 102},
                    "pitcher": {"id": 201},
                    "batSide": {"code": "L"},
                    "pitchHand": {"code": "L"},
                },
                "playEvents": [
                    {"index": 0, "isPitch": True, "pitchNumber": 1}
                ],
            },
        ]
    }

    result = normalize_official_play_sequence_observations(
        1,
        payload,
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    ).sort("at_bat_index")

    assert result.get_column("classification_status").to_list() == [
        "official_non_pa",
        "official_true_pa",
    ]
    assert result.get_column("is_plate_appearance").to_list() == [False, True]
    assert result.get_column("official_physical_pitch_count").to_list() == [1, 1]
    assert result.get_column("event_semantics_snapshot_id").n_unique() == 1
    assert len(current_event_semantics_snapshot_id()) == 64


def test_official_adapter_fails_on_unknown_event_semantics() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 1,
                "result": {"eventType": "future_rule_event"},
                "matchup": {},
                "about": {},
                "playEvents": [],
            }
        ]
    }
    with pytest.raises(ValueError, match="unknown eventType"):
        normalize_official_play_sequence_observations(
            1,
            payload,
            source_snapshot_id=SNAPSHOT,
            normalization_id=NORMALIZATION,
        )
