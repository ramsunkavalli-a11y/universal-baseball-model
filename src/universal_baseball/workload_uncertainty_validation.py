"""Validation helpers for conditional positive MLB workload distributions."""

from __future__ import annotations

import math

import polars as pl
from scipy.stats import nbinom

from universal_baseball.player_value_uncertainty import recover_untruncated_nb2_mean


def zero_truncated_nb2_quantile(
    probability: float, *, positive_mean: float, alpha: float
) -> float:
    """Return a quantile of the fitted zero-truncated NB2 workload distribution."""

    if not 0 < probability < 1:
        raise ValueError("workload quantile probability must be inside (0, 1)")
    mu = recover_untruncated_nb2_mean(positive_mean, alpha=alpha)
    size = 1.0 / alpha
    nb_probability = size / (size + mu)
    zero_probability = nb_probability**size
    untruncated_probability = zero_probability + probability * (1.0 - zero_probability)
    quantile = float(nbinom.ppf(untruncated_probability, size, nb_probability))
    if not math.isfinite(quantile):
        raise RuntimeError("zero-truncated NB2 quantile is not finite")
    return max(1.0, quantile)


def summarize_positive_workload_coverage(frame: pl.DataFrame) -> dict[str, float | int]:
    """Score the fitted P10-P90 workload range among players who were active."""

    required = {"conditional_mean", "nb_alpha", "observed_workload"}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"positive workload coverage missing fields: {missing}")
    active = frame.select(sorted(required)).filter(pl.col("observed_workload") > 0)
    if active.is_empty():
        raise ValueError("positive workload coverage requires active outcomes")
    rows = []
    for row in active.iter_rows(named=True):
        lower = zero_truncated_nb2_quantile(
            0.10,
            positive_mean=float(row["conditional_mean"]),
            alpha=float(row["nb_alpha"]),
        )
        upper = zero_truncated_nb2_quantile(
            0.90,
            positive_mean=float(row["conditional_mean"]),
            alpha=float(row["nb_alpha"]),
        )
        observed = float(row["observed_workload"])
        width = upper - lower
        score = width + 10.0 * max(0.0, lower - observed) + 10.0 * max(0.0, observed - upper)
        rows.append(
            {
                "covered": lower <= observed <= upper,
                "lower_miss": observed < lower,
                "upper_miss": observed > upper,
                "width": width,
                "interval_score": score,
            }
        )
    scored = pl.DataFrame(rows)
    return {
        "active_players": scored.height,
        "coverage": float(scored.get_column("covered").mean()),
        "lower_miss_rate": float(scored.get_column("lower_miss").mean()),
        "upper_miss_rate": float(scored.get_column("upper_miss").mean()),
        "median_interval_width": float(scored.get_column("width").median()),
        "mean_interval_score": float(scored.get_column("interval_score").mean()),
    }
