"""Frozen gate definitions for disclosed Hitter v2 Stage 2b development."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import polars as pl


PROPER_SCORE_METRICS = ("terminal_log_loss", "terminal_brier_score")
POOLED_RATE_METRICS = (
    "woba_rmse",
    "runs_per_600_rmse",
)
STRICT_IMPROVEMENT_TOLERANCE = 1e-8
RICHER_WOBA_RMSE_RELATIVE_TOLERANCE = 0.0025
LEVEL_SUPPORT_PLAYERS = 100
LEVEL_SUPPORT_PA = 10_000
MATERIAL_WOBA_RMSE_REVERSAL = 0.002
MATERIAL_RUNS_RMSE_REVERSAL = 0.5
MATERIAL_LOG_LOSS_REVERSAL = 0.0005
MATERIAL_BRIER_REVERSAL = 0.0005
CALIBRATION_INTERCEPT_SCALE = 0.005
CALIBRATION_SLOPE_SCALE = 0.10


def strongest_baseline_value(
    b0: Mapping[str, float | int | None],
    b1: Mapping[str, float | int | None],
    metric: str,
) -> tuple[str, float]:
    """Return the metric-wise lower-loss permanent baseline."""

    values = {
        "B0_ONE_YEAR_EB": b0.get(metric),
        "B1_MARCEL_345_K1200": b1.get(metric),
    }
    if any(value is None for value in values.values()):
        raise ValueError(f"baseline metric is unavailable: {metric}")
    return min(
        ((model_id, float(value)) for model_id, value in values.items()),
        key=lambda pair: (pair[1], pair[0]),
    )


def proper_score_gate(
    candidate: Mapping[str, float | int | None],
    b0: Mapping[str, float | int | None],
    b1: Mapping[str, float | int | None],
) -> dict[str, object]:
    """Require strict improvement in both event proper scores."""

    comparisons: dict[str, object] = {}
    for metric in PROPER_SCORE_METRICS:
        baseline_id, baseline = strongest_baseline_value(b0, b1, metric)
        value = float(candidate[metric])
        delta = value - baseline
        comparisons[metric] = {
            "candidate": value,
            "baseline_id": baseline_id,
            "baseline": baseline,
            "candidate_minus_baseline": delta,
            "pass": delta < -STRICT_IMPROVEMENT_TOLERANCE,
        }
    return {
        "comparisons": comparisons,
        "pass": all(bool(value["pass"]) for value in comparisons.values()),
    }


def pooled_prediction_gate(
    candidate: Mapping[str, float | int | None],
    b0: Mapping[str, float | int | None],
    b1: Mapping[str, float | int | None],
) -> dict[str, object]:
    """Require pooled proper-score and rate-RMSE improvement."""

    comparisons: dict[str, object] = {}
    for metric in (*PROPER_SCORE_METRICS, *POOLED_RATE_METRICS):
        baseline_id, baseline = strongest_baseline_value(b0, b1, metric)
        value = float(candidate[metric])
        delta = value - baseline
        comparisons[metric] = {
            "candidate": value,
            "baseline_id": baseline_id,
            "baseline": baseline,
            "candidate_minus_baseline": delta,
            "pass": delta < -STRICT_IMPROVEMENT_TOLERANCE,
        }
    return {
        "comparisons": comparisons,
        "pass": all(bool(value["pass"]) for value in comparisons.values()),
    }


def calibration_distance(metrics: Mapping[str, float | int | None]) -> float:
    """Return a dimensionless intercept/slope distance from ideal calibration."""

    intercept = metrics.get("woba_calibration_intercept")
    slope = metrics.get("woba_calibration_slope")
    if intercept is None or slope is None:
        raise ValueError("wOBA calibration is not identifiable")
    return (
        (float(intercept) / CALIBRATION_INTERCEPT_SCALE) ** 2
        + ((float(slope) - 1.0) / CALIBRATION_SLOPE_SCALE) ** 2
    )


def pooled_woba_calibration(
    surface: pl.DataFrame,
    *,
    weighting: str,
) -> dict[str, float]:
    """Fit pooled actual wOBA on predicted wOBA for one frozen weighting view."""

    if weighting not in {"player", "pa"}:
        raise ValueError("weighting must be 'player' or 'pa'")
    required = {"predicted_woba", "actual_woba", "hitter_talent_pa"}
    if missing := sorted(required - set(surface.columns)):
        raise ValueError(f"pooled calibration surface lacks columns: {missing}")
    predicted = surface["predicted_woba"].to_numpy().astype(float)
    actual = surface["actual_woba"].to_numpy().astype(float)
    weights = (
        np.ones(surface.height, dtype=float)
        if weighting == "player"
        else surface["hitter_talent_pa"].to_numpy().astype(float)
    )
    design = np.column_stack([np.ones(surface.height), predicted])
    weighted_design = design * np.sqrt(weights)[:, None]
    if np.linalg.matrix_rank(weighted_design) < 2:
        raise ValueError("pooled wOBA calibration is not identifiable")
    intercept, slope = np.linalg.lstsq(
        weighted_design,
        actual * np.sqrt(weights),
        rcond=None,
    )[0]
    return {
        "woba_calibration_intercept": float(intercept),
        "woba_calibration_slope": float(slope),
    }


def calibration_improvement_gate(
    candidate: Mapping[str, Mapping[str, float | int | None]],
    c0: Mapping[str, Mapping[str, float | int | None]],
) -> dict[str, object]:
    """Require pooled calibration distance to improve in both weighting views."""

    comparisons: dict[str, object] = {}
    for weighting in ("player", "pa"):
        candidate_distance = calibration_distance(candidate[weighting])
        c0_distance = calibration_distance(c0[weighting])
        delta = candidate_distance - c0_distance
        comparisons[weighting] = {
            "candidate_distance": candidate_distance,
            "c0_distance": c0_distance,
            "candidate_minus_c0": delta,
            "pass": delta < -STRICT_IMPROVEMENT_TOLERANCE,
        }
    return {
        "comparisons": comparisons,
        "pass": all(bool(value["pass"]) for value in comparisons.values()),
    }


def supported_level_reversal_gate(
    candidate: Mapping[str, float | int | None],
    b0: Mapping[str, float | int | None],
    b1: Mapping[str, float | int | None],
) -> dict[str, object]:
    """Reject the two frozen definitions of a material supported-level reversal."""

    deltas = {
        metric: float(candidate[metric])
        - min(float(b0[metric]), float(b1[metric]))
        for metric in (
            "woba_rmse",
            "runs_per_600_rmse",
            "terminal_log_loss",
            "terminal_brier_score",
        )
    }
    rate_reversal = (
        deltas["woba_rmse"] > MATERIAL_WOBA_RMSE_REVERSAL
        and deltas["runs_per_600_rmse"] > MATERIAL_RUNS_RMSE_REVERSAL
    )
    proper_score_reversal = (
        deltas["terminal_log_loss"] > MATERIAL_LOG_LOSS_REVERSAL
        and deltas["terminal_brier_score"] > MATERIAL_BRIER_REVERSAL
    )
    return {
        "candidate_minus_strongest_baseline": deltas,
        "rate_reversal": rate_reversal,
        "proper_score_reversal": proper_score_reversal,
        "pass": not rate_reversal and not proper_score_reversal,
    }


def richer_ablation_gate(
    richer: Mapping[str, Mapping[str, float | int | None]],
    d0: Mapping[str, Mapping[str, float | int | None]],
) -> dict[str, object]:
    """Require richer shape features to add proper-score value on identical rows."""

    comparisons: dict[str, object] = {}
    for weighting in ("player", "pa"):
        view: dict[str, object] = {}
        for metric in PROPER_SCORE_METRICS:
            richer_value = float(richer[weighting][metric])
            d0_value = float(d0[weighting][metric])
            view[metric] = {
                "richer": richer_value,
                "d0": d0_value,
                "richer_minus_d0": richer_value - d0_value,
                "pass": richer_value - d0_value < -STRICT_IMPROVEMENT_TOLERANCE,
            }
        richer_rmse = float(richer[weighting]["woba_rmse"])
        d0_rmse = float(d0[weighting]["woba_rmse"])
        relative = (richer_rmse - d0_rmse) / d0_rmse
        view["woba_rmse"] = {
            "richer": richer_rmse,
            "d0": d0_rmse,
            "relative_worsening": relative,
            "maximum_allowed": RICHER_WOBA_RMSE_RELATIVE_TOLERANCE,
            "pass": relative <= RICHER_WOBA_RMSE_RELATIVE_TOLERANCE,
        }
        view["pass"] = all(bool(view[metric]["pass"]) for metric in (
            *PROPER_SCORE_METRICS,
            "woba_rmse",
        ))
        comparisons[weighting] = view
    return {
        "comparisons": comparisons,
        "pass": all(bool(value["pass"]) for value in comparisons.values()),
    }
