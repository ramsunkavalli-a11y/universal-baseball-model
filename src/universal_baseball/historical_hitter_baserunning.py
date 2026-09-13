"""Historical centered stolen-base value for prospect outcome audits."""

from __future__ import annotations

import polars as pl

from universal_baseball.player_value_baserunning_runs import BaserunningReference


def steal_war_by_player_origin(
    hitting: pl.DataFrame,
    *,
    origin: int,
    horizon: int,
    runs_per_win: float,
    reference: BaserunningReference,
) -> pl.DataFrame:
    """Return future wSB-style WAR translated to one fixed MLB run environment."""

    required = {
        "season",
        "player_id",
        "batting_hits",
        "batting_doubles",
        "batting_triples",
        "batting_home_runs",
        "batting_base_on_balls",
        "batting_intentional_walks",
        "batting_hit_by_pitch",
        "batting_stolen_bases",
        "batting_caught_stealing",
    }
    if missing := sorted(required - set(hitting.columns)):
        raise ValueError(f"hitting outcomes missing steal fields: {missing}")
    if horizon <= 0 or runs_per_win <= 0:
        raise ValueError("horizon and runs_per_win must be positive")
    outcomes = (
        hitting.filter(pl.col("season").is_between(origin + 1, origin + horizon))
        .group_by("season", "player_id")
        .agg(*(pl.col(column).sum() for column in required - {"season", "player_id"}))
        .with_columns(
            (
                pl.col("batting_hits")
                - pl.col("batting_doubles")
                - pl.col("batting_triples")
                - pl.col("batting_home_runs")
                + pl.col("batting_base_on_balls")
                + pl.col("batting_hit_by_pitch")
                - pl.col("batting_intentional_walks")
            ).alias("steal_opportunities")
        )
    )
    environment = outcomes.group_by("season").agg(
        pl.col("steal_opportunities").sum().alias("league_opportunities"),
        pl.col("batting_stolen_bases").sum().alias("league_sb"),
        pl.col("batting_caught_stealing").sum().alias("league_cs"),
    ).with_columns(
        (
            (
                pl.col("league_sb") * reference.run_value_stolen_base
                + pl.col("league_cs") * reference.run_value_caught_stealing
            )
            / pl.col("league_opportunities")
        ).alias("league_runs_per_opportunity")
    )
    return (
        outcomes.join(environment, on="season", validate="m:1")
        .with_columns(
            (
                (
                    pl.col("batting_stolen_bases")
                    * reference.run_value_stolen_base
                    + pl.col("batting_caught_stealing")
                    * reference.run_value_caught_stealing
                    - pl.col("steal_opportunities")
                    * pl.col("league_runs_per_opportunity")
                )
                * pl.when(pl.col("season") == 2020).then(2.7).otherwise(1.0)
            ).alias("steal_runs")
        )
        .group_by("player_id")
        .agg(pl.col("steal_runs").sum().alias("later_steal_runs"))
        .with_columns(
            (pl.col("later_steal_runs") / runs_per_win).alias("later_steal_war")
        )
        .sort("player_id")
    )
