from __future__ import annotations

import polars as pl

from universal_baseball.performance_events import build_performance_events


def _sequences() -> pl.DataFrame:
    rows = [
        (0, "walk", 101, "R", "Example Batter walks."),
        (1, "strikeout", 102, "L", "Example Batter strikes out swinging."),
        (2, "field_out", 103, "R", "Example Batter flies out to center fielder Example Fielder."),
        (3, "sac_bunt", 104, "L", "Example Batter out on a sacrifice bunt."),
        (4, "field_out", 105, "L", "Example Batter grounds out to shortstop Example Fielder."),
        (5, "catcher_interf", 106, "R", "Example Batter reaches on catcher interference."),
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
            "result_description": [row[4] for row in rows],
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
    assert by_index[0]["fabio_core_bin"] == "BB_HBP"
    assert by_index[0]["evidence_status"] == "complete_non_bip"
    assert by_index[0]["is_foul_air_out"] is False
    assert by_index[1]["fabio_core_bin_pre_foul_screen"] == "K"
    assert by_index[1]["fabio_core_bin"] == "K"

    assert by_index[2]["trajectory_family"] == "OFFB"
    assert by_index[2]["direction"] == "pull"
    assert by_index[2]["fabio_core_bin_pre_foul_screen"] == "PULL_OFFB"
    assert by_index[2]["fabio_core_bin"] == "PULL_OFFB"
    assert by_index[2]["core_profile_eligible"] is True
    assert by_index[2]["foul_air_status"] == "not_foul_air_official_description"
    assert by_index[2]["evidence_status"] == "complete_bip"

    assert by_index[3]["trajectory_family"] == "BUNT"
    assert by_index[3]["evidence_status"] == "special_bunt"
    assert by_index[3]["fabio_core_bin_pre_foul_screen"] is None
    assert by_index[3]["fabio_core_bin"] is None

    assert by_index[4]["trajectory_family"] == "GB"
    assert by_index[4]["evidence_status"] == "missing_direction"
    assert by_index[4]["fabio_core_bin_pre_foul_screen"] is None
    assert by_index[4]["fabio_core_bin"] is None

    assert by_index[5]["performance_family"] == "special_non_bip"
    assert by_index[5]["evidence_status"] == "special_non_bip"
    assert by_index[5]["fabio_core_bin_pre_foul_screen"] is None
    assert by_index[5]["fabio_core_bin"] is None


def test_explicit_official_foul_territory_screens_air_out_from_core() -> None:
    sequences = _sequences().filter(pl.col("at_bat_index") == 2).with_columns(
        pl.lit(
            "Example Batter flies out to first baseman Example Fielder in foul territory."
        ).alias("result_description")
    )
    pitches = _pitches().filter(pl.col("at_bat_index") == 2)

    result = build_performance_events(sequences, pitches).to_dicts()[0]

    assert result["performance_family"] == "batted_ball"
    assert result["trajectory_family"] == "OFFB"
    assert result["fabio_core_bin_pre_foul_screen"] == "PULL_OFFB"
    assert result["core_profile_eligible_pre_foul_screen"] is True
    assert result["is_foul_air_out"] is True
    assert result["foul_air_status"] == "foul_air_official_foul_territory"
    assert result["fabio_core_bin"] is None
    assert result["core_profile_eligible"] is False


def test_explicit_foul_territory_screen_applies_to_line_drive_family() -> None:
    sequences = _sequences().filter(pl.col("at_bat_index") == 2).with_columns(
        pl.lit(
            "Example Batter lines out to third baseman Example Fielder in foul territory."
        ).alias("result_description")
    )
    pitches = pl.DataFrame(
        {
            "game_pk": [1],
            "at_bat_index": [2],
            "pitch_number": [1],
            "is_in_play": [True],
            "bb_type": ["line_drive"],
            "hc_x": [80.0],
            "hc_y": [100.0],
            "conflict_field_count": [0],
        }
    )

    result = build_performance_events(sequences, pitches).to_dicts()[0]

    assert result["trajectory_family"] == "LD"
    assert result["fabio_core_bin_pre_foul_screen"] == "PULL_LD"
    assert result["is_foul_air_out"] is True
    assert result["fabio_core_bin"] is None


def test_broad_foul_word_without_certified_phrase_does_not_screen_core() -> None:
    sequences = _sequences().filter(pl.col("at_bat_index") == 2).with_columns(
        pl.lit(
            "Example Batter flies out to left fielder Example Fielder near the foul line."
        ).alias("result_description")
    )
    pitches = _pitches().filter(pl.col("at_bat_index") == 2)

    result = build_performance_events(sequences, pitches).to_dicts()[0]

    assert result["is_foul_air_out"] is False
    assert result["foul_air_status"] == "not_foul_air_official_description"
    assert result["fabio_core_bin"] == "PULL_OFFB"


def test_missing_official_description_makes_airborne_core_eligibility_unknown() -> None:
    sequences = _sequences().filter(pl.col("at_bat_index") == 2).with_columns(
        pl.lit(None, dtype=pl.String).alias("result_description")
    )
    pitches = _pitches().filter(pl.col("at_bat_index") == 2)

    result = build_performance_events(sequences, pitches).to_dicts()[0]

    assert result["fabio_core_bin_pre_foul_screen"] == "PULL_OFFB"
    assert result["is_foul_air_out"] is None
    assert result["foul_air_status"] == "unknown_missing_official_description"
    assert result["fabio_core_bin"] is None
    assert result["core_profile_eligible"] is False


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
    assert result["fabio_core_bin"] is None


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
    assert result["core_profile_eligible"] is False
