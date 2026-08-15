from __future__ import annotations

import polars as pl

from universal_baseball.performance_events import build_performance_events


def _sequences() -> pl.DataFrame:
    rows = [
        (0, "walk", 101, "R"),
        (1, "strikeout", 102, "L"),
        (2, "field_out", 103, "R"),
        (3, "sac_bunt", 104, "L"),
        (4, "field_out", 105, "L"),
        (5, "catcher_interf", 106, "R"),
    ]
    return pl.DataFrame(
        {
            "game_pk": [1] * len(rows),
            "at_bat_index": [row[0] for row in rows],
            "classification_status": ["official_true_pa"] * len(rows),
            "result_event_type": [row[1] for row in rows],
            "batter_mlbam_id": [row[2] for row in rows],
            "pitcher_mlbam_id": [201] * len(rows),
            "batter_side": [row[3] for row in rows],
        }
    )


def _pitches() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 1, 1, 1, 1, 1],
            "at_bat_index": [1, 1, 2, 3, 4, 4],
            "pitch_number": [1, 2, 1, 1, 1, 2],
            "is_in_play": [False, False, True, True, False, True],
            "bb_type": [None, None, "fly_ball", "bunt_grounder", None, "ground_ball"],
            "hc_x": [None, None, 80.0, 120.0, None, None],
            "hc_y": [None, None, 100.0, 120.0, None, None],
            "conflict_field_count": [0, 0, 0, 0, 0, 0],
        },
        schema_overrides={
            "bb_type": pl.String,
            "hc_x": pl.Float64,
            "hc_y": pl.Float64,
        },
    )


def test_performance_mapper_preserves_every_true_pa_and_core_bins() -> None:
    result = build_performance_events(_sequences(), _pitches())
    assert result.height == 6

    by_index = {row["at_bat_index"]: row for row in result.to_dicts()}
    assert by_index[0]["fabio_core_bin_pre_foul_screen"] == "BB_HBP"
    assert by_index[0]["evidence_status"] == "complete_non_bip"
    assert by_index[1]["fabio_core_bin_pre_foul_screen"] == "K"

    assert by_index[2]["trajectory_family"] == "OFFB"
    assert by_index[2]["direction"] == "pull"
    assert by_index[2]["fabio_core_bin_pre_foul_screen"] == "PULL_OFFB"
    assert by_index[2]["evidence_status"] == "complete_bip"

    assert by_index[3]["trajectory_family"] == "BUNT"
    assert by_index[3]["evidence_status"] == "special_bunt"
    assert by_index[3]["fabio_core_bin_pre_foul_screen"] is None

    assert by_index[4]["trajectory_family"] == "GB"
    assert by_index[4]["evidence_status"] == "missing_direction"
    assert by_index[4]["fabio_core_bin_pre_foul_screen"] is None

    assert by_index[5]["performance_family"] == "special_non_bip"
    assert by_index[5]["evidence_status"] == "special_non_bip"
    assert by_index[5]["fabio_core_bin_pre_foul_screen"] is None


def test_non_bip_with_in_play_source_evidence_is_not_silently_core_classified() -> None:
    sequences = _sequences().filter(pl.col("at_bat_index") == 0)
    pitches = pl.DataFrame(
        {
            "game_pk": [1],
            "at_bat_index": [0],
            "pitch_number": [1],
            "is_in_play": [True],
            "bb_type": ["line_drive"],
            "hc_x": [125.42],
            "hc_y": [100.0],
        }
    )

    result = build_performance_events(sequences, pitches).to_dicts()[0]
    assert result["evidence_status"] == "unexpected_in_play_non_bip"
    assert result["fabio_core_bin_pre_foul_screen"] is None


def test_conflicted_in_play_flag_is_explicit_missing_evidence() -> None:
    sequences = _sequences().filter(pl.col("at_bat_index") == 2)
    pitches = pl.DataFrame(
        {
            "game_pk": [1],
            "at_bat_index": [2],
            "pitch_number": [1],
            "is_in_play": [None],
            "bb_type": [None],
            "hc_x": [None],
            "hc_y": [None],
            "conflict_field_count": [1],
        },
        schema_overrides={
            "is_in_play": pl.Boolean,
            "bb_type": pl.String,
            "hc_x": pl.Float64,
            "hc_y": pl.Float64,
        },
    )

    result = build_performance_events(sequences, pitches).to_dicts()[0]
    assert result["evidence_status"] == "conflicted_in_play_flag"
    assert result["core_profile_eligible_pre_foul_screen"] is False
