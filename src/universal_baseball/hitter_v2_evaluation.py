"""Frozen, chronology-safe Hitter v2 evaluation primitives.

This module defines evaluation geometry and rolling-origin slices only. It does
not fit a batting model, inspect a protected confirmation season, or decide a
promotion gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence

import numpy as np
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
SCORING_PROBABILITY_FLOOR = 1e-15
NESTED_COMPONENT_CHILD_LEAVES = {
    "plate_appearance": (("K",), tuple(o for o in HITTER_TALENT_OUTCOMES if o != "K")),
    "non_k": (("UBB",), tuple(o for o in HITTER_TALENT_OUTCOMES if o not in {"K", "UBB"})),
    "non_k_non_ubb": (("HBP",), ("HR", "3B", "2B", "1B", "ROE", "FC_REACH", "SF", "MULTI_OUT", "OTHER_OUT")),
    "contact": (("HR",), ("3B", "2B", "1B", "ROE", "FC_REACH", "SF", "MULTI_OUT", "OTHER_OUT")),
    "non_hr_contact": (("3B", "2B", "1B", "ROE", "FC_REACH"), ("SF", "MULTI_OUT", "OTHER_OUT")),
    "reach": (("3B", "2B", "1B"), ("ROE", "FC_REACH")),
    "hit_in_play": (("1B",), ("2B",), ("3B",)),
    "non_hit_reach": (("ROE",), ("FC_REACH",)),
    "non_reach": (("SF",), ("MULTI_OUT",), ("OTHER_OUT",)),
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


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sum(values * weights) / np.sum(weights))


def _weighted_rmse(errors: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sqrt(_weighted_mean(errors**2, weights)))


def _weighted_correlation(
    left: np.ndarray,
    right: np.ndarray,
    weights: np.ndarray,
) -> float | None:
    left_centered = left - _weighted_mean(left, weights)
    right_centered = right - _weighted_mean(right, weights)
    denominator = np.sqrt(
        np.sum(weights * left_centered**2)
        * np.sum(weights * right_centered**2)
    )
    if denominator <= 0.0:
        return None
    return float(np.sum(weights * left_centered * right_centered) / denominator)


def _average_ranks(values: np.ndarray) -> np.ndarray:
    return np.asarray(
        pl.Series("value", values).rank(method="average").to_numpy(), dtype=float
    )


def _weighted_calibration(
    predicted: np.ndarray,
    actual: np.ndarray,
    weights: np.ndarray,
) -> tuple[float | None, float | None]:
    design = np.column_stack([np.ones(predicted.size), predicted])
    weighted_design = design * np.sqrt(weights)[:, None]
    if np.linalg.matrix_rank(weighted_design) < 2:
        return None, None
    coefficients = np.linalg.lstsq(
        weighted_design,
        actual * np.sqrt(weights),
        rcond=None,
    )[0]
    return float(coefficients[0]), float(coefficients[1])


def score_hitter_predictions(
    predictions: pl.DataFrame,
    target_players: pl.DataFrame,
    *,
    weighting: str,
) -> dict[str, float | int | None]:
    """Score one prediction surface against a disclosed target-player table."""

    if weighting not in {"player", "pa"}:
        raise ValueError("weighting must be 'player' or 'pa'")
    probability_columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    missing_predictions = sorted(
        {"player_id", *probability_columns} - set(predictions.columns)
    )
    missing_targets = sorted(
        {"player_id", "hitter_talent_pa", *HITTER_TALENT_OUTCOMES}
        - set(target_players.columns)
    )
    if missing_predictions:
        raise ValueError(f"predictions missing scorer columns: {missing_predictions}")
    if missing_targets:
        raise ValueError(f"targets missing scorer columns: {missing_targets}")
    if predictions.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("prediction scoring keys must be unique by player")
    if target_players.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("target scoring keys must be unique by player")
    joined = target_players.join(
        predictions.select("player_id", *probability_columns),
        on="player_id",
        how="inner",
        validate="1:1",
    ).sort("player_id")
    if joined.is_empty():
        raise ValueError("prediction and target populations do not overlap")
    pa = joined["hitter_talent_pa"].to_numpy().astype(float)
    if np.any(pa <= 0.0):
        raise ValueError("scored target PA must be positive")
    counts = joined.select(HITTER_TALENT_OUTCOMES).to_numpy().astype(float)
    if np.any(counts < 0.0) or not np.allclose(counts.sum(axis=1), pa):
        raise ValueError("target outcome counts do not reconcile to target PA")
    probabilities = joined.select(probability_columns).to_numpy().astype(float)
    if not np.isfinite(probabilities).all() or np.any(probabilities < 0.0):
        raise ValueError("prediction probabilities must be finite and nonnegative")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-10):
        raise ValueError("prediction probabilities must sum to one")
    actual_probabilities = counts / pa[:, None]
    per_player_log_loss = -np.sum(
        actual_probabilities
        * np.log(np.maximum(probabilities, SCORING_PROBABILITY_FLOOR)),
        axis=1,
    )
    per_player_brier = (
        1.0
        - 2.0 * np.sum(actual_probabilities * probabilities, axis=1)
        + np.sum(probabilities**2, axis=1)
    )
    woba_weights = np.asarray(
        [NEUTRAL_WOBA_WEIGHTS[outcome] for outcome in HITTER_TALENT_OUTCOMES],
        dtype=float,
    )
    predicted_woba = probabilities @ woba_weights
    actual_woba = actual_probabilities @ woba_weights
    predicted_runs = (
        (predicted_woba - NEUTRAL_WOBA) / NEUTRAL_WOBA_SCALE
    ) * 600.0
    actual_runs = ((actual_woba - NEUTRAL_WOBA) / NEUTRAL_WOBA_SCALE) * 600.0
    weights = np.ones(joined.height, dtype=float) if weighting == "player" else pa
    woba_error = predicted_woba - actual_woba
    runs_error = predicted_runs - actual_runs
    woba_intercept, woba_slope = _weighted_calibration(
        predicted_woba, actual_woba, weights
    )
    return {
        "players": joined.height,
        "target_hitter_talent_pa": int(pa.sum()),
        "terminal_log_loss": _weighted_mean(per_player_log_loss, weights),
        "terminal_brier_score": _weighted_mean(per_player_brier, weights),
        "woba_mae": _weighted_mean(np.abs(woba_error), weights),
        "woba_rmse": _weighted_rmse(woba_error, weights),
        "runs_per_600_mae": _weighted_mean(np.abs(runs_error), weights),
        "runs_per_600_rmse": _weighted_rmse(runs_error, weights),
        "woba_pearson": _weighted_correlation(predicted_woba, actual_woba, weights),
        "woba_spearman": _weighted_correlation(
            _average_ranks(predicted_woba), _average_ranks(actual_woba), weights
        ),
        "runs_per_600_pearson": _weighted_correlation(
            predicted_runs, actual_runs, weights
        ),
        "runs_per_600_spearman": _weighted_correlation(
            _average_ranks(predicted_runs), _average_ranks(actual_runs), weights
        ),
        "woba_calibration_intercept": woba_intercept,
        "woba_calibration_slope": woba_slope,
        "mean_predicted_woba": _weighted_mean(predicted_woba, weights),
        "mean_actual_woba": _weighted_mean(actual_woba, weights),
    }


def score_nested_component_log_loss(
    predictions: pl.DataFrame,
    target_players: pl.DataFrame,
    *,
    component: str,
) -> dict[str, float | int]:
    """Score one nested conditional node by target events, for grid selection."""

    children = NESTED_COMPONENT_CHILD_LEAVES.get(component)
    if children is None:
        raise ValueError(f"unknown nested component: {component}")
    probability_columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    joined = target_players.join(
        predictions.select("player_id", *probability_columns),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    total_events = 0.0
    total_loss = 0.0
    for row in joined.iter_rows(named=True):
        child_counts = np.asarray(
            [sum(float(row[outcome]) for outcome in leaves) for leaves in children]
        )
        parent_events = float(child_counts.sum())
        if parent_events <= 0.0:
            continue
        child_mass = np.asarray(
            [
                sum(float(row[f"p_{outcome}"]) for outcome in leaves)
                for leaves in children
            ]
        )
        parent_mass = float(child_mass.sum())
        if parent_mass <= 0.0:
            raise ValueError("predicted nested parent has zero probability mass")
        conditional = child_mass / parent_mass
        total_loss -= float(
            np.sum(child_counts * np.log(np.maximum(conditional, SCORING_PROBABILITY_FLOOR)))
        )
        total_events += parent_events
    if total_events <= 0.0:
        raise ValueError(f"component {component} has no target events")
    return {
        "component": component,
        "events": int(total_events),
        "event_log_loss": total_loss / total_events,
    }
