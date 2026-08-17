"""Source-completeness diagnostics for tracked EV/launch-angle evidence.

The richer Current Talent challenger uses only complete observed EV+LA batted
balls, but its audit surface also needs to show how much returned BBE-like source
evidence was complete and how many games contributed. These diagnostics remain
separate from talent features: they describe measurement/source coverage, not
player skill, and they never impute a missing measurement.
"""

from __future__ import annotations

from datetime import date

import polars as pl


TRACKING_OBSERVATION_KEY = ("game_pk", "player_id", "at_bat_number")
TRACKING_OBSERVATION_SCHEMA: dict[str, pl.DataType] = {
    "game_date": pl.Date,
    "game_pk": pl.Int64,
    "player_id": pl.Int64,
    "at_bat_number": pl.Int64,
    "bbe_like_source_rows": pl.Int64,
    "rows_with_exit_velocity": pl.Int64,
    "rows_with_launch_angle": pl.Int64,
    "complete_ev_la_rows": pl.Int64,
    "has_complete_ev_la": pl.Boolean,
    "ambiguous_multiple_complete_ev_la": pl.Boolean,
}

TRACKING_COMPLETENESS_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "bbe_like_observations": pl.Int64,
    "complete_ev_la_bbe": pl.Int64,
    "complete_ev_la_share": pl.Float64,
    "tracked_game_count": pl.Int64,
    "complete_tracked_game_count": pl.Int64,
    "ambiguous_multiple_complete_ev_la_bbe": pl.Int64,
}


def _integer_like(column: str, alias: str) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias)
    )


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (
        pl.col(column).cast(pl.String).str.strip_chars() != ""
    )


def project_savant_bbe_tracking_observations(raw: pl.DataFrame) -> pl.DataFrame:
    """Collapse broad Savant BBE-like rows to one source observation per PA key.

    The broad BBE-like definition is for *measurement completeness diagnostics*
    only. It must not replace the stricter complete-EV+LA feature projection.
    Multiple complete EV+LA rows at one canonical key are retained as an explicit
    ambiguity flag rather than silently deduplicated.
    """

    required = {
        "game_date",
        "game_pk",
        "batter",
        "at_bat_number",
        "bb_type",
        "description",
        "launch_speed",
        "launch_angle",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Savant tracking diagnostics missing fields: {missing}")
    if raw.is_empty():
        return pl.DataFrame(schema=TRACKING_OBSERVATION_SCHEMA)

    projected = raw.select(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("game_date"),
        _integer_like("game_pk", "game_pk"),
        _integer_like("batter", "player_id"),
        _integer_like("at_bat_number", "at_bat_number"),
        pl.col("bb_type").cast(pl.String),
        pl.col("description").cast(pl.String),
        pl.col("launch_speed").cast(pl.Float64, strict=False),
        pl.col("launch_angle").cast(pl.Float64, strict=False),
    ).filter(
        pl.col("game_date").is_not_null()
        & pl.col("game_pk").is_not_null()
        & pl.col("player_id").is_not_null()
        & pl.col("at_bat_number").is_not_null()
    )

    bbe_like = projected.filter(
        _nonblank("bb_type")
        | (pl.col("description").str.to_lowercase() == "hit_into_play")
        | pl.col("launch_speed").is_not_null()
        | pl.col("launch_angle").is_not_null()
    )
    if bbe_like.is_empty():
        return pl.DataFrame(schema=TRACKING_OBSERVATION_SCHEMA)

    date_conflict = (
        bbe_like.group_by(list(TRACKING_OBSERVATION_KEY))
        .agg(pl.col("game_date").n_unique().alias("date_count"))
        .filter(pl.col("date_count") != 1)
    )
    if not date_conflict.is_empty():
        raise ValueError("Savant BBE-like source has conflicting game dates at canonical key")

    observations = (
        bbe_like.group_by(list(TRACKING_OBSERVATION_KEY))
        .agg(
            pl.col("game_date").first().alias("game_date"),
            pl.len().cast(pl.Int64).alias("bbe_like_source_rows"),
            pl.col("launch_speed").is_not_null().sum().cast(pl.Int64).alias(
                "rows_with_exit_velocity"
            ),
            pl.col("launch_angle").is_not_null().sum().cast(pl.Int64).alias(
                "rows_with_launch_angle"
            ),
            (
                pl.col("launch_speed").is_not_null()
                & pl.col("launch_angle").is_not_null()
            ).sum().cast(pl.Int64).alias("complete_ev_la_rows"),
        )
        .with_columns(
            (pl.col("complete_ev_la_rows") >= 1).alias("has_complete_ev_la"),
            (pl.col("complete_ev_la_rows") > 1).alias("ambiguous_multiple_complete_ev_la"),
        )
        .select(*TRACKING_OBSERVATION_SCHEMA)
        .cast(TRACKING_OBSERVATION_SCHEMA, strict=True)
        .sort(["game_date", *TRACKING_OBSERVATION_KEY])
    )
    return observations


def build_tracking_completeness_diagnostics(
    observations: pl.DataFrame,
    *,
    cutoff: date,
) -> pl.DataFrame:
    """Summarize pre-cutoff tracking completeness at player grain."""

    missing = sorted(set(TRACKING_OBSERVATION_SCHEMA) - set(observations.columns))
    if missing:
        raise ValueError(f"tracking observations missing fields: {missing}")
    if observations.is_empty():
        return pl.DataFrame(schema=TRACKING_COMPLETENESS_SCHEMA)

    duplicate = observations.group_by(list(TRACKING_OBSERVATION_KEY)).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("tracking observations violate canonical BBE-like grain")

    eligible = observations.with_columns(
        pl.col("game_date").cast(pl.Date, strict=False).alias("game_date")
    ).filter(pl.col("game_date") < pl.lit(cutoff))
    if eligible.is_empty():
        return pl.DataFrame(schema=TRACKING_COMPLETENESS_SCHEMA)

    result = (
        eligible.group_by("player_id")
        .agg(
            pl.len().cast(pl.Int64).alias("bbe_like_observations"),
            pl.col("has_complete_ev_la").sum().cast(pl.Int64).alias("complete_ev_la_bbe"),
            pl.col("game_pk").n_unique().cast(pl.Int64).alias("tracked_game_count"),
            pl.col("game_pk")
            .filter(pl.col("has_complete_ev_la"))
            .n_unique()
            .cast(pl.Int64)
            .alias("complete_tracked_game_count"),
            pl.col("ambiguous_multiple_complete_ev_la")
            .sum()
            .cast(pl.Int64)
            .alias("ambiguous_multiple_complete_ev_la_bbe"),
        )
        .with_columns(
            (
                pl.col("complete_ev_la_bbe")
                / pl.col("bbe_like_observations").cast(pl.Float64)
            ).alias("complete_ev_la_share"),
            pl.lit(cutoff).alias("as_of_date"),
        )
        .select(*TRACKING_COMPLETENESS_SCHEMA)
        .cast(TRACKING_COMPLETENESS_SCHEMA, strict=True)
        .sort("player_id")
    )
    return result
