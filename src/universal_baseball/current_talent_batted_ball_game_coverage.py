"""Certified-game coverage diagnostics for tracked Savant source evidence.

A tracked-only Savant response can be nearly complete among returned rows while
omitting entire untracked games. This module therefore uses the already-certified
player-game environment as the denominator and asks only whether each certified
game appears anywhere in the returned source response.

This is a source-capability diagnostic, not a talent feature or eligibility rule.
"""

from __future__ import annotations

from typing import Any

import polars as pl


CERTIFIED_GAME_COVERAGE_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "league_id": pl.Int64,
    "level_group": pl.String,
    "certified_game_count": pl.Int64,
    "tracked_game_count": pl.Int64,
    "tracked_game_share": pl.Float64,
}


def _integer_like(column: str, alias: str) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias)
    )


def build_certified_game_tracking_coverage(
    raw_savant: pl.DataFrame,
    certified_player_games: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Compare returned tracked-source games with the certified game universe.

    ``certified_player_games`` may contain many player rows per game. Every game
    must collapse to exactly one season/league/level environment. A game counts as
    tracked when its ``game_pk`` appears anywhere in the returned Savant response;
    this intentionally does not depend on EV/LA completeness or player matching.
    """

    if "game_pk" not in raw_savant.columns:
        raise ValueError("tracked Savant source missing game_pk for game coverage")
    required = {"game_pk", "season", "league_id", "level_group"}
    missing = sorted(required - set(certified_player_games.columns))
    if missing:
        raise ValueError(f"certified player-game evidence missing coverage fields: {missing}")

    certified_games = certified_player_games.select(
        pl.col("game_pk").cast(pl.Int64, strict=False),
        pl.col("season").cast(pl.Int64, strict=False),
        pl.col("league_id").cast(pl.Int64, strict=False),
        pl.col("level_group").cast(pl.String),
    ).drop_nulls(["game_pk", "season", "league_id", "level_group"])

    if certified_games.is_empty():
        raise ValueError("certified player-game evidence contains no usable games")

    ambiguous = (
        certified_games.group_by("game_pk")
        .agg(pl.struct(["season", "league_id", "level_group"]).n_unique().alias("environment_count"))
        .filter(pl.col("environment_count") != 1)
    )
    if not ambiguous.is_empty():
        raise ValueError("certified game universe has ambiguous game environment")

    game_universe = certified_games.unique(
        subset=["game_pk", "season", "league_id", "level_group"], keep="first"
    )
    returned_games = (
        raw_savant.select(_integer_like("game_pk", "game_pk"))
        .drop_nulls("game_pk")
        .unique()
    )

    matched_games = returned_games.join(game_universe, on="game_pk", how="inner")

    denominator = (
        game_universe.group_by(["season", "league_id", "level_group"])
        .agg(pl.col("game_pk").n_unique().cast(pl.Int64).alias("certified_game_count"))
    )
    numerator = (
        matched_games.group_by(["season", "league_id", "level_group"])
        .agg(pl.col("game_pk").n_unique().cast(pl.Int64).alias("tracked_game_count"))
    )
    by_environment = (
        denominator.join(
            numerator,
            on=["season", "league_id", "level_group"],
            how="left",
        )
        .with_columns(pl.col("tracked_game_count").fill_null(0).cast(pl.Int64))
        .with_columns(
            (
                pl.col("tracked_game_count").cast(pl.Float64)
                / pl.col("certified_game_count").cast(pl.Float64)
            ).alias("tracked_game_share")
        )
        .select(*CERTIFIED_GAME_COVERAGE_SCHEMA)
        .cast(CERTIFIED_GAME_COVERAGE_SCHEMA, strict=True)
        .sort(["season", "level_group", "league_id"])
    )

    certified_count = int(game_universe.get_column("game_pk").n_unique())
    returned_count = int(returned_games.get_column("game_pk").n_unique())
    matched_count = int(matched_games.get_column("game_pk").n_unique())
    metrics: dict[str, Any] = {
        "certified_game_count": certified_count,
        "returned_source_game_count": returned_count,
        "tracked_game_count": matched_count,
        "unmatched_source_game_count": returned_count - matched_count,
        "tracked_game_share": matched_count / certified_count if certified_count else None,
    }
    return by_environment, metrics
