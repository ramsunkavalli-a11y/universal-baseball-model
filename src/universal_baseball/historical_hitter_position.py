"""Historical hitter positional value from official fielding usage."""

from __future__ import annotations

import polars as pl

from universal_baseball.player_value_positional_adjustment import (
    DEFENSIVE_POSITIONS,
    FULL_SEASON_DEFENSIVE_OUTS,
    FULL_SEASON_DH_ROLE_EVENTS,
    POSITIONAL_RUNS_PER_162,
)


def origin_position_profiles(fielding: pl.DataFrame, *, season: int) -> pl.DataFrame:
    """Choose the position with the most equivalent defensive-game exposure."""

    required = {
        "season",
        "player_id",
        "position_abbreviation",
        "games_started",
        "fielding_outs",
    }
    if missing := sorted(required - set(fielding.columns)):
        raise ValueError(f"fielding origins missing fields: {missing}")
    positions = (*DEFENSIVE_POSITIONS, "DH")
    return (
        fielding.filter(
            (pl.col("season") == season)
            & pl.col("position_abbreviation").is_in(positions)
        )
        .with_columns(
            pl.when(pl.col("position_abbreviation") == "DH")
            .then(pl.col("games_started") * 27)
            .otherwise(pl.col("fielding_outs"))
            .alias("role_exposure")
        )
        .filter(pl.col("role_exposure") > 0)
        .group_by("player_id", "position_abbreviation")
        .agg(pl.col("role_exposure").sum())
        .sort(
            ["player_id", "role_exposure", "position_abbreviation"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select(
            "player_id",
            pl.col("position_abbreviation").alias("origin_position"),
            pl.col("role_exposure").alias("origin_position_exposure"),
        )
    )


def position_war_by_player_origin(
    fielding: pl.DataFrame,
    *,
    origin: int,
    horizon: int,
    runs_per_win: float,
) -> pl.DataFrame:
    """Return actual future positional WAR under the frozen transparent schedule."""

    required = {
        "season",
        "player_id",
        "position_abbreviation",
        "games_started",
        "fielding_outs",
    }
    if missing := sorted(required - set(fielding.columns)):
        raise ValueError(f"fielding outcomes missing fields: {missing}")
    if horizon <= 0 or runs_per_win <= 0:
        raise ValueError("horizon and runs_per_win must be positive")
    rows = fielding.filter(
        pl.col("season").is_between(origin + 1, origin + horizon)
    ).with_columns(
        pl.when(pl.col("season") == 2020)
        .then(2.7)
        .otherwise(1.0)
        .alias("season_scale")
    )
    defensive = rows.filter(
        pl.col("position_abbreviation").is_in(list(DEFENSIVE_POSITIONS))
    ).with_columns(
        (
            pl.col("fielding_outs")
            * pl.col("season_scale")
            / FULL_SEASON_DEFENSIVE_OUTS
            * pl.col("position_abbreviation").replace_strict(
                dict(POSITIONAL_RUNS_PER_162), return_dtype=pl.Float64
            )
        ).alias("position_runs")
    )
    designated_hitter = rows.filter(
        pl.col("position_abbreviation") == "DH"
    ).with_columns(
        (
            pl.col("games_started")
            * pl.col("season_scale")
            / FULL_SEASON_DH_ROLE_EVENTS
            * POSITIONAL_RUNS_PER_162["DH"]
        ).alias("position_runs")
    )
    return (
        pl.concat(
            [
                defensive.select("player_id", "position_runs"),
                designated_hitter.select("player_id", "position_runs"),
            ]
        )
        .group_by("player_id")
        .agg(pl.col("position_runs").sum().alias("later_position_runs"))
        .with_columns(
            (pl.col("later_position_runs") / runs_per_win).alias(
                "later_position_war"
            )
        )
        .sort("player_id")
    )
