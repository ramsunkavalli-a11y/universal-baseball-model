"""Regressed adjacent-season pitcher component aging on a coherent BF profile."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping

import numpy as np
import polars as pl


COMPONENTS = ("so", "ubb", "hbp", "hr", "other")
MODELED_COMPONENTS = COMPONENTS[:-1]
AGE_CENTER = 28.0
AGE_SCALE = 10.0


@dataclass(frozen=True, slots=True)
class PitcherAgingParameters:
    model_id: str
    coefficients: dict[str, tuple[float, float, float]]
    regression_bf: float
    ridge_weight: float
    pair_count: int
    pitcher_count: int
    minimum_age: float
    maximum_age: float


def _profiles(history: pl.DataFrame, ages: pl.DataFrame, regression_bf: float) -> pl.DataFrame:
    required = {"season", "player_id", "bf", "so", "ubb", "hbp", "hr"}
    if missing := sorted(required - set(history.columns)):
        raise ValueError(f"pitcher aging history missing columns: {missing}")
    if set(ages.columns) != {"season", "player_id", "age"}:
        raise ValueError("pitcher ages require season, player_id, and age")
    source = history.group_by("season", "player_id").agg(
        *(pl.col(column).sum().alias(column) for column in required - {"season", "player_id"})
    ).with_columns(
        (pl.col("bf") - pl.sum_horizontal("so", "ubb", "hbp", "hr")).alias("other")
    )
    if source.filter(
        (pl.col("bf") <= 0)
        | pl.any_horizontal(*(pl.col(column) < 0 for column in COMPONENTS))
    ).height:
        raise ValueError("pitcher aging history has invalid BF accounting")
    priors = source.group_by("season").agg(
        pl.col("bf").sum().alias("season_bf"),
        *(pl.col(column).sum().alias(f"season_{column}") for column in COMPONENTS),
    ).with_columns(
        *(
            (pl.col(f"season_{column}") / pl.col("season_bf")).alias(f"prior_{column}")
            for column in COMPONENTS
        )
    )
    result = source.join(priors, on="season", how="left", validate="m:1").with_columns(
        *(
            (
                (pl.col(column) + regression_bf * pl.col(f"prior_{column}"))
                / (pl.col("bf") + regression_bf)
            ).alias(f"p_{column}")
            for column in COMPONENTS
        )
    ).join(ages, on=["season", "player_id"], how="inner", validate="1:1")
    return result.select(
        "season", "player_id", "age", "bf", *COMPONENTS,
        *(f"p_{column}" for column in COMPONENTS)
    )


def build_adjacent_pitcher_profiles(
    history: pl.DataFrame,
    ages: pl.DataFrame,
    *,
    regression_bf: float = 200.0,
) -> pl.DataFrame:
    """Create same-pitcher adjacent pairs after shrinkage to each season's league."""

    if regression_bf <= 0:
        raise ValueError("regression_bf must be positive")
    profiles = _profiles(history, ages, regression_bf)
    target = profiles.rename(
        {
            "season": "target_season", "age": "target_age", "bf": "target_bf",
            **{key: f"target_count_{key}" for key in COMPONENTS},
            **{f"p_{key}": f"target_p_{key}" for key in COMPONENTS},
        }
    ).select(
        "target_season", "player_id", "target_age", "target_bf",
        *(f"target_count_{key}" for key in COMPONENTS),
        *(f"target_p_{key}" for key in COMPONENTS),
    )
    source = profiles.select(
        "season", "player_id", "age", "bf", *(f"p_{key}" for key in COMPONENTS)
    )
    pairs = source.rename(
        {
            "age": "source_age", "bf": "source_bf",
            **{f"p_{key}": f"source_p_{key}" for key in COMPONENTS},
        }
    ).with_columns((pl.col("season") + 1).alias("target_season")).join(
        target, on=["player_id", "target_season"], how="inner", validate="1:1"
    ).with_columns(
        (
            2.0 * pl.col("source_bf") * pl.col("target_bf")
            / (pl.col("source_bf") + pl.col("target_bf"))
        ).clip(upper_bound=800.0).alias("pair_weight")
    )
    return pairs.filter(
        pl.col("source_age").is_between(18, 45)
        & pl.col("target_age").is_between(19, 46)
    ).sort(["target_season", "player_id"])


