"""Frozen, chronology-safe Hitter v2 evaluation primitives.

This module defines evaluation geometry and rolling-origin slices only. It does
not fit a batting model, inspect a protected confirmation season, or decide a
promotion gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence

import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


NEUTRAL_POOL_SEASONS = (2016, 2017, 2018, 2019, 2020)
NEUTRAL_WOBA = 0.3188
NEUTRAL_WOBA_SCALE = 1.193
NEUTRAL_WOBA_WEIGHTS = {
    "UBB": 0.6926,
    "IBB": 0.0,
    "HBP": 0.7222,
    "K": 0.0,
    "HR": 1.989,
    "3B": 1.5572,
    "2B": 1.2352,
    "1B": 0.8776,
    "ROE": 0.0,
    "FC_REACH": 0.0,
    "SF": 0.0,
    "MULTI_OUT": 0.0,
    "OTHER_OUT": 0.0,
    "SH_OR_SPECIAL": 0.0,
}


@dataclass(frozen=True, slots=True)
class RollingOriginFold:
    fold_id: str
    predictor_cutoff_season: int
    target_season: int


ROLLING_ORIGIN_FOLDS = (
    RollingOriginFold("V2022", 2021, 2022),
    RollingOriginFold("V2023", 2022, 2023),
    RollingOriginFold("V2024", 2023, 2024),
)


def validate_probability_vector(
    probabilities: Mapping[str, float],
    *,
    tolerance: float = 1e-12,
) -> None:
    """Validate one exhaustive Hitter v2 talent-outcome simplex."""

    expected = set(HITTER_TALENT_OUTCOMES)
    observed = set(probabilities)
    if observed != expected:
        raise ValueError(
            f"probability outcomes differ: missing={sorted(expected - observed)}, "
            f"extra={sorted(observed - expected)}"
        )
    values = [float(probabilities[outcome]) for outcome in HITTER_TALENT_OUTCOMES]
    if any(not isfinite(value) for value in values):
        raise ValueError("probabilities must be finite")
    if any(value < 0.0 for value in values):
        raise ValueError("probabilities must be nonnegative")
    if abs(sum(values) - 1.0) > tolerance:
        raise ValueError("probabilities must sum to one")


def probability_vector_to_woba(probabilities: Mapping[str, float]) -> float:
    """Apply the frozen 2016-2020 neutral wOBA weights to one simplex."""

    validate_probability_vector(probabilities)
    return sum(
        float(probabilities[outcome]) * NEUTRAL_WOBA_WEIGHTS[outcome]
        for outcome in HITTER_TALENT_OUTCOMES
    )


def woba_to_neutral_batting_runs_per_600(woba: float) -> float:
    """Convert neutral wOBA to FanGraphs-style runs above average per 600 PA."""

    value = float(woba)
    if not isfinite(value):
        raise ValueError("wOBA must be finite")
    return ((value - NEUTRAL_WOBA) / NEUTRAL_WOBA_SCALE) * 600.0


def move_probability_mass(
    probabilities: Mapping[str, float],
    *,
    source: str,
    destination: str,
    mass: float,
) -> dict[str, float]:
    """Return a coherent simplex after moving probability mass."""

    validate_probability_vector(probabilities)
    amount = float(mass)
    if not isfinite(amount) or amount <= 0.0:
        raise ValueError("moved probability mass must be finite and positive")
    if source == destination:
        raise ValueError("source and destination outcomes must differ")
    if source not in probabilities or destination not in probabilities:
        raise ValueError("source and destination must be modeled outcomes")
    if amount > float(probabilities[source]):
        raise ValueError("cannot move more mass than the source contains")
    result = {key: float(value) for key, value in probabilities.items()}
    result[source] -= amount
    result[destination] += amount
    validate_probability_vector(result)
    return result


def eligible_player_seasons(frame: pl.DataFrame) -> pl.DataFrame:
    """Return accepted positive-denominator rows without consulting a target cohort."""

    required = {
        "season",
        "league_id",
        "player_id",
        "level_group",
        "hitter_talent_pa",
        "modeling_eligible",
        *HITTER_TALENT_OUTCOMES,
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"fold source is missing columns: {missing}")
    eligible = frame.filter(
        pl.col("modeling_eligible") & (pl.col("hitter_talent_pa") > 0)
    ).sort(["season", "league_id", "player_id"])
    duplicate = (
        eligible.group_by(["season", "league_id", "player_id"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate.is_empty():
        raise ValueError("eligible player-season keys are not unique")
    return eligible


def rolling_origin_slices(
    frame: pl.DataFrame,
    fold: RollingOriginFold,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build a full-population training slice and a separate target slice."""

    eligible = eligible_player_seasons(frame)
    training = eligible.filter(pl.col("season") <= fold.predictor_cutoff_season)
    target = eligible.filter(pl.col("season") == fold.target_season)
    if training.is_empty() or target.is_empty():
        raise ValueError(f"{fold.fold_id} has an empty training or target slice")
    if int(training["season"].max()) > fold.predictor_cutoff_season:
        raise ValueError(f"{fold.fold_id} training crosses its predictor cutoff")
    if set(int(value) for value in target["season"].unique().to_list()) != {
        fold.target_season
    }:
        raise ValueError(f"{fold.fold_id} target contains another season")
    return training, target


def aggregate_target_players(target: pl.DataFrame) -> pl.DataFrame:
    """Aggregate target outcomes to one player while retaining primary level."""

    eligible = eligible_player_seasons(target)
    seasons = eligible["season"].unique().to_list()
    if len(seasons) != 1:
        raise ValueError("target-player aggregation requires exactly one season")
    primary = (
        eligible.sort(
            ["player_id", "hitter_talent_pa", "level_group", "league_id"],
            descending=[False, True, False, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select(
            "player_id",
            pl.col("league_id").alias("primary_target_league_id"),
            pl.col("level_group").alias("primary_target_level_group"),
        )
    )
    sums: Sequence[str] = (*HITTER_TALENT_OUTCOMES, "hitter_talent_pa")
    players = (
        eligible.group_by(["season", "player_id"])
        .agg(
            *[pl.col(column).sum().alias(column) for column in sums],
            pl.col("league_id").n_unique().alias("target_league_count"),
            pl.col("level_group").n_unique().alias("target_level_count"),
        )
        .join(primary, on="player_id", how="left", validate="1:1")
        .sort("player_id")
    )
    total = pl.sum_horizontal(*[pl.col(value) for value in HITTER_TALENT_OUTCOMES])
    if players.filter(total != pl.col("hitter_talent_pa")).height:
        raise ValueError("target-player outcomes do not reconcile to hitter-talent PA")
    return players


def build_forecast_population(training: pl.DataFrame) -> pl.DataFrame:
    """Define forecast eligibility exclusively from pre-cutoff evidence."""

    eligible = eligible_player_seasons(training)
    return (
        eligible.group_by("player_id")
        .agg(
            pl.col("season").min().alias("first_evidence_season"),
            pl.col("season").max().alias("last_evidence_season"),
            pl.col("hitter_talent_pa").sum().alias("prior_hitter_talent_pa"),
            pl.col("league_id").n_unique().alias("prior_league_count"),
            pl.col("level_group").n_unique().alias("prior_level_count"),
        )
        .sort("player_id")
    )
