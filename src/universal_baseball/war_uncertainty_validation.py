"""Diagnostics for frozen WAR intervals against like-for-like realized WAR."""

from __future__ import annotations

import math
from statistics import NormalDist

import polars as pl


def wilson_interval(successes: int, trials: int, *, confidence: float = 0.95) -> tuple[float, float]:
    """Return a two-sided Wilson score interval for a binomial proportion."""

    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("Wilson inputs must satisfy 0 <= successes <= trials")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between zero and one")
    z = NormalDist().inv_cdf((1.0 + confidence) / 2.0)
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2.0 * trials)) / denominator
    half_width = z * math.sqrt(
        proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return center - half_width, center + half_width


def summarize_interval_coverage(frame: pl.DataFrame) -> dict[str, float | int | str | None]:
    """Summarize interval behavior without changing or clipping any row."""

    required = {
        "projected_war_mean",
        "projected_war_lower",
        "projected_war_upper",
        "annual_war_variance",
        "observed_neutral_war",
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"WAR coverage input missing fields: {missing}")
    if frame.is_empty():
        raise ValueError("WAR coverage slice is empty")
    invalid = frame.filter(
        pl.any_horizontal(
            pl.col("projected_war_mean").is_null(),
            pl.col("projected_war_lower").is_null(),
            pl.col("projected_war_upper").is_null(),
            pl.col("annual_war_variance").is_null(),
            pl.col("observed_neutral_war").is_null(),
            pl.col("projected_war_lower") > pl.col("projected_war_upper"),
            pl.col("annual_war_variance") < 0.0,
        )
    )
    if invalid.height:
        raise ValueError("WAR coverage input contains invalid intervals")

    scored = frame.with_columns(
        (
            (pl.col("observed_neutral_war") >= pl.col("projected_war_lower"))
            & (pl.col("observed_neutral_war") <= pl.col("projected_war_upper"))
        ).alias("covered"),
        (pl.col("observed_neutral_war") < pl.col("projected_war_lower")).alias(
            "lower_miss"
        ),
        (pl.col("observed_neutral_war") > pl.col("projected_war_upper")).alias(
            "upper_miss"
        ),
        (pl.col("projected_war_upper") - pl.col("projected_war_lower")).alias(
            "interval_width"
        ),
    )
    positive_variance = scored.filter(pl.col("annual_war_variance") > 0.0).with_columns(
        (
            (pl.col("observed_neutral_war") - pl.col("projected_war_mean"))
            / pl.col("annual_war_variance").sqrt()
        ).alias("standardized_error")
    )
    count = scored.height
    covered = int(scored.get_column("covered").sum())
    lower, upper = wilson_interval(covered, count)
    if positive_variance.height:
        standardized = positive_variance.get_column("standardized_error")
        standardized_mean: float | None = float(standardized.mean())
        standardized_rmse: float | None = math.sqrt(float((standardized**2).mean()))
    else:
        standardized_mean = None
        standardized_rmse = None
    nominal = 0.80
    if lower <= nominal <= upper:
        assessment = "target_inside_wilson_interval"
    elif lower > nominal:
        assessment = "overcoverage"
    else:
        assessment = "undercoverage"
    widths = scored.get_column("interval_width")
    return {
        "players": count,
        "covered_players": covered,
        "coverage": covered / count,
        "coverage_wilson_95_lower": lower,
        "coverage_wilson_95_upper": upper,
        "nominal_coverage": nominal,
        "assessment": assessment,
        "lower_tail_miss_rate": float(scored.get_column("lower_miss").mean()),
        "upper_tail_miss_rate": float(scored.get_column("upper_miss").mean()),
        "median_interval_width": float(widths.median()),
        "p90_interval_width": float(widths.quantile(0.9)),
        "positive_variance_players": positive_variance.height,
        "standardized_error_mean": standardized_mean,
        "standardized_error_rmse": standardized_rmse,
    }


def summarize_named_slices(
    frame: pl.DataFrame,
    *,
    slice_column: str,
) -> list[dict[str, object]]:
    """Summarize every observed category while retaining small-slice labels."""

    if slice_column not in frame.columns:
        raise ValueError(f"WAR coverage slice column missing: {slice_column}")
    rows: list[dict[str, object]] = []
    for value in frame.get_column(slice_column).unique().sort().to_list():
        subset = frame.filter(pl.col(slice_column) == value)
        rows.append(
            {
                "slice_column": slice_column,
                "slice_value": str(value),
                "decision_eligible": subset.height >= 30,
                **summarize_interval_coverage(subset),
            }
        )
    return rows
