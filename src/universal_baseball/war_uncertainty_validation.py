"""Diagnostics for frozen WAR intervals against like-for-like realized WAR."""

from __future__ import annotations

import math
from statistics import NormalDist

import polars as pl


PROBABILITY_BREAKS = (0.10, 0.30, 0.60, 0.85)
PROBABILITY_LABELS = ("0-.10", ".10-.30", ".30-.60", ".60-.85", ".85-1")
REFERENCE_QUANTILES = (0.10, 0.25, 0.50, 0.75, 0.90)


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
    alpha = 1.0 - nominal
    interval_score = scored.select(
        (
            pl.col("interval_width")
            + (2.0 / alpha)
            * (pl.col("projected_war_lower") - pl.col("observed_neutral_war"))
            .clip(lower_bound=0.0)
            + (2.0 / alpha)
            * (pl.col("observed_neutral_war") - pl.col("projected_war_upper"))
            .clip(lower_bound=0.0)
        ).mean()
    ).item()
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
        "mean_interval_score": float(interval_score),
        "positive_variance_players": positive_variance.height,
        "standardized_error_mean": standardized_mean,
        "standardized_error_rmse": standardized_rmse,
    }


def summarize_binary_probability_calibration(
    frame: pl.DataFrame,
    *,
    probability_column: str,
    outcome_column: str,
    minimum_bin_size: int = 30,
) -> dict[str, object]:
    """Score a binary probability and fixed forecast-time reliability bands."""

    if probability_column not in frame.columns or outcome_column not in frame.columns:
        raise ValueError("probability calibration columns are missing")
    if minimum_bin_size <= 0:
        raise ValueError("minimum bin size must be positive")
    scored = frame.select(probability_column, outcome_column).cast(
        {probability_column: pl.Float64, outcome_column: pl.Float64}, strict=True
    )
    if scored.is_empty() or scored.null_count().row(0) != (0, 0):
        raise ValueError("probability calibration input is empty or null")
    if scored.filter(
        ~pl.col(probability_column).is_finite()
        | ~pl.col(probability_column).is_between(0.0, 1.0)
        | ~pl.col(outcome_column).is_in([0.0, 1.0])
    ).height:
        raise ValueError("probability calibration values are invalid")
    scored = scored.with_columns(
        pl.col(probability_column)
        .cut(PROBABILITY_BREAKS, labels=PROBABILITY_LABELS)
        .alias("probability_band")
    )
    rows = []
    absolute_gap_mass = 0.0
    for band in PROBABILITY_LABELS:
        subset = scored.filter(pl.col("probability_band") == band)
        if subset.is_empty():
            continue
        predicted = float(subset.get_column(probability_column).mean())
        observed = float(subset.get_column(outcome_column).mean())
        absolute_gap_mass += subset.height * abs(predicted - observed)
        rows.append(
            {
                "probability_band": band,
                "players": subset.height,
                "mean_predicted_probability": predicted,
                "observed_rate": observed,
                "calibration_gap": predicted - observed,
                "decision_eligible": subset.height >= minimum_bin_size,
            }
        )
    probabilities = scored.get_column(probability_column).clip(1e-12, 1.0 - 1e-12)
    outcomes = scored.get_column(outcome_column)
    return {
        "players": scored.height,
        "observed_rate": float(outcomes.mean()),
        "mean_predicted_probability": float(probabilities.mean()),
        "brier": float(((probabilities - outcomes) ** 2).mean()),
        "log_loss": float(
            (-(outcomes * probabilities.log()
               + (1.0 - outcomes) * (1.0 - probabilities).log())).mean()
        ),
        "expected_calibration_error": absolute_gap_mass / scored.height,
        "fixed_probability_bands": rows,
    }


def summarize_normal_reference_calibration(frame: pl.DataFrame) -> dict[str, object]:
    """Audit fixed quantiles and PIT values implied by the moment-normal reference."""

    required = {"projected_war_mean", "annual_war_variance", "observed_neutral_war"}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"normal reference calibration missing fields: {missing}")
    source = frame.select(sorted(required)).cast(
        {column: pl.Float64 for column in required}, strict=True
    )
    if source.is_empty() or source.null_count().row(0) != (0, 0, 0):
        raise ValueError("normal reference calibration input is empty or null")
    if source.filter(
        pl.any_horizontal(*(~pl.col(column).is_finite() for column in required))
        | (pl.col("annual_war_variance") < 0)
    ).height:
        raise ValueError("normal reference calibration input is invalid")
    positive = source.filter(pl.col("annual_war_variance") > 0)
    if positive.is_empty():
        raise ValueError("normal reference calibration requires positive variance")
    normal = NormalDist()
    means = positive.get_column("projected_war_mean").to_list()
    standard_deviations = positive.get_column("annual_war_variance").sqrt().to_list()
    observations = positive.get_column("observed_neutral_war").to_list()
    pit = [
        normal.cdf((float(observed) - float(mean)) / float(deviation))
        for mean, deviation, observed in zip(
            means, standard_deviations, observations, strict=True
        )
    ]
    pit_counts = [0] * 10
    for value in pit:
        pit_counts[min(9, int(value * 10))] += 1
    ordered = sorted(pit)
    count = len(ordered)
    ks_distance = max(
        max((index + 1) / count - value, value - index / count)
        for index, value in enumerate(ordered)
    )
    quantiles = []
    for probability in REFERENCE_QUANTILES:
        z = normal.inv_cdf(probability)
        forecasts = [
            float(mean) + z * float(deviation)
            for mean, deviation in zip(means, standard_deviations, strict=True)
        ]
        hits = sum(
            float(observed) <= forecast
            for observed, forecast in zip(observations, forecasts, strict=True)
        )
        errors = [
            float(observed) - forecast
            for observed, forecast in zip(observations, forecasts, strict=True)
        ]
        quantiles.append(
            {
                "nominal_quantile": probability,
                "observed_below_rate": hits / count,
                "calibration_gap": hits / count - probability,
                "mean_pinball_loss": sum(
                    max(probability * error, (probability - 1.0) * error)
                    for error in errors
                )
                / count,
            }
        )
    pit_mean = sum(pit) / count
    return {
        "reference_distribution": "normal_from_reported_mean_and_variance",
        "players": source.height,
        "positive_variance_players": count,
        "zero_variance_players_excluded": source.height - count,
        "pit_mean": pit_mean,
        "pit_variance": sum((value - pit_mean) ** 2 for value in pit) / count,
        "pit_uniform_reference_variance": 1.0 / 12.0,
        "pit_ks_distance_from_uniform": ks_distance,
        "fixed_pit_bin_counts": pit_counts,
        "fixed_quantile_calibration": quantiles,
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