def fit_pitcher_component_aging(
    pairs: pl.DataFrame,
    *,
    maximum_target_season: int,
    regression_bf: float = 200.0,
    ridge_weight: float = 20_000.0,
    model_id: str = "pitcher_adjacent_clr_quadratic_v1",
) -> PitcherAgingParameters:
    """Fit quadratic one-year CLR shifts with a zero-effect ridge prior."""

    train = pairs.filter(pl.col("target_season") <= maximum_target_season)
    if train.height < 100:
        raise ValueError("pitcher aging fit requires at least 100 adjacent pairs")
    age = train.get_column("source_age").to_numpy().astype(float)
    x = (age - AGE_CENTER) / AGE_SCALE
    design = np.column_stack([np.ones(len(x)), x, x * x])
    weights = train.get_column("pair_weight").to_numpy().astype(float)
    weighted_design = design * weights[:, None]
    penalty = np.eye(3) * float(ridge_weight)
    coefficients: dict[str, tuple[float, float, float]] = {}
    for component in MODELED_COMPONENTS:
        response = np.log(
            train.get_column(f"target_p_{component}").to_numpy()
            / train.get_column("target_p_other").to_numpy()
        ) - np.log(
            train.get_column(f"source_p_{component}").to_numpy()
            / train.get_column("source_p_other").to_numpy()
        )
        fitted = np.linalg.solve(weighted_design.T @ design + penalty, weighted_design.T @ response)
        coefficients[component] = tuple(float(value) for value in fitted)
    return PitcherAgingParameters(
        model_id=model_id,
        coefficients=coefficients,
        regression_bf=float(regression_bf),
        ridge_weight=float(ridge_weight),
        pair_count=train.height,
        pitcher_count=train.get_column("player_id").n_unique(),
        minimum_age=float(train.get_column("source_age").min()),
        maximum_age=float(train.get_column("source_age").max()),
    )


def _one_year_shift(component: str, age: float, parameters: PitcherAgingParameters) -> float:
    bounded = min(parameters.maximum_age, max(parameters.minimum_age, float(age)))
    x = (bounded - AGE_CENTER) / AGE_SCALE
    intercept, linear, quadratic = parameters.coefficients[component]
    return intercept + linear * x + quadratic * x * x


def apply_fitted_pitcher_aging(
    probabilities: Mapping[str, float],
    *,
    current_age: float | None,
    target_age: float | None,
    parameters: PitcherAgingParameters,
) -> dict[str, float]:
    """Apply cumulative fitted CLR shifts while preserving the BF composition."""

    if set(probabilities) != set(COMPONENTS):
        raise ValueError("pitcher probability keys differ from five-part profile")
    values = {key: float(value) for key, value in probabilities.items()}
    if any(not math.isfinite(value) or value <= 0 for value in values.values()):
        raise ValueError("fitted aging requires finite positive probabilities")
    if not math.isclose(sum(values.values()), 1.0, abs_tol=1e-9):
        raise ValueError("pitcher probabilities must sum to one")
    if current_age is None or target_age is None:
        return values
    years = int(round(float(target_age) - float(current_age)))
    if years < 0 or not math.isclose(float(target_age) - float(current_age), years, abs_tol=1e-6):
        raise ValueError("pitcher aging supports nonnegative whole-season horizons")
    log_ratios = {
        component: math.log(values[component] / values["other"])
        for component in MODELED_COMPONENTS
    }
    for step in range(years):
        age = float(current_age) + step
        for component in MODELED_COMPONENTS:
            log_ratios[component] += _one_year_shift(component, age, parameters)
    ratios = {component: math.exp(value) for component, value in log_ratios.items()}
    other = 1.0 / (1.0 + sum(ratios.values()))
    return {**{component: ratio * other for component, ratio in ratios.items()}, "other": other}


def component_log_loss(
    pairs: pl.DataFrame,
    predictor,
) -> float:
    """Return target-BF-weighted multinomial log loss for adjacent pairs."""

    loss = 0.0
    exposure = 0.0
    for row in pairs.iter_rows(named=True):
        source = {key: float(row[f"source_p_{key}"]) for key in COMPONENTS}
        predicted = predictor(source, float(row["source_age"]), float(row["target_age"]))
        target_bf = float(row["target_bf"])
        for key in COMPONENTS:
            loss -= float(row[f"target_count_{key}"]) * math.log(float(predicted[key]))
        exposure += target_bf
    if exposure <= 0:
        raise ValueError("aging score requires positive target BF")
    return loss / exposure
