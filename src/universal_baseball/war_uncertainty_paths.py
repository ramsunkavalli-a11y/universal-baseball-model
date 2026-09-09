"""Phase 1 moment-based annual WAR uncertainty for universal paths."""

from __future__ import annotations

import math
from statistics import NormalDist

import polars as pl


UNCERTAINTY_MODEL_ID = "phase1_empirical_opportunity_posterior_rate_v1"
CENTRAL_COVERAGE = 0.80
_Z = NormalDist().inv_cdf((1.0 + CENTRAL_COVERAGE) / 2.0)

COMPONENT_UNCERTAINTY_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "season": pl.Int64,
    "horizon": pl.Int64,
    "projection_component": pl.String,
    "projected_war_mean": pl.Float64,
    "projected_war_lower": pl.Float64,
    "projected_war_upper": pl.Float64,
    "annual_war_variance": pl.Float64,
    "opportunity_war_variance": pl.Float64,
    "performance_war_variance": pl.Float64,
    "central_reference_coverage": pl.Float64,
    "uncertainty_model_id": pl.String,
}

WHOLE_PLAYER_UNCERTAINTY_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "season": pl.Int64,
    "projected_war_mean": pl.Float64,
    "projected_war_lower": pl.Float64,
    "projected_war_upper": pl.Float64,
    "annual_war_variance": pl.Float64,
    "opportunity_war_variance": pl.Float64,
    "performance_war_variance": pl.Float64,
    "central_reference_coverage": pl.Float64,
    "uncertainty_model_id": pl.String,
}


def build_component_war_uncertainty(
    paths: pl.DataFrame,
    *,
    component: str,
    conditional_workload_column: str,
    conditional_workload_variance_column: str,
    conditional_war_rate_column: str,
    workload_unit: float,
    runs_per_win: float,
) -> pl.DataFrame:
    """Propagate empirical opportunity spread and rate posterior uncertainty."""

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
        raise ValueError(f"{component} uncertainty input missing fields: {missing}")
    if not component or not math.isfinite(workload_unit) or workload_unit <= 0:
        raise ValueError("component and workload unit must be valid")
    if not math.isfinite(runs_per_win) or runs_per_win <= 0:
        raise ValueError("runs per win must be finite and positive")
    if paths.group_by("player_id", "season").len().filter(pl.col("len") != 1).height:
        raise ValueError(f"{component} uncertainty input violates player-season grain")

    rows: list[dict[str, object]] = []
    for row in paths.iter_rows(named=True):
        probability = float(row["mlb_active_probability"])
        conditional_workload = float(row[conditional_workload_column])
        conditional_variance = float(row[conditional_workload_variance_column])
        conditional_rate = float(row[conditional_war_rate_column])
        event_run_variance = float(row["event_run_variance"])
        posterior_rate_variance = float(row["posterior_run_rate_variance"])
        values = (
            probability,
            conditional_workload,
            conditional_variance,
            conditional_rate,
            event_run_variance,
            posterior_rate_variance,
        )
        if (
            any(not math.isfinite(value) for value in values)
            or not 0.0 <= probability <= 1.0
            or min(
                conditional_workload,
                conditional_variance,
                event_run_variance,
                posterior_rate_variance,
            )
            < 0.0
        ):
            raise ValueError(f"{component} uncertainty input contains invalid values")

        expected_workload = probability * conditional_workload
        expected_workload_squared = probability * (
            conditional_variance + conditional_workload * conditional_workload
        )
        workload_variance = max(
            0.0, expected_workload_squared - expected_workload * expected_workload
        )
        war_per_workload = conditional_rate / workload_unit
        opportunity_variance = workload_variance * war_per_workload * war_per_workload
        expected_pair_count = max(
            0.0, expected_workload_squared - expected_workload
        )
        performance_variance = (
            expected_workload * event_run_variance
            + expected_pair_count * posterior_rate_variance
        ) / (runs_per_win * runs_per_win)
        total_variance = opportunity_variance + performance_variance
        point = float(row["expected_war"])
        identity = expected_workload * war_per_workload
        if not math.isclose(point, identity, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError(f"{component} expected WAR identity does not reconcile")
        spread = _Z * math.sqrt(total_variance)
        rows.append(
            {
                "as_of_date": row["as_of_date"],
                "player_id": int(row["player_id"]),
                "season": int(row["season"]),
                "horizon": int(row["horizon"]),
                "projection_component": component,
                "projected_war_mean": point,
                "projected_war_lower": point - spread,
                "projected_war_upper": point + spread,
                "annual_war_variance": total_variance,
                "opportunity_war_variance": opportunity_variance,
                "performance_war_variance": performance_variance,
                "central_reference_coverage": CENTRAL_COVERAGE,
                "uncertainty_model_id": UNCERTAINTY_MODEL_ID,
            }
        )
    return pl.DataFrame(rows, schema=COMPONENT_UNCERTAINTY_SCHEMA).sort(
        ["player_id", "season"]
    )


def build_whole_player_war_uncertainty(
    components: pl.DataFrame,
) -> pl.DataFrame:
    """Add hitter and pitcher means/variances without claiming covariance."""

    missing = sorted(set(COMPONENT_UNCERTAINTY_SCHEMA) - set(components.columns))
    if missing:
        raise ValueError(f"component uncertainty missing fields: {missing}")
    source = components.select(list(COMPONENT_UNCERTAINTY_SCHEMA)).cast(
        COMPONENT_UNCERTAINTY_SCHEMA, strict=True
    )
    if source.group_by("player_id", "season", "projection_component").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("component uncertainty violates player-season-component grain")
    combined = source.group_by("as_of_date", "player_id", "season").agg(
        pl.col("projected_war_mean").sum(),
        pl.col("annual_war_variance").sum(),
        pl.col("opportunity_war_variance").sum(),
        pl.col("performance_war_variance").sum(),
    ).with_columns(
        (_Z * pl.col("annual_war_variance").sqrt()).alias("spread"),
    ).with_columns(
        (pl.col("projected_war_mean") - pl.col("spread")).alias(
            "projected_war_lower"
        ),
        (pl.col("projected_war_mean") + pl.col("spread")).alias(
            "projected_war_upper"
        ),
        pl.lit(CENTRAL_COVERAGE).alias("central_reference_coverage"),
        pl.lit(UNCERTAINTY_MODEL_ID).alias("uncertainty_model_id"),
    ).select(list(WHOLE_PLAYER_UNCERTAINTY_SCHEMA))
    return combined.cast(WHOLE_PLAYER_UNCERTAINTY_SCHEMA, strict=True).sort(
        ["player_id", "season"]
    )
