"""Deterministic scoring primitives for Current Talent richer challenger 2.

These functions score an already-paired prediction surface. They do not fit richer
coefficients, select features, alter target coverage, or access any source data.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

import polars as pl


COMPARATOR_PREDICTION = "comparator_contact_value_prediction"
RICHER_PREDICTION = "richer_contact_value_prediction"
TARGET_VALUE = "terminal_value"


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def score_contact_value_pair(predictions: pl.DataFrame) -> dict[str, float | int | bool]:
    """Return event-weighted MSE/MAE for the fixed comparator/richer pair."""

    _require_columns(
        predictions,
        {TARGET_VALUE, COMPARATOR_PREDICTION, RICHER_PREDICTION},
        "contact-value prediction surface",
    )
    if predictions.is_empty():
        raise ValueError("contact-value scoring requires at least one paired event")

    working = predictions.select(
        pl.col(TARGET_VALUE).cast(pl.Float64, strict=False).alias("y"),
        pl.col(COMPARATOR_PREDICTION).cast(pl.Float64, strict=False).alias("baseline"),
        pl.col(RICHER_PREDICTION).cast(pl.Float64, strict=False).alias("richer"),
    )
    invalid = working.filter(
        pl.col("y").is_null()
        | ~pl.col("y").is_finite()
        | pl.col("baseline").is_null()
        | ~pl.col("baseline").is_finite()
        | pl.col("richer").is_null()
        | ~pl.col("richer").is_finite()
    )
    if not invalid.is_empty():
        raise ValueError("contact-value scoring surface contains invalid values")

    summary = working.select(
        ((pl.col("y") - pl.col("baseline")) ** 2).mean().alias("baseline_mse"),
        ((pl.col("y") - pl.col("richer")) ** 2).mean().alias("richer_mse"),
        (pl.col("y") - pl.col("baseline")).abs().mean().alias("baseline_mae"),
        (pl.col("y") - pl.col("richer")).abs().mean().alias("richer_mae"),
    ).row(0, named=True)
    baseline_mse = float(summary["baseline_mse"])
    richer_mse = float(summary["richer_mse"])
    baseline_mae = float(summary["baseline_mae"])
    richer_mae = float(summary["richer_mae"])
    if not all(isfinite(v) for v in (baseline_mse, richer_mse, baseline_mae, richer_mae)):
        raise ValueError("contact-value scoring produced non-finite loss")
    return {
        "event_count": int(predictions.height),
        "baseline_mse": baseline_mse,
        "richer_mse": richer_mse,
        "mse_delta_richer_minus_baseline": richer_mse - baseline_mse,
        "richer_mse_win": richer_mse < baseline_mse,
        "baseline_mae": baseline_mae,
        "richer_mae": richer_mae,
        "mae_delta_richer_minus_baseline": richer_mae - baseline_mae,
    }


def fit_contact_value_calibration(
    predictions: pl.DataFrame,
    *,
    prediction_column: str,
    variance_tolerance: float = 1e-15,
) -> dict[str, float | int]:
    """Fit event-weighted ``target = intercept + slope * prediction`` OLS."""

    if variance_tolerance <= 0:
        raise ValueError("variance_tolerance must be positive")
    _require_columns(
        predictions,
        {TARGET_VALUE, prediction_column},
        "contact-value calibration surface",
    )
    if predictions.height < 2:
        raise ValueError("contact-value calibration requires at least two events")

    working = predictions.select(
        pl.col(TARGET_VALUE).cast(pl.Float64, strict=False).alias("y"),
        pl.col(prediction_column).cast(pl.Float64, strict=False).alias("x"),
    )
    invalid = working.filter(
        pl.col("y").is_null()
        | ~pl.col("y").is_finite()
        | pl.col("x").is_null()
        | ~pl.col("x").is_finite()
    )
    if not invalid.is_empty():
        raise ValueError("contact-value calibration surface contains invalid values")

    means = working.select(pl.col("x").mean().alias("x_mean"), pl.col("y").mean().alias("y_mean")).row(0, named=True)
    x_mean = float(means["x_mean"])
    y_mean = float(means["y_mean"])
    centered = working.select(
        ((pl.col("x") - x_mean) ** 2).sum().alias("sxx"),
        ((pl.col("x") - x_mean) * (pl.col("y") - y_mean)).sum().alias("sxy"),
    ).row(0, named=True)
    sxx = float(centered["sxx"])
    sxy = float(centered["sxy"])
    scale = max(float(predictions.height), abs(x_mean) * predictions.height, 1.0)
    if not isfinite(sxx) or not isfinite(sxy) or sxx <= variance_tolerance * scale:
        raise ValueError("contact-value calibration prediction variance is not identifiable")
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    if not isfinite(slope) or not isfinite(intercept):
        raise ValueError("contact-value calibration fit is non-finite")
    return {
        "event_count": int(predictions.height),
        "intercept": float(intercept),
        "slope": float(slope),
        "absolute_intercept_error": abs(float(intercept)),
        "absolute_slope_error": abs(float(slope) - 1.0),
    }


def score_contact_value_fold(predictions: pl.DataFrame) -> dict[str, Any]:
    """Score losses and calibration for one fixed paired development fold."""

    losses = score_contact_value_pair(predictions)
    baseline_calibration = fit_contact_value_calibration(
        predictions, prediction_column=COMPARATOR_PREDICTION
    )
    richer_calibration = fit_contact_value_calibration(
        predictions, prediction_column=RICHER_PREDICTION
    )
    return {
        **losses,
        "baseline_calibration": baseline_calibration,
        "richer_calibration": richer_calibration,
    }
