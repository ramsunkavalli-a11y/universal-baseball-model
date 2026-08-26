"""Target-free support accounting for the Hitter v2 historical bridge."""

from __future__ import annotations

import polars as pl


LEVEL_ORDER = {
    "ROOKIE_COMPLEX": 0,
    "SINGLE_A": 1,
    "HIGH_A": 2,
    "AA": 3,
    "AAA": 4,
    "MLB": 5,
}


def canonicalize_stints(frame: pl.DataFrame) -> pl.DataFrame:
    """Validate and aggregate source rows to one player-season-level stint."""

    required = {"season", "player_id", "level_group", "pa", "source"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"missing bridge columns: {missing}")
    if frame.select(pl.col("player_id").is_null().any()).item():
        raise ValueError("bridge identity cannot be null")
    unknown = sorted(
        set(frame.get_column("level_group").unique().to_list()) - set(LEVEL_ORDER)
    )
    if unknown:
        raise ValueError(f"unknown bridge levels: {unknown}")
    if frame.select((pl.col("pa") < 0).any()).item():
        raise ValueError("bridge PA cannot be negative")
    return (
        frame.group_by("season", "player_id", "level_group", "source")
        .agg(pl.col("pa").sum())
        .sort("season", "player_id", "level_group", "source")
    )


def player_seasons(stints: pl.DataFrame) -> pl.DataFrame:
    """Return total exposure and a level-set label for each player-season."""

    return (
        stints.group_by("season", "player_id")
        .agg(
            pl.col("pa").sum().alias("total_pa"),
            pl.col("level_group").n_unique().alias("level_count"),
            pl.col("level_group").sort_by("level_group").implode().alias("levels"),
        )
        .with_columns(
            pl.when(pl.col("level_count") == 1)
            .then(pl.col("levels").list.first())
            .otherwise(pl.lit("MULTI_STINT"))
            .alias("level_label")
        )
        .sort("season", "player_id")
    )


def evidence_band(pa: int) -> str:
    if pa < 100:
        return "LT100"
    if pa < 300:
        return "100_299"
    if pa < 600:
        return "300_599"
    return "600_PLUS"


def transition_label(origin_level: str, destination_level: str) -> str:
    if "MULTI_STINT" in {origin_level, destination_level}:
        return "AMBIGUOUS"
    delta = LEVEL_ORDER[destination_level] - LEVEL_ORDER[origin_level]
    if delta > 0:
        return "PROMOTION"
    if delta < 0:
        return "DEMOTION"
    return "SAME"


def matched_pair(
    player_season_frame: pl.DataFrame,
    *,
    origin_season: int,
    destination_season: int,
    comparison: str,
) -> pl.DataFrame:
    """Build one target-free same-player bridge comparison."""

    origin = player_season_frame.filter(pl.col("season") == origin_season).select(
        "player_id",
        pl.col("total_pa").alias("origin_pa"),
        pl.col("level_label").alias("origin_level"),
    )
    destination = player_season_frame.filter(
        pl.col("season") == destination_season
    ).select(
        "player_id",
        pl.col("total_pa").alias("destination_pa"),
        pl.col("level_label").alias("destination_level"),
    )
    matched = origin.join(destination, on="player_id", how="inner")
    return matched.with_columns(
        pl.lit(comparison).alias("comparison"),
        pl.col("origin_pa")
        .map_elements(evidence_band, return_dtype=pl.String)
        .alias("origin_evidence_band"),
        pl.struct("origin_level", "destination_level")
        .map_elements(
            lambda row: transition_label(
                row["origin_level"], row["destination_level"]
            ),
            return_dtype=pl.String,
        )
        .alias("transition"),
    ).select(
        "comparison",
        "player_id",
        "origin_pa",
        "destination_pa",
        "origin_level",
        "destination_level",
        "origin_evidence_band",
        "transition",
    )
