"""Zero-inflated annual WAR reference intervals for research comparison."""

from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import polars as pl

from universal_baseball.player_value_uncertainty import (
    sample_hurdle_plate_appearances,
)
from universal_baseball.war_uncertainty_paths import (
    COMPONENT_UNCERTAINTY_SCHEMA,
    WHOLE_PLAYER_UNCERTAINTY_SCHEMA,
)


UNCERTAINTY_MODEL_ID = "zero_mass_active_normal_war_reference_v1"
CENTRAL_COVERAGE = 0.80
SIMULATED_UNCERTAINTY_MODEL_ID = "exact_workload_performance_mixture_v1"


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
    performance_standard_deviation_multiplier: float = 1.0,
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
    if (
        workload_unit <= 0
        or runs_per_win <= 0
        or not math.isfinite(performance_standard_deviation_multiplier)
        or performance_standard_deviation_multiplier <= 0
    ):
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
        raw_active_performance_variance = (
            workload * event_variance + active_pair_count * posterior_variance
        ) / (runs_per_win * runs_per_win)
        active_performance_variance = (
            raw_active_performance_variance
            * performance_standard_deviation_multiplier
            * performance_standard_deviation_multiplier
        )
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
                "uncertainty_model_id": (
                    UNCERTAINTY_MODEL_ID
                    if performance_standard_deviation_multiplier == 1.0
                    else f"{UNCERTAINTY_MODEL_ID}_rolling_performance_scale"
                ),
            }
        )
    return pl.DataFrame(rows, schema=COMPONENT_UNCERTAINTY_SCHEMA).sort("player_id", "season")


