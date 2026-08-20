"""Deterministic statistics for the Player Value v1 park-neutrality audit."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class WeightedSlope:
    intercept: float
    slope: float
    fitted_weighted_sd: float


def harmonic_exposure(first: float, second: float) -> float:
    """Balanced exposure weight that tends to zero with either split."""

    left = float(first)
    right = float(second)
    if not math.isfinite(left) or not math.isfinite(right) or left < 0 or right < 0:
        raise ValueError("exposures must be finite and nonnegative")
    return 0.0 if left == 0.0 or right == 0.0 else 2.0 * left * right / (left + right)


def weighted_mean(values: Sequence[float], weights: Sequence[float]) -> float:
    if len(values) != len(weights) or not values:
        raise ValueError("values and weights must be nonempty and equally sized")
    if any(not math.isfinite(float(value)) for value in values):
        raise ValueError("values must be finite")
    if any(not math.isfinite(float(weight)) or float(weight) < 0 for weight in weights):
        raise ValueError("weights must be finite and nonnegative")
    total = math.fsum(float(weight) for weight in weights)
    if total <= 0:
        raise ValueError("weights must have positive total")
    return math.fsum(float(value) * float(weight) for value, weight in zip(values, weights)) / total


def weighted_slope(
    x: Sequence[float],
    y: Sequence[float],
    weights: Sequence[float],
) -> WeightedSlope:
    """Fit a finite weighted line and report SD of its fitted centered values."""

    if len(x) != len(y) or len(x) != len(weights) or len(x) < 2:
        raise ValueError("weighted slope requires equally sized inputs with at least two rows")
    x_mean = weighted_mean(x, weights)
    y_mean = weighted_mean(y, weights)
    denominator = math.fsum(
        float(weight) * (float(value) - x_mean) ** 2
        for value, weight in zip(x, weights)
    )
    if denominator <= 0:
        raise ValueError("weighted slope requires nonconstant x")
    numerator = math.fsum(
        float(weight) * (float(x_value) - x_mean) * (float(y_value) - y_mean)
        for x_value, y_value, weight in zip(x, y, weights)
    )
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    fitted = [intercept + slope * float(value) for value in x]
    fitted_mean = weighted_mean(fitted, weights)
    weight_total = math.fsum(float(weight) for weight in weights)
    fitted_sd = math.sqrt(
        math.fsum(
            float(weight) * (value - fitted_mean) ** 2
            for value, weight in zip(fitted, weights)
        )
        / weight_total
    )
    return WeightedSlope(float(intercept), float(slope), float(fitted_sd))


def one_sided_permutation_p_value(
    x: Sequence[float],
    y: Sequence[float],
    weights: Sequence[float],
    *,
    iterations: int = 10_000,
    seed: int = 20_240_820,
) -> float:
    """Return P(permuted slope >= observed slope), with plus-one correction."""

    if iterations <= 0:
        raise ValueError("iterations must be positive")
    observed = weighted_slope(x, y, weights).slope
    shuffled = [float(value) for value in y]
    generator = random.Random(seed)
    exceedances = 0
    for _ in range(iterations):
        generator.shuffle(shuffled)
        if weighted_slope(x, shuffled, weights).slope >= observed:
            exceedances += 1
    return (exceedances + 1.0) / (iterations + 1.0)


def centered_rate_rows(
    rows: Iterable[tuple[float, float]],
    *,
    scale: float = 600.0,
) -> list[float]:
    """Center (numerator, exposure) rows by their pooled rate and scale them."""

    materialized = [(float(value), float(exposure)) for value, exposure in rows]
    if not materialized or any(
        not math.isfinite(value)
        or not math.isfinite(exposure)
        or exposure <= 0
        for value, exposure in materialized
    ):
        raise ValueError("rate rows require finite numerators and positive exposures")
    pooled = math.fsum(value for value, _ in materialized) / math.fsum(
        exposure for _, exposure in materialized
    )
    return [scale * (value / exposure - pooled) for value, exposure in materialized]
