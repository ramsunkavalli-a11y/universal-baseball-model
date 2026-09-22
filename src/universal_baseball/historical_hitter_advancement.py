"""Chronology-safe non-steal baserunning outcome helpers."""

from __future__ import annotations

import polars as pl


def advancement_war_by_player_origin(
    advancement: pl.DataFrame,
    *,
    origin: int,
    horizon: int,
    runs_per_win: float,
) -> pl.DataFrame:
    """Return future Savant non-steal advancement WAR by player."""

    required = {"season", "player_id", "runner_runs_xb"}
    if missing := sorted(required - set(advancement.columns)):
        raise ValueError(f"advancement outcomes missing fields: {missing}")
    if horizon <= 0 or runs_per_win <= 0:
        raise ValueError("horizon and runs_per_win must be positive")
    return (
        advancement.filter(pl.col("season").is_between(origin + 1, origin + horizon))
        .with_columns(
            (
                pl.col("runner_runs_xb")
                * pl.when(pl.col("season") == 2020).then(2.7).otherwise(1.0)
            ).alias("advancement_runs")
        )
        .group_by("player_id")
        .agg(pl.col("advancement_runs").sum().alias("later_advancement_runs"))
        .with_columns(
            (pl.col("later_advancement_runs") / runs_per_win).alias(
                "later_advancement_war"
            )
        )
        .sort("player_id")
    )
