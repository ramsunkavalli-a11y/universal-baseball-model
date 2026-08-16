from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.contact_profile import classify_contact_profile_events


def _contacts() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024] * 6,
            "league_id": [112] * 6,
            "game_pk": [1] * 6,
            "at_bat_index": [0, 1, 2, 3, 4, 5],
            "pitch_number": [1] * 6,
            "batter_mlbam_id": [101, 102, 103, 104, 105, 106],
            "participant_authority": [
                "source_default",
                "official_exception_overlay",
                "source_default",
                "source_default",
                "source_default",
                "source_default",
            ],
            "result_description_authority": ["source_certified_mirror"] * 6,
            "batter_side": ["R", "L", "R", "L", "R", "R"],
            "bb_type": [
                "fly_ball",
                "popup",
                "ground_ball",
                "bunt_grounder",
                "line_drive",
                None,
            ],
            "hc_x": [80.0, 120.0, 125.42, 120.0, 80.0, None],
            "hc_y": [100.0, 100.0, 100.0, 120.0, 100.0, None],
            "result_description": [
                "Batter flies out to center fielder.",
                "Batter pops out to first baseman in foul territory.",
                "Batter grounds out to shortstop.",
                "Batter out on a bunt.",
                None,
                "Batter reaches on a batted ball.",
            ],
        },
        schema_overrides={"bb_type": pl.String, "result_description": pl.String},
    )


def test_contact_profile_classifies_core_and_exclusion_states() -> None:
    result = classify_contact_profile_events(_contacts())
    assert result.height == 6
    by_index = {row["at_bat_index"]: row for row in result.to_dicts()}

    assert by_index[0]["trajectory_family"] == "OFFB"
    assert by_index[0]["direction"] == "pull"
    assert by_index[0]["core_bin"] == "PULL_OFFB"
    assert by_index[0]["contact_profile_status"] == "core_contact"

    assert by_index[1]["trajectory_family"] == "IFFB"
    assert by_index[1]["is_foul_air_out"] is True
    assert by_index[1]["core_bin"] is None
    assert by_index[1]["contact_profile_status"] == "foul_air_excluded"
    assert by_index[1]["participant_authority"] == "official_exception_overlay"

    assert by_index[2]["trajectory_family"] == "GB"
    assert by_index[2]["core_profile_eligible"] is True
    assert by_index[2]["foul_air_status"] == "not_foul_air_trajectory"

    assert by_index[3]["trajectory_family"] == "BUNT"
    assert by_index[3]["core_bin"] is None
    assert by_index[3]["contact_profile_status"] == "special_bunt"

    assert by_index[4]["trajectory_family"] == "LD"
    assert by_index[4]["core_bin"] is None
    assert by_index[4]["is_foul_air_out"] is None
    assert by_index[4]["contact_profile_status"] == "unknown_missing_foul_narrative"

    assert by_index[5]["trajectory_family"] == "UNKNOWN"
    assert by_index[5]["core_bin"] is None
    assert by_index[5]["contact_profile_status"] == "unknown_missing_trajectory"


def test_opposite_direction_uses_compact_oppo_core_bin_label() -> None:
    frame = _contacts().head(1).with_columns(
        pl.lit("ground_ball").alias("bb_type"),
        pl.lit(170.0).alias("hc_x"),
        pl.lit(100.0).alias("hc_y"),
        pl.lit("R").alias("batter_side"),
        pl.lit("Batter grounds out to second baseman.").alias("result_description"),
    )
    row = classify_contact_profile_events(frame).to_dicts()[0]
    assert row["direction"] == "opposite"
    assert row["core_bin"] == "OPPO_GB"


def test_ground_ball_does_not_require_result_narrative_for_core() -> None:
    frame = _contacts().filter(pl.col("at_bat_index") == 2).with_columns(
        pl.lit(None, dtype=pl.String).alias("result_description")
    )
    row = classify_contact_profile_events(frame).to_dicts()[0]
    assert row["trajectory_family"] == "GB"
    assert row["is_foul_air_out"] is False
    assert row["core_bin"] is not None
    assert row["contact_profile_status"] == "core_contact"


def test_contact_profile_rejects_duplicate_physical_keys() -> None:
    row = _contacts().head(1)
    with pytest.raises(ValueError, match="one row per physical contact key"):
        classify_contact_profile_events(pl.concat([row, row]))