def build_component_simulated_war_uncertainty(
    paths: pl.DataFrame,
    *,
    component: str,
    conditional_workload_column: str,
    conditional_workload_variance_column: str,
    conditional_war_rate_column: str,
    workload_unit: float,
    runs_per_win: float,
    nb_alpha: float | None = None,
    performance_standard_deviation_multiplier: float = 1.0,
    draws: int = 4_096,
    master_seed: int = 20250910,
) -> pl.DataFrame:
    """Simulate the exact workload mixture and conditional performance noise."""

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
        raise ValueError(f"{component} simulated uncertainty missing fields: {missing}")
    scales = (workload_unit, runs_per_win, performance_standard_deviation_multiplier)
    if nb_alpha is not None:
        scales += (nb_alpha,)
    if any(not math.isfinite(value) or value <= 0 for value in scales) or draws <= 0:
        raise ValueError("simulated uncertainty scales and draws must be positive")

    rows = []
    for row in paths.iter_rows(named=True):
        player_id = int(row["player_id"])
        season = int(row["season"])
        active_probability = float(row["mlb_active_probability"])
        workload = float(row[conditional_workload_column])
        workload_variance = float(row[conditional_workload_variance_column])
        war_rate = float(row[conditional_war_rate_column]) / workload_unit
        event_variance = float(row["event_run_variance"])
        posterior_variance = float(row["posterior_run_rate_variance"])
        if (
            not 0 <= active_probability <= 1
            or workload <= 1
            or min(workload_variance, event_variance, posterior_variance) < 0
        ):
            raise ValueError("simulated uncertainty inputs are invalid")
        active_mean = workload * war_rate
        point = active_probability * active_mean
        if not math.isclose(point, float(row["expected_war"]), rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("simulated uncertainty expected WAR identity does not reconcile")

        rng = np.random.Generator(
            np.random.PCG64(np.random.SeedSequence([master_seed, player_id, season]))
        )
        if nb_alpha is not None:
            sampled_workload = sample_hurdle_plate_appearances(
                rng,
                draws=draws,
                participation_probability=active_probability,
                positive_truncated_mean=workload,
                alpha=nb_alpha,
            )
            workload_distribution = "zero_truncated_nb2"
        else:
            participates = rng.random(draws) < active_probability
            sampled_workload = np.zeros(draws, dtype=np.float64)
            active_draws = int(participates.sum())
            if workload_variance == 0:
                sampled_workload[participates] = workload
            elif active_draws:
                shape = workload * workload / workload_variance
                scale = workload_variance / workload
                sampled_workload[participates] = rng.gamma(
                    shape, scale, size=active_draws
                )
            workload_distribution = "moment_matched_gamma"
        pair_count = np.maximum(
            0.0, sampled_workload * sampled_workload - sampled_workload
        )
        performance_variance = (
            sampled_workload * event_variance + pair_count * posterior_variance
        ) / (runs_per_win * runs_per_win)
        performance_noise = rng.normal(
            0.0,
            np.sqrt(performance_variance) * performance_standard_deviation_multiplier,
        )
        war = sampled_workload * war_rate + performance_noise
        quantiles = np.quantile(war, [0.10, 0.90], method="linear")
        lower = min(float(quantiles[0]), point)
        upper = max(float(quantiles[1]), point)

        active_pair_count = max(
            0.0, workload_variance + workload * workload - workload
        )
        active_performance_variance = (
            workload * event_variance + active_pair_count * posterior_variance
        ) / (runs_per_win * runs_per_win)
        active_performance_variance *= performance_standard_deviation_multiplier**2
        opportunity_variance = (
            active_probability * workload_variance * war_rate * war_rate
            + active_probability
            * (1.0 - active_probability)
            * active_mean
            * active_mean
        )
        total_performance_variance = active_probability * active_performance_variance
        rows.append(
            {
                "as_of_date": row["as_of_date"],
                "player_id": player_id,
                "season": season,
                "horizon": int(row["horizon"]),
                "projection_component": component,
                "projected_war_mean": point,
                "projected_war_lower": lower,
                "projected_war_upper": upper,
                "annual_war_variance": opportunity_variance
                + total_performance_variance,
                "opportunity_war_variance": opportunity_variance,
                "performance_war_variance": total_performance_variance,
                "central_reference_coverage": CENTRAL_COVERAGE,
                "uncertainty_model_id": (
                    f"{SIMULATED_UNCERTAINTY_MODEL_ID}:{workload_distribution}"
                ),
            }
        )
    return pl.DataFrame(rows, schema=COMPONENT_UNCERTAINTY_SCHEMA).sort(
        "player_id", "season"
    )


def build_whole_player_from_component_intervals(
    components: pl.DataFrame,
) -> pl.DataFrame:
    """Preserve simulated single-component ranges; moment-combine two-way players."""

    missing = sorted(set(COMPONENT_UNCERTAINTY_SCHEMA) - set(components.columns))
    if missing:
        raise ValueError(f"component uncertainty missing fields: {missing}")
    source = components.select(list(COMPONENT_UNCERTAINTY_SCHEMA)).cast(
        COMPONENT_UNCERTAINTY_SCHEMA, strict=True
    )
    rows = []
    z80 = NormalDist().inv_cdf(0.90)
    for group in source.partition_by("as_of_date", "player_id", "season"):
        if group.height == 1:
            row = group.row(0, named=True)
            lower = float(row["projected_war_lower"])
            upper = float(row["projected_war_upper"])
            model_id = str(row["uncertainty_model_id"])
        else:
            variance = float(group.get_column("annual_war_variance").sum())
            mean = float(group.get_column("projected_war_mean").sum())
            spread = z80 * math.sqrt(variance)
            lower, upper = mean - spread, mean + spread
            model_id = f"{SIMULATED_UNCERTAINTY_MODEL_ID}:two_way_independent_moments"
        rows.append(
            {
                "as_of_date": group.item(0, "as_of_date"),
                "player_id": int(group.item(0, "player_id")),
                "season": int(group.item(0, "season")),
                "projected_war_mean": float(
                    group.get_column("projected_war_mean").sum()
                ),
                "projected_war_lower": lower,
                "projected_war_upper": upper,
                "annual_war_variance": float(
                    group.get_column("annual_war_variance").sum()
                ),
                "opportunity_war_variance": float(
                    group.get_column("opportunity_war_variance").sum()
                ),
                "performance_war_variance": float(
                    group.get_column("performance_war_variance").sum()
                ),
                "central_reference_coverage": CENTRAL_COVERAGE,
                "uncertainty_model_id": model_id,
            }
        )
    return pl.DataFrame(rows, schema=WHOLE_PLAYER_UNCERTAINTY_SCHEMA).sort(
        "player_id", "season"
    )
