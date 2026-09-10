"""Historical pitcher component-WAR paths aligned to career workload paths."""

from __future__ import annotations

import math

import polars as pl

from universal_baseball.conditional_war_rates import PITCHER_WAR_ALLOCATION
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)


def build_historical_pitcher_performance_paths(
    annual_paths: pl.DataFrame,
    pitching: pl.DataFrame,
    *,
    runs_per_win: float,
    shortened_2020_scale: float = 2.7,
) -> pl.DataFrame:
    """Attach comparable annual pitcher component WAR to complete career paths."""

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
    pitching_required = {
        "season",
        "player_id",
        "pitching_bf",
        "pitching_so",
        "pitching_ubb",
        "pitching_hbp",
        "pitching_hr",
    }
    if missing := sorted(path_required - set(annual_paths.columns)):
        raise ValueError(f"annual paths missing fields: {missing}")
    if missing := sorted(pitching_required - set(pitching.columns)):
        raise ValueError(f"pitching outcomes missing fields: {missing}")

    outcomes = (
        pitching.group_by(["season", "player_id"])
        .agg(
            pl.col("pitching_bf").sum(),
            pl.col("pitching_so").sum(),
            pl.col("pitching_ubb").sum(),
            pl.col("pitching_hbp").sum(),
            pl.col("pitching_hr").sum(),
        )
        .with_columns(
            pl.when(pl.col("season") == 2020)
            .then(pl.col("pitching_bf") * shortened_2020_scale)
            .otherwise(pl.col("pitching_bf"))
            .alias("environment_adjusted_bf")
        )
    )
    environment = (
        outcomes.group_by("season")
        .agg(
            pl.col("environment_adjusted_bf").sum().alias("league_bf"),
            pl.col("pitching_bf").sum().alias("unadjusted_league_bf"),
            pl.col("pitching_so").sum(),
            pl.col("pitching_ubb").sum(),
            pl.col("pitching_hbp").sum(),
            pl.col("pitching_hr").sum(),
        )
        .with_columns(
            (pl.col("pitching_so") / pl.col("unadjusted_league_bf")).alias(
                "league_so_rate"
            ),
            (pl.col("pitching_ubb") / pl.col("unadjusted_league_bf")).alias(
                "league_ubb_rate"
            ),
            (pl.col("pitching_hbp") / pl.col("unadjusted_league_bf")).alias(
                "league_hbp_rate"
            ),
            (pl.col("pitching_hr") / pl.col("unadjusted_league_bf")).alias(
                "league_hr_rate"
            ),
        )
        .with_columns(
            (
                1.0
                - pl.col("league_so_rate")
                - pl.col("league_ubb_rate")
                - pl.col("league_hbp_rate")
                - pl.col("league_hr_rate")
            ).alias("league_other_rate")
        )
        .with_columns(
            (
                (
                    0.3188
                    - pl.col("league_ubb_rate") * NEUTRAL_WOBA_WEIGHTS["UBB"]
                    - pl.col("league_hbp_rate") * NEUTRAL_WOBA_WEIGHTS["HBP"]
                    - pl.col("league_hr_rate") * NEUTRAL_WOBA_WEIGHTS["HR"]
                )
                / pl.col("league_other_rate")
            ).alias("other_weight"),
            (PITCHER_WAR_ALLOCATION * runs_per_win * 800.0 / pl.col("league_bf")).alias(
                "replacement_runs_per_800"
            ),
        )
    )
    scored = (
        outcomes.join(environment, on="season", validate="m:1")
        .with_columns(
            (
                pl.col("pitching_bf")
                - pl.col("pitching_so")
                - pl.col("pitching_ubb")
                - pl.col("pitching_hbp")
                - pl.col("pitching_hr")
            ).alias("pitching_other")
        )
        .with_columns(
            (
                (
                    pl.col("pitching_ubb") * NEUTRAL_WOBA_WEIGHTS["UBB"]
                    + pl.col("pitching_hbp") * NEUTRAL_WOBA_WEIGHTS["HBP"]
                    + pl.col("pitching_hr") * NEUTRAL_WOBA_WEIGHTS["HR"]
                    + pl.col("pitching_other") * pl.col("other_weight")
                )
                / pl.col("pitching_bf")
            ).alias("observed_woba_allowed")
        )
        .with_columns(
            (
                -(pl.col("observed_woba_allowed") - 0.3188) * 800.0 / NEUTRAL_WOBA_SCALE
            ).alias("pitching_runs_above_average_per_800")
        )
        .with_columns(
            (
                (
                    pl.col("pitching_runs_above_average_per_800")
                    + pl.col("replacement_runs_per_800")
                )
                / runs_per_win
            ).alias("observed_conditional_war_per_800")
        )
    )

    paths = annual_paths.filter(pl.col("player_type") == "pitcher").join(
        scored.select(
            pl.col("season").alias("source_season"),
            pl.col("player_id").alias("path_player_id"),
            "pitching_bf",
            "observed_woba_allowed",
            "pitching_runs_above_average_per_800",
            "replacement_runs_per_800",
            "observed_conditional_war_per_800",
        ),
        on=["path_player_id", "source_season"],
        how="left",
        validate="m:1",
    )
    missing_active = paths.filter(
        (pl.col("adjusted_workload") > 0)
        & pl.col("observed_conditional_war_per_800").is_null()
    )
    if missing_active.height:
        raise ValueError("active pitcher paths lack matching MLB component outcomes")
    return paths.with_columns(
        pl.when(pl.col("adjusted_workload") > 0)
        .then(
            pl.col("adjusted_workload")
            * pl.col("observed_conditional_war_per_800")
            / 800.0
        )
        .otherwise(0.0)
        .alias("observed_component_war")
    ).sort(["path_player_id", "path_year"])
