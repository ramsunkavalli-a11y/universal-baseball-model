"""Deterministic batted-ball-quality evidence for richer Current Talent challengers.

This module intentionally stops before model fitting. It projects complete observed
Savant exit-velocity / launch-angle batted balls to a small canonical surface and
builds leakage-safe player features at an as-of cutoff.

Missing tracking is never imputed. Capability-tier assignment remains external so
source coverage can be certified at game/league/venue grain before these features
are used by a richer model.
"""

from __future__ import annotations

from datetime import date
from math import log

import polars as pl


TRACKED_BBE_HALF_LIFE_DAYS = 180.0
PRIMARY_MIN_COMPLETE_TRACKED_BBE = 20
SWEET_SPOT_MIN_DEGREES = 8.0
SWEET_SPOT_MAX_DEGREES = 32.0

TRACKED_BBE_KEY = ("game_pk", "player_id", "at_bat_number")
TRACKED_BBE_SCHEMA: dict[str, pl.DataType] = {
    "game_date": pl.Date,
    "game_pk": pl.Int64,
    "player_id": pl.Int64,
    "at_bat_number": pl.Int64,
    "launch_speed": pl.Float64,
    "launch_angle": pl.Float64,
    "sweet_spot": pl.Boolean,
}

TRACKED_FEATURE_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "raw_complete_tracked_bbe": pl.Int64,
    "effective_complete_tracked_bbe": pl.Float64,
    "recency_weighted_mean_exit_velocity": pl.Float64,
    "recency_weighted_sweet_spot_share": pl.Float64,
    "first_tracked_bbe_date": pl.Date,
    "last_tracked_bbe_date": pl.Date,
    "tracked_bbe_eligible": pl.Boolean,
}


def _integer_like(column: str, alias: str) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias)
    )


def project_complete_tracked_bbe(raw: pl.DataFrame) -> pl.DataFrame:
    """Project complete observed Savant EV+LA rows to one row per batted ball.

    The canonical key is ``game_pk + batter + at_bat_number``. Savant normally
    places launch metrics on the terminal/contact pitch of the plate appearance;
    multiple complete EV+LA rows for the same key are treated as source ambiguity
    and fail rather than being silently deduplicated.
    """

    required = {
        "game_date",
        "game_pk",
        "batter",
        "at_bat_number",
        "launch_speed",
        "launch_angle",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"tracked batted-ball source missing fields: {missing}")
    if raw.is_empty():
        return pl.DataFrame(schema=TRACKED_BBE_SCHEMA)

    projected = (
        raw.select(
            pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("game_date"),
            _integer_like("game_pk", "game_pk"),
            _integer_like("batter", "player_id"),
            _integer_like("at_bat_number", "at_bat_number"),
            pl.col("launch_speed").cast(pl.Float64, strict=False),
            pl.col("launch_angle").cast(pl.Float64, strict=False),
        )
        .filter(
            pl.col("game_date").is_not_null()
            & pl.col("game_pk").is_not_null()
            & pl.col("player_id").is_not_null()
            & pl.col("at_bat_number").is_not_null()
            & pl.col("launch_speed").is_not_null()
            & pl.col("launch_angle").is_not_null()
        )
        .with_columns(
            pl.col("launch_angle")
            .is_between(SWEET_SPOT_MIN_DEGREES, SWEET_SPOT_MAX_DEGREES, closed="both")
            .alias("sweet_spot")
        )
        .cast(TRACKED_BBE_SCHEMA, strict=True)
    )

    duplicate = projected.group_by(list(TRACKED_BBE_KEY)).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError(
            "tracked batted-ball source has multiple complete EV+LA rows for one "
            "game_pk + player_id + at_bat_number"
        )

    return projected.sort(["game_date", *TRACKED_BBE_KEY])


def build_batted_ball_quality_features(
    tracked_bbe: pl.DataFrame,
    *,
    cutoff: date,
    half_life_days: float = TRACKED_BBE_HALF_LIFE_DAYS,
    min_complete_tracked_bbe: int = PRIMARY_MIN_COMPLETE_TRACKED_BBE,
) -> pl.DataFrame:
    """Build leakage-safe EV/LA player features using only rows before cutoff."""

    if half_life_days <= 0:
        raise ValueError("tracked-BBE half-life must be positive")
    if min_complete_tracked_bbe < 1:
        raise ValueError("minimum complete tracked BBE must be at least one")
    missing = sorted(set(TRACKED_BBE_SCHEMA) - set(tracked_bbe.columns))
    if missing:
        raise ValueError(f"canonical tracked batted-ball evidence missing fields: {missing}")
    if tracked_bbe.is_empty():
        return pl.DataFrame(schema=TRACKED_FEATURE_SCHEMA)

    duplicate = tracked_bbe.group_by(list(TRACKED_BBE_KEY)).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("canonical tracked batted-ball evidence violates canonical grain")

    working = tracked_bbe.with_columns(
        pl.col("game_date").cast(pl.Date, strict=False).alias("game_date")
    ).filter(pl.col("game_date") < pl.lit(cutoff))
    if working.is_empty():
        return pl.DataFrame(schema=TRACKED_FEATURE_SCHEMA)

    days_old = (pl.lit(cutoff) - pl.col("game_date")).dt.total_days().cast(pl.Float64)
    weight = (-days_old * (log(2.0) / float(half_life_days))).exp()
    weighted = working.with_columns(weight.alias("_recency_weight"))

    features = (
        weighted.group_by("player_id")
        .agg(
            pl.len().cast(pl.Int64).alias("raw_complete_tracked_bbe"),
            pl.col("_recency_weight").sum().alias("effective_complete_tracked_bbe"),
            (
                (pl.col("launch_speed") * pl.col("_recency_weight")).sum()
                / pl.col("_recency_weight").sum()
            ).alias("recency_weighted_mean_exit_velocity"),
            (
                (pl.col("sweet_spot").cast(pl.Float64) * pl.col("_recency_weight")).sum()
                / pl.col("_recency_weight").sum()
            ).alias("recency_weighted_sweet_spot_share"),
            pl.col("game_date").min().alias("first_tracked_bbe_date"),
            pl.col("game_date").max().alias("last_tracked_bbe_date"),
        )
        .with_columns(
            pl.lit(cutoff).alias("as_of_date"),
            (pl.col("raw_complete_tracked_bbe") >= min_complete_tracked_bbe).alias(
                "tracked_bbe_eligible"
            ),
        )
        .select(*TRACKED_FEATURE_SCHEMA)
        .cast(TRACKED_FEATURE_SCHEMA, strict=True)
        .sort("player_id")
    )
    return features
