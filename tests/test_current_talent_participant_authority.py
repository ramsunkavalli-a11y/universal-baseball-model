import polars as pl
import pytest

from universal_baseball.current_talent_participant_authority import (
    project_official_allplays_participant_authority,
)


def test_participant_authority_uses_allplays_grain_without_pitch_projection() -> None:
    payload = {
        "allPlays": [
            {
                "atBatIndex": 4,
                "result": {"eventType": "caught_stealing_2b"},
                "matchup": {"batter": {"id": 100}},
                "playEvents": [
                    {
                        "isPitch": True,
                        "details": {"code": 1},
                    },
                    {
                        "isPitch": True,
                        "details": {"code": "FF"},
                    },
                ],
            },
            {
                "atBatIndex": 5,
                "result": {"eventType": "single"},
                "matchup": {"batter": {"id": 200}},
                "playEvents": [],
            },
        ]
    }

    result = project_official_allplays_participant_authority(700001, payload)
    assert result.to_dicts() == [
        {
            "game_pk": 700001,
            "at_bat_index": 4,
            "official_batter_id": 100,
        },
        {
            "game_pk": 700001,
            "at_bat_index": 5,
            "official_batter_id": 200,
        },
    ]


def test_participant_authority_ignores_rows_without_sequence_or_batter_identity() -> None:
    result = project_official_allplays_participant_authority(
        1,
        {
            "allPlays": [
                {"matchup": {"batter": {"id": 10}}},
                {"atBatIndex": 2, "matchup": {}},
            ]
        },
    )
    assert result.is_empty()
    assert result.schema == {
        "game_pk": pl.Int64,
        "at_bat_index": pl.Int64,
        "official_batter_id": pl.Int64,
    }


def test_participant_authority_rejects_conflicting_duplicate_sequence_identity() -> None:
    with pytest.raises(ValueError, match="conflicting matchup batters"):
        project_official_allplays_participant_authority(
            1,
            {
                "allPlays": [
                    {"atBatIndex": 2, "matchup": {"batter": {"id": 10}}},
                    {"atBatIndex": 2, "matchup": {"batter": {"id": 11}}},
                ]
            },
        )
