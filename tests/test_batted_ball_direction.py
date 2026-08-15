from __future__ import annotations

from math import tan, pi

import polars as pl

from universal_baseball.batted_ball_direction import (
    batted_ball_direction_expr,
    field_spray_angle_expr,
)


def _coordinates_for_final_angle(angle_degrees: float) -> tuple[float, float]:
    """Build Statcast-style coordinates for a desired calibrated field angle."""

    geometric_angle = angle_degrees / 0.75
    forward = 100.0
    horizontal = tan(geometric_angle * pi / 180.0) * forward
    return 125.42 + horizontal, 198.27 - forward


def test_field_spray_angle_matches_public_petti_pybaseball_calibration() -> None:
    frame = pl.DataFrame(
        {
            "hc_x": [25.42, 125.42, 225.42],
            "hc_y": [98.27, 98.27, 98.27],
        }
    ).with_columns(
        field_spray_angle_expr(pl.col("hc_x"), pl.col("hc_y")).alias("angle")
    )

    angles = frame.get_column("angle").to_list()
    assert abs(angles[0] - (-33.75)) < 1e-9
    assert abs(angles[1]) < 1e-9
    assert abs(angles[2] - 33.75) < 1e-9


def test_direction_uses_equal_field_thirds_and_batter_hand() -> None:
    left_x, left_y = _coordinates_for_final_angle(-30.0)
    center_x, center_y = _coordinates_for_final_angle(0.0)
    right_x, right_y = _coordinates_for_final_angle(30.0)

    frame = pl.DataFrame(
        {
            "hc_x": [left_x, center_x, right_x, left_x, center_x, right_x],
            "hc_y": [left_y, center_y, right_y, left_y, center_y, right_y],
            "stand": ["R", "R", "R", "L", "L", "L"],
        }
    ).with_columns(
        batted_ball_direction_expr(
            pl.col("hc_x"), pl.col("hc_y"), pl.col("stand")
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


def test_exact_field_third_boundaries_are_center() -> None:
    minus_x, minus_y = _coordinates_for_final_angle(-15.0)
    plus_x, plus_y = _coordinates_for_final_angle(15.0)

    frame = pl.DataFrame(
        {
            "hc_x": [minus_x, plus_x, minus_x, plus_x],
            "hc_y": [minus_y, plus_y, minus_y, plus_y],
            "stand": ["R", "R", "L", "L"],
        }
    ).with_columns(
        batted_ball_direction_expr(
            pl.col("hc_x"), pl.col("hc_y"), pl.col("stand")
        ).alias("direction")
    )

    assert frame.get_column("direction").to_list() == [
        "center",
        "center",
        "center",
        "center",
    ]


def test_missing_coordinates_or_unknown_hand_stays_unknown() -> None:
    frame = pl.DataFrame(
        {
            "hc_x": [None, 125.42, 125.42],
            "hc_y": [98.27, None, 98.27],
            "stand": ["R", "L", "S"],
        },
        schema={"hc_x": pl.Float64, "hc_y": pl.Float64, "stand": pl.String},
    ).with_columns(
        batted_ball_direction_expr(
            pl.col("hc_x"), pl.col("hc_y"), pl.col("stand")
        ).alias("direction")
    )

    assert frame.get_column("direction").to_list() == [None, None, None]


def test_sparse_string_coordinates_are_cast_and_invalid_values_become_unknown() -> None:
    frame = pl.DataFrame(
        {
            "hc_x": ["25.42", "125.42", "not-a-number", ""],
            "hc_y": ["98.27", "98.27", "98.27", "98.27"],
            "stand": ["R", "R", "R", "L"],
        }
    ).with_columns(
        [
            field_spray_angle_expr(pl.col("hc_x"), pl.col("hc_y")).alias("angle"),
            batted_ball_direction_expr(
                pl.col("hc_x"), pl.col("hc_y"), pl.col("stand")
            ).alias("direction"),
        ]
    )

    angles = frame.get_column("angle").to_list()
    assert abs(angles[0] - (-33.75)) < 1e-9
    assert abs(angles[1]) < 1e-9
    assert angles[2] is None
    assert angles[3] is None
    assert frame.get_column("direction").to_list() == [
        "pull",
        "center",
        None,
        None,
    ]
