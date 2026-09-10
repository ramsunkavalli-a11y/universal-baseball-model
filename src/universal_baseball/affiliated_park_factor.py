"""Partially pooled affiliated park factors from home/road game results."""

from __future__ import annotations

from math import sqrt

import polars as pl


def build_venue_season_observations(games: pl.DataFrame) -> pl.DataFrame:
    """Compare each team/venue home environment with that team's road games."""

    required = {
        "season", "sport_id", "venue_id", "home_team_id", "away_team_id",
        "home_score", "away_score", "scheduled_innings",
    }
    if missing := sorted(required - set(games.columns)):
        raise ValueError(f"park-factor games missing fields: {missing}")
    scored = games.filter(pl.col("scheduled_innings") > 0).with_columns(
        (
            (pl.col("home_score") + pl.col("away_score")) * 9.0
            / pl.col("scheduled_innings")
        ).alias("total_runs_per_nine")
    )
    road = scored.group_by("season", "sport_id", "away_team_id").agg(
        pl.len().alias("road_games"),
        pl.col("total_runs_per_nine").mean().alias("road_runs_per_nine"),
    ).rename({"away_team_id": "home_team_id"})
    return (
        scored.group_by("season", "sport_id", "home_team_id", "venue_id")
        .agg(
            pl.len().alias("home_games"),
            pl.col("total_runs_per_nine").mean().alias("home_runs_per_nine"),
        )
        .join(
            road, on=["season", "sport_id", "home_team_id"],
            how="inner", validate="m:1",
        )
        .filter(
            (pl.col("home_games") >= 10)
            & (pl.col("road_games") >= 20)
            & (pl.col("road_runs_per_nine") > 0)
        )
        .with_columns(
            (pl.col("home_runs_per_nine") / pl.col("road_runs_per_nine"))
            .alias("observed_park_factor")
        )
        .sort(["season", "sport_id", "venue_id", "home_team_id"])
    )


def fit_park_factors(
    observations: pl.DataFrame, *, through_season: int, prior_games: float
) -> pl.DataFrame:
    if prior_games < 0:
        raise ValueError("prior_games cannot be negative")
    training = observations.filter(pl.col("season") <= through_season)
    return (
        training.group_by("venue_id")
        .agg(
            pl.col("home_games").sum().cast(pl.Float64).alias("training_home_games"),
            (pl.col("observed_park_factor") * pl.col("home_games"))
            .sum().alias("weighted_factor_sum"),
            pl.col("season").n_unique().alias("training_seasons"),
        )
        .with_columns(
            (
                (pl.col("weighted_factor_sum") + prior_games)
                / (pl.col("training_home_games") + prior_games)
            ).alias("predicted_park_factor")
        )
        .select(
            "venue_id", "training_home_games", "training_seasons",
            "predicted_park_factor",
        )
        .sort("venue_id")
    )


def score_park_factors(
    observations: pl.DataFrame, factors: pl.DataFrame, *, season: int
) -> dict[str, float | int]:
    evaluated = (
        observations.filter(pl.col("season") == season)
        .join(factors, on="venue_id", how="left", validate="m:1")
        .with_columns(pl.col("predicted_park_factor").fill_null(1.0))
    )
    if evaluated.is_empty():
        raise ValueError(f"no park-factor observations for {season}")
    weight = evaluated.get_column("home_games")
    observed = evaluated.get_column("observed_park_factor")
    predicted = evaluated.get_column("predicted_park_factor")
    total_weight = float(weight.sum())

    def mae(values: pl.Series) -> float:
        return float((values.abs() * weight).sum() / total_weight)

    def rmse(values: pl.Series) -> float:
        return sqrt(float(((values ** 2) * weight).sum() / total_weight))

    baseline_error = observed - 1.0
    candidate_error = observed - predicted
    return {
        "season": season,
        "venue_team_cells": evaluated.height,
        "venues": evaluated.get_column("venue_id").n_unique(),
        "games": int(weight.sum()),
        "baseline_mae": mae(baseline_error),
        "candidate_mae": mae(candidate_error),
        "baseline_rmse": rmse(baseline_error),
        "candidate_rmse": rmse(candidate_error),
        "observed_mean": float((observed * weight).sum() / total_weight),
        "predicted_mean": float((predicted * weight).sum() / total_weight),
    }
