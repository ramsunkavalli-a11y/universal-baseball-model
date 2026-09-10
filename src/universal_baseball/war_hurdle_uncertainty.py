"""Zero-inflated annual WAR reference intervals for research comparison."""

from __future__ import annotations

import math
from statistics import NormalDist

import polars as pl

from universal_baseball.war_uncertainty_paths import COMPONENT_UNCERTAINTY_SCHEMA


UNCERTAINTY_MODEL_ID = "zero_mass_active_normal_war_reference_v1"
CENTRAL_COVERAGE = 0.80


def hurdle_normal_quantile(
    probability: float,
    *,
    active_probability: float,
    active_mean: float,
    active_standard_deviation: float,
) -> float:
    """Quantile of an inactive-zero/active-normal mixture."""

    values = (probability, active_probability, active_mean, active_standard_deviation)
    if any(not math.isfinite(value) for value in values):
        raise ValueError("hurdle quantile inputs must be finite")
    if not 0 < probability < 1 or not 0 <= active_probability <= 1:
        raise ValueError("hurdle probabilities are outside valid bounds")
    if active_standard_deviation < 0:
        raise ValueError("active standard deviation cannot be negative")
    if active_probability == 0:
        return 0.0
    if active_standard_deviation == 0:
        points = sorted(((0.0, 1.0 - active_probability), (active_mean, active_probability)))
        cumulative = 0.0
        for value, mass in points:
            cumulative += mass
            if probability <= cumulative:
                return value
        return points[-1][0]

    normal = NormalDist()
    active_below_zero = active_probability * normal.cdf(
        -active_mean / active_standard_deviation
    )
    zero_jump_top = active_below_zero + 1.0 - active_probability
    if active_below_zero <= probability <= zero_jump_top:
        return 0.0
    if probability < active_below_zero:
        active_quantile = probability / active_probability
    else:
        active_quantile = (probability - (1.0 - active_probability)) / active_probability
    active_quantile = min(1.0 - 1e-12, max(1e-12, active_quantile))
    return active_mean + active_standard_deviation * normal.inv_cdf(active_quantile)


def build_component_hurdle_war_uncertainty(
    paths: pl.DataFrame,
    *,
    component: str,
    conditional_workload_column: str,
    conditional_workload_variance_column: str,
    conditional_war_rate_column: str,
    workload_unit: float,
    runs_per_win: float,
) -> pl.DataFrame:
    """Build a point-preserving zero-mass plus active-normal interval."""

    required = {
        "as_of_date",
        "player_id",
        "season",
        "horizon",
        "mlb_active_probability",
        conditional_workload_column,
        conditional_workload_variance_column,
        conditional_war_rate_column,
        "expected_war",
        "event_run_variance",
        "posterior_run_rate_variance",
    }
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"{component} hurdle uncertainty missing fields: {missing}")
    if workload_unit <= 0 or runs_per_win <= 0:
        raise ValueError("hurdle uncertainty scales must be positive")
    rows = []
    for row in paths.iter_rows(named=True):
        active_probability = float(row["mlb_active_probability"])
        workload = float(row[conditional_workload_column])
        workload_variance = float(row[conditional_workload_variance_column])
        war_rate = float(row[conditional_war_rate_column]) / workload_unit
        event_variance = float(row["event_run_variance"])
        posterior_variance = float(row["posterior_run_rate_variance"])
        if (
            not 0 <= active_probability <= 1
            or min(workload, workload_variance, event_variance, posterior_variance) < 0
        ):
            raise ValueError("hurdle uncertainty inputs are invalid")
        active_mean = workload * war_rate
        active_pair_count = max(0.0, workload_variance + workload * workload - workload)
        active_performance_variance = (
            workload * event_variance + active_pair_count * posterior_variance
        ) / (runs_per_win * runs_per_win)
        active_variance = workload_variance * war_rate * war_rate + active_performance_variance
        total_variance = (
            active_probability * active_variance
            + active_probability * (1.0 - active_probability) * active_mean * active_mean
        )
        point = active_probability * active_mean
        if not math.isclose(point, float(row["expected_war"]), rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("hurdle uncertainty expected WAR identity does not reconcile")
        standard_deviation = math.sqrt(active_variance)
        rows.append(
            {
                "as_of_date": row["as_of_date"],
                "player_id": int(row["player_id"]),
                "season": int(row["season"]),
                "horizon": int(row["horizon"]),
                "projection_component": component,
                "projected_war_mean": point,
                "projected_war_lower": hurdle_normal_quantile(
                    0.10,
                    active_probability=active_probability,
                    active_mean=active_mean,
                    active_standard_deviation=standard_deviation,
                ),
                "projected_war_upper": hurdle_normal_quantile(
                    0.90,
                    active_probability=active_probability,
                    active_mean=active_mean,
                    active_standard_deviation=standard_deviation,
                ),
                "annual_war_variance": total_variance,
                "opportunity_war_variance": (
                    active_probability * workload_variance * war_rate * war_rate
                    + active_probability
                    * (1.0 - active_probability)
                    * active_mean
                    * active_mean
                ),
                "performance_war_variance": active_probability * active_performance_variance,
                "central_reference_coverage": CENTRAL_COVERAGE,
                "uncertainty_model_id": UNCERTAINTY_MODEL_ID,
            }
        )
    return pl.DataFrame(rows, schema=COMPONENT_UNCERTAINTY_SCHEMA).sort("player_id", "season")
