"""Historical hitter batting-plus-replacement paths aligned to workloads."""

from __future__ import annotations

import math

import polars as pl

from universal_baseball.conditional_war_rates import HITTER_WAR_ALLOCATION
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)


HITTER_EVENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")


def build_historical_hitter_performance_paths(
    annual_paths: pl.DataFrame,
    hitting: pl.DataFrame,
    *,
    runs_per_win: float,
    shortened_2020_scale: float = 2.7,
) -> pl.DataFrame:
    """Attach annual batting-plus-replacement WAR to complete hitter paths.

    Defense, baserunning and positional adjustment are deliberately excluded. Those
    components are not present at the same historical player-season grain and must
    not be inferred from current player data.
    """

    if not math.isfinite(runs_per_win) or runs_per_win <= 0:
        raise ValueError("runs_per_win must be finite and positive")
    if not math.isfinite(shortened_2020_scale) or shortened_2020_scale <= 0:
        raise ValueError("shortened_2020_scale must be finite and positive")
    path_required = {
        "path_player_id",
        "player_type",
        "outcome_tier_v2",
        "career_role",
        "path_year",
        "source_season",
        "adjusted_workload",
        "annual_role",
    }
    hitting_required = {
        "season",
        "player_id",
        "batting_plate_appearances",
        "batting_hits",
        "batting_doubles",
        "batting_triples",
        "batting_home_runs",
        "batting_base_on_balls",
        "batting_intentional_walks",
        "batting_hit_by_pitch",
    }
    if missing := sorted(path_required - set(annual_paths.columns)):
        raise ValueError(f"annual paths missing fields: {missing}")
    if missing := sorted(hitting_required - set(hitting.columns)):
        raise ValueError(f"hitting outcomes missing fields: {missing}")

    outcomes = (
        hitting.group_by("season", "player_id")
        .agg(*(pl.col(column).sum() for column in hitting_required - {"season", "player_id"}))
        .with_columns(
            (pl.col("batting_base_on_balls") - pl.col("batting_intentional_walks")).alias("ubb"),
            pl.col("batting_hit_by_pitch").alias("hbp"),
            (
                pl.col("batting_hits")
                - pl.col("batting_doubles")
                - pl.col("batting_triples")
                - pl.col("batting_home_runs")
            ).alias("single"),
            pl.col("batting_doubles").alias("double"),
            pl.col("batting_triples").alias("triple"),
            pl.col("batting_home_runs").alias("hr"),
        )
        .with_columns(
            (
                pl.col("batting_plate_appearances")
                - pl.sum_horizontal(*HITTER_EVENTS[:-1])
            ).alias("other"),
            pl.when(pl.col("season") == 2020)
            .then(pl.col("batting_plate_appearances") * shortened_2020_scale)
            .otherwise(pl.col("batting_plate_appearances"))
            .alias("environment_adjusted_pa"),
        )
    )
    if outcomes.filter(
        pl.any_horizontal(*(pl.col(event) < 0 for event in HITTER_EVENTS))
        | (pl.col("batting_intentional_walks") > pl.col("batting_base_on_balls"))
    ).height:
        raise ValueError("hitter outcome event accounting is invalid")

    environment = outcomes.group_by("season").agg(
        pl.col("environment_adjusted_pa").sum().alias("league_pa"),
        pl.col("batting_plate_appearances").sum().alias("unadjusted_league_pa"),
        *(pl.col(event).sum().alias(f"league_{event}") for event in HITTER_EVENTS),
    )
    weights = {
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "single": NEUTRAL_WOBA_WEIGHTS["1B"],
        "double": NEUTRAL_WOBA_WEIGHTS["2B"],
        "triple": NEUTRAL_WOBA_WEIGHTS["3B"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": 0.0,
    }
    environment = environment.with_columns(
        sum(
            pl.col(f"league_{event}")
            / pl.col("unadjusted_league_pa")
            * weight
            for event, weight in weights.items()
        ).alias("league_woba"),
        (
            HITTER_WAR_ALLOCATION
            * runs_per_win
            * 600.0
            / pl.col("league_pa")
        ).alias("replacement_runs_per_600"),
    )
    scored = (
        outcomes.join(environment, on="season", validate="m:1")
        .with_columns(
            (
                sum(pl.col(event) * weight for event, weight in weights.items())
                / pl.col("batting_plate_appearances")
            ).alias("observed_woba")
        )
        .with_columns(
            (
                (pl.col("observed_woba") - pl.col("league_woba"))
                * 600.0
                / NEUTRAL_WOBA_SCALE
            ).alias("batting_runs_above_average_per_600")
        )
        .with_columns(
            (
                (
                    pl.col("batting_runs_above_average_per_600")
                    + pl.col("replacement_runs_per_600")
                )
                / runs_per_win
            ).alias("observed_conditional_war_per_600")
        )
    )
    paths = annual_paths.filter(pl.col("player_type") == "hitter").join(
        scored.select(
            pl.col("season").alias("source_season"),
            pl.col("player_id").alias("path_player_id"),
            "batting_plate_appearances",
            "observed_woba",
            "batting_runs_above_average_per_600",
            "replacement_runs_per_600",
            "observed_conditional_war_per_600",
        ),
        on=["path_player_id", "source_season"],
        how="left",
        validate="m:1",
    )
    if paths.filter(
        (pl.col("adjusted_workload") > 0)
        & pl.col("observed_conditional_war_per_600").is_null()
    ).height:
        raise ValueError("active hitter paths lack matching MLB component outcomes")
    return paths.with_columns(
        pl.when(pl.col("adjusted_workload") > 0)
        .then(
            pl.col("adjusted_workload")
            * pl.col("observed_conditional_war_per_600")
            / 600.0
        )
        .otherwise(0.0)
        .alias("observed_component_war")
    ).sort("path_player_id", "path_year")
