from __future__ import annotations

import polars as pl

from universal_baseball.batted_ball import compare_source_batted_balls


def test_batted_ball_comparison_matches_direct_hitdata_fields() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "1"],
            "pitch_number": ["2", "3"],
            "stand": ["R", "L"],
            "bb_type": ["line_drive", None],
            "hit_location": ["8", None],
            "hc_x": ["124.2", None],
            "hc_y": ["87.6", None],
            "hit_distance_sc": ["286", None],
            "launch_speed": ["101.4", None],
            "launch_angle": ["17", None],
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "1"],
            "pitch_number": [2, 3],
            "is_in_play": [True, False],
            "batter_side": ["R", "L"],
            "hit_trajectory": ["line_drive", None],
            "hit_location": ["8", None],
            "hit_coord_x": [124.2, None],
            "hit_coord_y": [87.6, None],
            "hit_total_distance": [286.0, None],
            "hit_launch_speed": [101.4, None],
            "hit_launch_angle": [17.0, None],
        }
    )

    result = compare_source_batted_balls(source, official)

    assert result["official_in_play_pitch_count"] == 1
    assert result["shared_in_play_pitch_key_count"] == 1
    assert result["source_missing_in_play_pitch_key_count"] == 0
    assert result["total_field_mismatch_count"] == 0
    assert result["total_source_field_conflict_count"] == 0
    assert result["field_summaries"]["bb_type"]["both_nonblank"] == 1
    assert result["field_summaries"]["bb_type"][
        "agreement_rate_when_both_nonblank"
    ] == 1.0
    assert result["field_summaries"]["hc_x"]["matches_when_both_nonblank"] == 1
    assert result["certification_clean"] is True


def test_batted_ball_comparison_normalizes_integer_location_codes_from_float_csv() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": ["2"],
            "hit_location": ["9.0"],
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": [2],
            "is_in_play": [True],
            "hit_location": ["9"],
        }
    )

    result = compare_source_batted_balls(source, official)

    assert result["field_summaries"]["hit_location"][
        "matches_when_both_nonblank"
    ] == 1
    assert result["total_field_mismatch_count"] == 0
    assert result["certification_clean"] is True


def test_batted_ball_comparison_reports_missing_source_metadata_and_mismatch() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": ["2"],
            "stand": ["R"],
            "bb_type": ["ground_ball"],
            "hit_location": [None],
            "hc_x": [None],
            "hc_y": [None],
            "hit_distance_sc": [None],
            "launch_speed": [None],
            "launch_angle": [None],
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": [2],
            "is_in_play": [True],
            "batter_side": ["R"],
            "hit_trajectory": ["line_drive"],
            "hit_location": ["8"],
            "hit_coord_x": [124.2],
            "hit_coord_y": [87.6],
            "hit_total_distance": [286.0],
            "hit_launch_speed": [101.4],
            "hit_launch_angle": [17.0],
        }
    )

    result = compare_source_batted_balls(source, official)

    assert result["field_summaries"]["bb_type"]["mismatches_when_both_nonblank"] == 1
    assert result["field_summaries"]["hit_location"][
        "source_missing_when_official_present"
    ] == 1
    assert result["total_field_mismatch_count"] == 1
    assert result["certification_clean"] is False


def test_batted_ball_comparison_never_silently_resolves_conflicting_source_payloads() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "0"],
            "pitch_number": ["2", "2"],
            "stand": ["R", "R"],
            "bb_type": ["line_drive", "ground_ball"],
            "hit_location": ["8", "8"],
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": [2],
            "is_in_play": [True],
            "batter_side": ["R"],
            "hit_trajectory": ["line_drive"],
            "hit_location": ["8"],
        }
    )

    result = compare_source_batted_balls(source, official)

    assert result["field_summaries"]["bb_type"]["source_conflicting_key_count"] == 1
    assert result["total_source_field_conflict_count"] == 1
    assert result["source_field_conflict_examples"][0]["conflicts"]["bb_type"] == [
        "line_drive",
        "ground_ball",
    ]
    assert result["certification_clean"] is False


def test_batted_ball_comparison_reports_current_official_bip_missing_from_source() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": ["1"],
            "bb_type": [None],
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": [2],
            "is_in_play": [True],
            "hit_trajectory": ["ground_ball"],
        }
    )

    result = compare_source_batted_balls(source, official)

    assert result["official_in_play_pitch_count"] == 1
    assert result["shared_in_play_pitch_key_count"] == 0
    assert result["source_missing_in_play_pitch_key_count"] == 1
    assert result["certification_clean"] is False
