from __future__ import annotations

import polars as pl

from universal_baseball.mlb_performance_materialization import (
    classify_mlb_savant_contacts,
)


def test_mlb_savant_contacts_preserve_official_authority() -> None:
    frame = pl.DataFrame(
        {
            "game_year": [2024],
            "league_id": [103],
            "game_pk": [1],
            "at_bat_index": [2],
            "pitch_number": [3],
            "batter_mlbam_id": [10],
            "batter_side": ["R"],
            "bb_type": ["ground_ball"],
            "hc_x": [125.42],
            "hc_y": [100.0],
            "result_description": ["grounds out"],
            "is_contact": [True],
        }
    )
    result = classify_mlb_savant_contacts(frame)
    row = result.to_dicts()[0]
    assert row["season"] == 2024
    assert row["league_id"] == 103
    assert row["batter_mlbam_id"] == 10
    assert row["participant_authority"] == "savant_official"
    assert row["result_description_authority"] == "savant_official"
    assert row["core_bin"] in {"PULL_GB", "CENTER_GB", "OPPO_GB"}


def test_mlb_savant_contact_helper_ignores_noncontacts() -> None:
    frame = pl.DataFrame(
        {
            "game_year": [2024],
            "league_id": [104],
            "game_pk": [1],
            "at_bat_index": [2],
            "pitch_number": [3],
            "batter_mlbam_id": [10],
            "batter_side": ["L"],
            "bb_type": [None],
            "hc_x": [None],
            "hc_y": [None],
            "result_description": ["strikes out"],
            "is_contact": [False],
        },
        schema_overrides={"bb_type": pl.String, "hc_x": pl.Float64, "hc_y": pl.Float64},
    )
    result = classify_mlb_savant_contacts(frame)
    assert result.is_empty()
