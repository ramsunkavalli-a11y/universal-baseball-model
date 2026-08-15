"""Certified-candidate batted-ball direction transforms.

This module ports the public Bill Petti / pybaseball Statcast coordinate
conversion into Polars rather than adding a pandas dependency for one small
formula. It is not yet a promoted universal model feature; lower-level coverage
and fallback behavior still require empirical certification.
"""

from __future__ import annotations

from math import pi

import polars as pl


STATCAST_HOME_X = 125.42
STATCAST_HOME_Y = 198.27
STATCAST_SPRAY_CALIBRATION = 0.75
FIELD_THIRD_BOUNDARY_DEGREES = 15.0


def field_spray_angle_expr(hc_x: pl.Expr, hc_y: pl.Expr) -> pl.Expr:
    """Return field-relative Statcast spray angle in degrees.

    This matches the established Petti/pybaseball transform:

    ``atan2(hc_x - 125.42, 198.27 - hc_y) * 180/pi * 0.75``

    Negative values point toward left field, zero points toward straightaway
    center, and positive values point toward right field. Null coordinates stay
    null through the Polars expression.
    """

    return (
        pl.arctan2(hc_x - STATCAST_HOME_X, STATCAST_HOME_Y - hc_y)
        * (180.0 / pi)
        * STATCAST_SPRAY_CALIBRATION
    )


def batted_ball_direction_expr(
    hc_x: pl.Expr,
    hc_y: pl.Expr,
    stand: pl.Expr,
) -> pl.Expr:
    """Classify coordinate-based batted-ball direction as pull/center/opposite.

    The approximately 90-degree fair field is split into three equal 30-degree
    sectors, so ±15 degrees bound the center third. Exactly ±15 degrees is
    classified as center. Batter handedness converts left/right field into
    pull/opposite. Missing coordinates or a batting side other than L/R produce
    null rather than an imputed direction.
    """

    angle = field_spray_angle_expr(hc_x, hc_y)
    has_evidence = hc_x.is_not_null() & hc_y.is_not_null() & stand.is_in(["L", "R"])
    center = angle.is_between(
        -FIELD_THIRD_BOUNDARY_DEGREES,
        FIELD_THIRD_BOUNDARY_DEGREES,
        closed="both",
    )
    pull = ((stand == "R") & (angle < -FIELD_THIRD_BOUNDARY_DEGREES)) | (
        (stand == "L") & (angle > FIELD_THIRD_BOUNDARY_DEGREES)
    )

    return (
        pl.when(~has_evidence)
        .then(pl.lit(None, dtype=pl.String))
        .when(center)
        .then(pl.lit("center"))
        .when(pull)
        .then(pl.lit("pull"))
        .otherwise(pl.lit("opposite"))
    )
