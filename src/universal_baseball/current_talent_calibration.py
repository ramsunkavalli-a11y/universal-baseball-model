"""Calibration intercept/slope diagnostics for Current Talent component forecasts.

For each model × core component we fit a grouped-binomial logistic calibration
model on realized future target-environment counts:

    logit(P[outcome_k]) = intercept + slope * logit(predicted_probability_k)

Ideal calibration is intercept = 0 and slope = 1. These coefficients are
validation diagnostics only; this module does not recalibrate predictions or feed
future outcomes back into a Current Talent estimate.
"""

from __future__ import annotations

from math import exp, log

import polars as pl

from universal_baseball.current_talent_scoring import MODEL_TARGET_COLUMNS
from universal_baseball.current_talent_validation_dataset import TARGET_ENVIRONMENT_KEY
from universal_baseball.performance_season import ALL_CORE_BINS


DEFAULT_PROBABILITY_CLIP = 1e-8
DEFAULT_MAX_ITERATIONS = 100
DEFAULT_TOLERANCE = 1e-10


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _attach_target_counts(
    projected_profile: pl.DataFrame,
    target_profile: pl.DataFrame,
) -> pl.DataFrame:
    projected_required = {
        *TARGET_ENVIRONMENT_KEY,
        "future_core_events",
        "core_bin",
        *MODEL_TARGET_COLUMNS.values(),
    }
    target_required = {*TARGET_ENVIRONMENT_KEY, "core_bin", "future_occurrence_count"}
    _require_columns(projected_profile, projected_required, "projected profile")
    _require_columns(target_profile, target_required, "target profile")

    duplicate = target_profile.group_by([*TARGET_ENVIRONMENT_KEY, "core_bin"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("target profile violates target-environment + core-bin grain")

    counts = target_profile.select(
        *TARGET_ENVIRONMENT_KEY,
        "core_bin",
        "future_occurrence_count",
    )
    attached = projected_profile.join(
        counts,
        on=[*TARGET_ENVIRONMENT_KEY, "core_bin"],
        how="left",
    ).with_columns(pl.col("future_occurrence_count").fill_null(0).cast(pl.Int64))

    bad_counts = attached.filter(
        (pl.col("future_occurrence_count") < 0)
        | (pl.col("future_occurrence_count") > pl.col("future_core_events"))
        | (pl.col("future_core_events") <= 0)
    )
    if not bad_counts.is_empty():
        raise ValueError("calibration rows contain invalid grouped-binomial counts")
    return attached


def _sigmoid(value: float) -> float:
    if value >= 35.0:
        return 1.0 - 1e-15
    if value <= -35.0:
        return 1e-15
    return 1.0 / (1.0 + exp(-value))


def _fit_grouped_binomial_calibration(
    rows: list[tuple[float, int, int]],
    *,
    probability_clip: float,
    max_iterations: int,
    tolerance: float,
) -> dict[str, float | int | bool | str]:
    if not 0 < probability_clip < 0.5:
        raise ValueError("probability_clip must lie between zero and 0.5")
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    if not rows:
        raise ValueError("calibration fit requires at least one grouped-binomial row")

    design: list[tuple[float, int, int]] = []
    observed_total = 0
    opportunity_total = 0
    predicted_mass = 0.0
    for probability, successes, opportunities in rows:
        if opportunities <= 0 or successes < 0 or successes > opportunities:
            raise ValueError("invalid grouped-binomial calibration observation")
        clipped = min(max(float(probability), probability_clip), 1.0 - probability_clip)
        logit = log(clipped / (1.0 - clipped))
        design.append((logit, int(successes), int(opportunities)))
        observed_total += int(successes)
        opportunity_total += int(opportunities)
        predicted_mass += float(probability) * int(opportunities)

    if observed_total == 0 or observed_total == opportunity_total:
        return {
            "calibration_intercept": float("nan"),
            "calibration_slope": float("nan"),
            "converged": False,
            "iterations": 0,
            "fit_status": "degenerate_outcome",
            "future_core_events": opportunity_total,
            "observed_count": observed_total,
            "observed_event_rate": observed_total / opportunity_total,
            "mean_predicted_probability": predicted_mass / opportunity_total,
        }

    intercept = 0.0
    slope = 1.0
    converged = False
    fit_status = "max_iterations"
    iterations = 0

    for iteration in range(1, max_iterations + 1):
        gradient_intercept = 0.0
        gradient_slope = 0.0
        information_00 = 0.0
        information_01 = 0.0
        information_11 = 0.0

        for x_value, successes, opportunities in design:
            fitted = _sigmoid(intercept + slope * x_value)
            residual = successes - opportunities * fitted
            variance_weight = opportunities * fitted * (1.0 - fitted)
            gradient_intercept += residual
            gradient_slope += residual * x_value
            information_00 += variance_weight
            information_01 += variance_weight * x_value
            information_11 += variance_weight * x_value * x_value

        determinant = information_00 * information_11 - information_01 * information_01
        scale = max(1.0, information_00 * information_11)
        if abs(determinant) <= 1e-14 * scale:
            fit_status = "singular_information"
            iterations = iteration
            break

        delta_intercept = (
            gradient_intercept * information_11
            - gradient_slope * information_01
        ) / determinant
        delta_slope = (
            information_00 * gradient_slope
            - information_01 * gradient_intercept
        ) / determinant

        intercept += delta_intercept
        slope += delta_slope
        iterations = iteration
        if max(abs(delta_intercept), abs(delta_slope)) <= tolerance:
            converged = True
            fit_status = "converged"
            break

    return {
        "calibration_intercept": float(intercept),
        "calibration_slope": float(slope),
        "converged": converged,
        "iterations": iterations,
        "fit_status": fit_status,
        "future_core_events": opportunity_total,
        "observed_count": observed_total,
        "observed_event_rate": observed_total / opportunity_total,
        "mean_predicted_probability": predicted_mass / opportunity_total,
    }


def build_component_calibration_coefficients(
    projected_profile: pl.DataFrame,
    target_profile: pl.DataFrame,
    *,
    probability_clip: float = DEFAULT_PROBABILITY_CLIP,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    tolerance: float = DEFAULT_TOLERANCE,
) -> pl.DataFrame:
    """Fit grouped-binomial calibration intercept/slope per model/component.

    The fit uses target-environment rows as grouped binomial observations. Future
    event counts are therefore used as their natural binomial exposure, not as an
    arbitrary post-hoc weight. Ideal coefficients are intercept=0 and slope=1.
    """

    attached = _attach_target_counts(projected_profile, target_profile)
    rows: list[dict[str, object]] = []
    for model, probability_column in MODEL_TARGET_COLUMNS.items():
        for core_bin in ALL_CORE_BINS:
            group = attached.filter(pl.col("core_bin") == core_bin)
            observations = [
                (
                    float(row[probability_column]),
                    int(row["future_occurrence_count"]),
                    int(row["future_core_events"]),
                )
                for row in group.iter_rows(named=True)
            ]
            fit = _fit_grouped_binomial_calibration(
                observations,
                probability_clip=probability_clip,
                max_iterations=max_iterations,
                tolerance=tolerance,
            )
            intercept = float(fit["calibration_intercept"])
            slope = float(fit["calibration_slope"])
            rows.append(
                {
                    "model": model,
                    "core_bin": core_bin,
                    **fit,
                    "absolute_intercept_error": abs(intercept),
                    "absolute_slope_error": abs(slope - 1.0),
                    "ideal_calibration_intercept": 0.0,
                    "ideal_calibration_slope": 1.0,
                    "probability_clip": float(probability_clip),
                }
            )
    return pl.DataFrame(rows).sort(["core_bin", "model"])
