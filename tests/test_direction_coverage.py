from __future__ import annotations

from math import pi, tan

import polars as pl

from universal_baseball.direction_coverage import (
    build_direction_coverage_report,
    collapse_direction_evidence,
    field_location_direction_expr,
)


def _coordinates_for_final_angle(angle_degrees: float) -> tuple[float, float]:
    geometric_angle = angle_degrees / 0.75
    forward = 100.0
    horizontal = tan(geometric_angle * pi / 180.0) * forward
    return 125.42 + horizontal, 198.27 - forward


def test_collapse_direction_evidence_keeps_agreement_and_nulls_conflicts() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1"],
            "at_bat_number": ["0", "0", "0"],
            "pitch_number": ["1", "1", "1"],
            "type": ["X", "X", "X"],
            "bb_type": ["ground_ball", "ground_ball", "line_drive"],
            "hit_location": ["6", "6", "6"],
            "hc_x": [100.0, 100.0, 100.0],
            "hc_y": [100.0, 100.0, 100.0],
            "stand": ["R", "R", "R"],
        }
    )

    collapsed = collapse_direction_evidence(frame)
    row = collapsed.to_dicts()[0]

    assert collapsed.height == 1
    assert row["type"] == "X"
    assert row["type__conflict"] is False
    assert row["bb_type"] is None
    assert row["bb_type__conflict"] is True
    assert row["hit_location"] == "6"
    assert row["hit_location__conflict"] is False


def test_conflicting_type_is_not_silently_counted_as_in_play() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "0"],
            "pitch_number": ["1", "1"],
            "type": ["X", "S"],
            "bb_type": ["line_drive", "line_drive"],
            "hit_location": ["7", "7"],
            "hc_x": [100.0, 100.0],
            "hc_y": [100.0, 100.0],
            "stand": ["R", "R"],
        }
    )

    report = build_direction_coverage_report(frame)

    assert report["natural_pitch_key_count"] == 1
    assert report["audited_field_conflicts"]["field_conflict_counts"]["type"] == 1
    assert report["audited_field_conflicts"]["conflicting_pitch_key_count"] == 1
    assert report["in_play_pitch_key_count"] == 0


def test_direction_coverage_uses_only_in_play_pitch_keys() -> None:
    left_x, left_y = _coordinates_for_final_angle(-30.0)
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "1"],
            "pitch_number": ["1", "1"],
            "type": ["X", "S"],
            "bb_type": ["line_drive", None],
            "hit_location": ["7", None],
            "hc_x": [left_x, None],
            "hc_y": [left_y, None],
            "stand": ["R", "R"],
        },
        schema={
            "game_pk": pl.String,
            "at_bat_number": pl.String,
            "pitch_number": pl.String,
            "type": pl.String,
            "bb_type": pl.String,
            "hit_location": pl.String,
            "hc_x": pl.Float64,
            "hc_y": pl.Float64,
            "stand": pl.String,
        },
    )

    report = build_direction_coverage_report(frame)

    assert report["in_play_pitch_key_count"] == 1
    assert report["coverage_counts"]["bb_type"] == 1
    assert report["coverage_counts"]["hc_x_and_hc_y"] == 1
    assert report["coverage_counts"]["coordinate_direction"] == 1
    assert report["coordinate_direction_counts"] == {"pull": 1}


def test_field_location_proxy_is_handedness_adjusted() -> None:
    frame = pl.DataFrame(
        {
            "hit_location": ["7", "8", "9", "7", "8", "9"],
            "stand": ["R", "R", "R", "L", "L", "L"],
        }
    ).with_columns(
        field_location_direction_expr(
            pl.col("hit_location"), pl.col("stand")
        ).alias("direction")
    )

    assert frame.get_column("direction").to_list() == [
        "pull",
        "center",
        "opposite",
        "opposite",
        "center",
        "pull",
    ]


def test_report_measures_coordinate_vs_location_agreement_by_trajectory() -> None:
    left_x, left_y = _coordinates_for_final_angle(-30.0)
    right_x, right_y = _coordinates_for_final_angle(30.0)
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1"],
            "at_bat_number": ["0", "1", "2"],
            "pitch_number": ["1", "1", "1"],
            "type": ["X", "X", "X"],
            "bb_type": ["line_drive", "ground_ball", "ground_ball"],
            "hit_location": ["7", "9", "7"],
            "hc_x": [left_x, right_x, right_x],
            "hc_y": [left_y, right_y, right_y],
            "stand": ["R", "R", "R"],
        }
    )

    report = build_direction_coverage_report(frame)

    assert report["coordinate_location_both_count"] == 3
    assert report["coordinate_location_agreement_count"] == 2
    assert report["coordinate_location_agreement_rate"] == 2 / 3
    assert report["agreement_by_trajectory"]["line_drive"]["agreement_rate"] == 1.0
    assert report["agreement_by_trajectory"]["ground_ball"]["agreement_rate"] == 0.5
