"""Universal projection-path validation and historical plausibility diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

import polars as pl


PROJECTION_PATH_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "season": pl.Int64,
    "projection_component": pl.String,
    "role": pl.String,
    "workload_measure": pl.String,
    "mlb_active_probability": pl.Float64,
    "conditional_war_rate": pl.Float64,
    "conditional_workload": pl.Float64,
    "workload_unit": pl.Float64,
    "expected_war": pl.Float64,
    "is_controlled_season": pl.Boolean,
    "coverage_tier": pl.String,
    "probability_model_id": pl.String,
    "workload_model_id": pl.String,
    "talent_model_id": pl.String,
    "uses_current_team_depth": pl.Boolean,
}

HISTORICAL_PLAUSIBILITY_INPUT_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "player_id": pl.Int64,
    "projection_component": pl.String,
    "role": pl.String,
    "workload_measure": pl.String,
    "workload": pl.Float64,
    "workload_unit": pl.Float64,
    "context_neutral_war": pl.Float64,
}

HISTORICAL_PLAUSIBILITY_REFERENCE_SCHEMA: dict[str, pl.DataType] = {
    "projection_component": pl.String,
    "role": pl.String,
    "workload_measure": pl.String,
    "history_start_season": pl.Int64,
    "history_end_season": pl.Int64,
    "active_player_seasons": pl.Int64,
    "workload_unit": pl.Float64,
    "workload_high_quantile": pl.Float64,
    "workload_observed_max": pl.Float64,
    "war_rate_low_quantile": pl.Float64,
    "war_rate_high_quantile": pl.Float64,
    "annual_war_high_quantile": pl.Float64,
    "low_quantile": pl.Float64,
    "high_quantile": pl.Float64,
    "reference_status": pl.String,
}

PROJECTION_PLAUSIBILITY_SCHEMA: dict[str, pl.DataType] = {
    **PROJECTION_PATH_SCHEMA,
    **{
        key: value
        for key, value in HISTORICAL_PLAUSIBILITY_REFERENCE_SCHEMA.items()
        if key not in {"projection_component", "role", "workload_measure", "workload_unit"}
    },
    "war_identity_difference": pl.Float64,
    "workload_above_high_quantile": pl.Boolean,
    "workload_above_observed_max": pl.Boolean,
    "war_rate_below_low_quantile": pl.Boolean,
    "war_rate_above_high_quantile": pl.Boolean,
    "expected_war_above_high_quantile": pl.Boolean,
    "plausibility_status": pl.String,
    "plausibility_reasons": pl.String,
}

PROJECTION_PATH_SUMMARY_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "forecast_start_season": pl.Int64,
    "forecast_end_season": pl.Int64,
    "component_rows": pl.Int64,
    "expected_war": pl.Float64,
    "controlled_expected_war": pl.Float64,
    "review_rows": pl.Int64,
    "coverage_tiers": pl.String,
    "path_status": pl.String,
}


@dataclass(frozen=True)
class ProjectionGuardrailResult:
    annual: pl.DataFrame
    paths: pl.DataFrame
    reviews: pl.DataFrame


def _finite_columns(frame: pl.DataFrame, columns: Iterable[str]) -> bool:
    for column in columns:
        values = frame.get_column(column).drop_nulls().to_list()
        if any(not isfinite(float(value)) for value in values):
            return False
    return True


def build_historical_plausibility_reference(
    history: pl.DataFrame,
    *,
    forecast_year: int,
    low_quantile: float = 0.01,
    high_quantile: float = 0.99,
    minimum_active_player_seasons: int = 30,
) -> pl.DataFrame:
    """Build pre-forecast role references used only to flag unusual projections."""

    missing = sorted(set(HISTORICAL_PLAUSIBILITY_INPUT_SCHEMA) - set(history.columns))
    if missing:
        raise ValueError(f"historical plausibility input missing columns: {missing}")
    if not 0.0 <= low_quantile < high_quantile <= 1.0:
        raise ValueError("historical plausibility quantiles are invalid")
    if minimum_active_player_seasons < 1:
        raise ValueError("minimum historical active sample must be positive")
    source = history.select(list(HISTORICAL_PLAUSIBILITY_INPUT_SCHEMA)).cast(
        HISTORICAL_PLAUSIBILITY_INPUT_SCHEMA, strict=True
    )
    if source.is_empty():
        return pl.DataFrame(schema=HISTORICAL_PLAUSIBILITY_REFERENCE_SCHEMA)
    required = [
        "season",
        "player_id",
        "projection_component",
        "role",
        "workload_measure",
        "workload",
        "workload_unit",
        "context_neutral_war",
    ]
    if sum(source.select(required).null_count().row(0)):
        raise ValueError("historical plausibility input has null required values")
    if source.filter(pl.col("season") >= forecast_year).height:
        raise ValueError("historical plausibility input crosses the forecast year")
    if (
        source.group_by(["season", "player_id", "projection_component"])
        .len()
        .filter(pl.col("len") > 1)
        .height
    ):
        raise ValueError("historical plausibility input has duplicate component seasons")
    if source.filter(
        (pl.col("player_id") <= 0)
        | (pl.col("workload") < 0)
        | (pl.col("workload_unit") <= 0)
        | (pl.col("projection_component") == "")
        | (pl.col("role") == "")
        | (pl.col("workload_measure") == "")
    ).height or not _finite_columns(
        source, ["workload", "workload_unit", "context_neutral_war"]
    ):
        raise ValueError("historical plausibility input has invalid values")

    rows: list[dict[str, object]] = []
    for group in source.partition_by(
        ["projection_component", "role", "workload_measure"], maintain_order=True
    ):
        first = group.row(0, named=True)
        if group.get_column("workload_unit").n_unique() != 1:
            raise ValueError("historical role group has inconsistent workload units")
        active = group.filter(pl.col("workload") > 0).with_columns(
            (
                pl.col("context_neutral_war")
                * pl.col("workload_unit")
                / pl.col("workload")
            ).alias("war_rate")
        )
        enough = active.height >= minimum_active_player_seasons
        rows.append(
            {
                "projection_component": first["projection_component"],
                "role": first["role"],
                "workload_measure": first["workload_measure"],
                "history_start_season": int(group.get_column("season").min()),
                "history_end_season": int(group.get_column("season").max()),
                "active_player_seasons": active.height,
                "workload_unit": float(first["workload_unit"]),
                "workload_high_quantile": (
                    float(active.get_column("workload").quantile(high_quantile))
                    if enough
                    else None
                ),
                "workload_observed_max": (
                    float(active.get_column("workload").max()) if enough else None
                ),
                "war_rate_low_quantile": (
                    float(active.get_column("war_rate").quantile(low_quantile))
                    if enough
                    else None
                ),
                "war_rate_high_quantile": (
                    float(active.get_column("war_rate").quantile(high_quantile))
                    if enough
                    else None
                ),
                "annual_war_high_quantile": (
                    float(group.get_column("context_neutral_war").quantile(high_quantile))
                    if enough
                    else None
                ),
                "low_quantile": low_quantile,
                "high_quantile": high_quantile,
                "reference_status": "available" if enough else "insufficient_sample",
            }
        )
    return pl.DataFrame(
        rows, schema=HISTORICAL_PLAUSIBILITY_REFERENCE_SCHEMA
    ).sort(["projection_component", "role", "workload_measure"])


def audit_projection_paths(
    projections: pl.DataFrame,
    universe: pl.DataFrame,
    historical_reference: pl.DataFrame,
    *,
    forecast_years: Iterable[int],
    reconciliation_tolerance: float = 1e-10,
) -> ProjectionGuardrailResult:
    """Fail mechanical errors and flag, without changing, historical extremes."""

    years = tuple(sorted(set(int(year) for year in forecast_years)))
    if not years:
        raise ValueError("projection guardrails require forecast years")
    if reconciliation_tolerance <= 0:
        raise ValueError("WAR reconciliation tolerance must be positive")
    if set(universe.columns) != {"player_id"}:
        raise ValueError("projection universe must contain only player_id")
    players = universe.cast({"player_id": pl.Int64}, strict=True)
    if players.is_empty() or players.filter(
        pl.col("player_id").is_null() | (pl.col("player_id") <= 0)
    ).height:
        raise ValueError("projection universe has invalid player IDs")
    if players.get_column("player_id").n_unique() != players.height:
        raise ValueError("projection universe has duplicate player IDs")

    missing = sorted(set(PROJECTION_PATH_SCHEMA) - set(projections.columns))
    if missing:
        raise ValueError(f"projection path missing columns: {missing}")
    source = projections.select(list(PROJECTION_PATH_SCHEMA)).cast(
        PROJECTION_PATH_SCHEMA, strict=True
    )
    required = [column for column in PROJECTION_PATH_SCHEMA]
    if source.is_empty() or sum(source.select(required).null_count().row(0)):
        raise ValueError("projection path is empty or has null required values")
    if source.get_column("as_of_date").n_unique() != 1:
        raise ValueError("projection path requires one as-of date")
    if set(source.get_column("season").unique().to_list()) != set(years):
        raise ValueError("projection path seasons differ from the required horizon")
    if (
        source.group_by(["player_id", "season", "projection_component"])
        .len()
        .filter(pl.col("len") > 1)
        .height
    ):
        raise ValueError("projection path duplicates a player-season component")
    if source.filter(
        (pl.col("player_id") <= 0)
        | ~pl.col("projection_component").is_in(["hitter", "pitcher"])
        | ~pl.col("workload_measure").is_in(["PA", "BF"])
        | (
            (pl.col("projection_component") == "hitter")
            & (pl.col("workload_measure") != "PA")
        )
        | (
            (pl.col("projection_component") == "pitcher")
            & (pl.col("workload_measure") != "BF")
        )
        | ~pl.col("mlb_active_probability").is_between(0.0, 1.0, closed="both")
        | (pl.col("conditional_workload") < 0)
        | (pl.col("workload_unit") <= 0)
        | (pl.col("role") == "")
        | (pl.col("coverage_tier") == "")
        | (pl.col("probability_model_id") == "")
        | (pl.col("workload_model_id") == "")
        | (pl.col("talent_model_id") == "")
    ).height or not _finite_columns(
        source,
        [
            "mlb_active_probability",
            "conditional_war_rate",
            "conditional_workload",
            "workload_unit",
            "expected_war",
        ],
    ):
        raise ValueError("projection path has invalid component values")
    if source.filter(pl.col("uses_current_team_depth")).height:
        raise ValueError("intrinsic projection path uses current-team depth")

    universe_ids = set(players.get_column("player_id").to_list())
    source_ids = set(source.get_column("player_id").to_list())
    if source_ids != universe_ids:
        raise ValueError("projection path player coverage differs from the rights universe")
    observed_player_years = set(
        source.select("player_id", "season").unique().iter_rows()
    )
    required_player_years = {(player, year) for player in universe_ids for year in years}
    if observed_player_years != required_player_years:
        raise ValueError("projection path does not cover every player-year")

    source = source.with_columns(
        (
            pl.col("mlb_active_probability")
            * pl.col("conditional_war_rate")
            * pl.col("conditional_workload")
            / pl.col("workload_unit")
        ).alias("reconciled_expected_war")
    ).with_columns(
        (pl.col("expected_war") - pl.col("reconciled_expected_war")).alias(
            "war_identity_difference"
        )
    )
    if source.filter(
        pl.col("war_identity_difference").abs()
        > reconciliation_tolerance
        * pl.max_horizontal(pl.lit(1.0), pl.col("expected_war").abs())
    ).height:
        raise ValueError("projection expected WAR does not reconcile to path components")

    reference = historical_reference.select(
        list(HISTORICAL_PLAUSIBILITY_REFERENCE_SCHEMA)
    ).cast(HISTORICAL_PLAUSIBILITY_REFERENCE_SCHEMA, strict=True)
    if (
        reference.group_by(["projection_component", "role", "workload_measure"])
        .len()
        .filter(pl.col("len") > 1)
        .height
    ):
        raise ValueError("historical plausibility reference has duplicate role keys")
    if reference.filter(pl.col("history_end_season") >= min(years)).height:
        raise ValueError("historical plausibility reference crosses the forecast horizon")

    joined = source.join(
        reference,
        on=["projection_component", "role", "workload_measure"],
        how="left",
        suffix="_history",
    )
    if joined.filter(
        pl.col("workload_unit_history").is_not_null()
        & (
            (pl.col("workload_unit") - pl.col("workload_unit_history")).abs()
            > reconciliation_tolerance
        )
    ).height:
        raise ValueError("projection and historical workload units differ")

    annual_rows: list[dict[str, object]] = []
    for raw in joined.iter_rows(named=True):
        row = dict(raw)
        available = row["reference_status"] == "available"
        flags = {
            "workload_above_high_quantile": available
            and row["conditional_workload"] > row["workload_high_quantile"],
            "workload_above_observed_max": available
            and row["conditional_workload"] > row["workload_observed_max"],
            "war_rate_below_low_quantile": available
            and row["conditional_war_rate"] < row["war_rate_low_quantile"],
            "war_rate_above_high_quantile": available
            and row["conditional_war_rate"] > row["war_rate_high_quantile"],
            "expected_war_above_high_quantile": available
            and row["expected_war"] > row["annual_war_high_quantile"],
        }
        reasons = [name for name, flagged in flags.items() if flagged]
        if row["reference_status"] is None:
            status = "review_missing_historical_reference"
            reasons.append("missing_historical_reference")
        elif row["reference_status"] != "available":
            status = "review_insufficient_historical_reference"
            reasons.append("insufficient_historical_reference")
        elif reasons:
            status = "review_historical_extreme"
        else:
            status = "available"
        annual_rows.append(
            {
                **{column: row[column] for column in PROJECTION_PATH_SCHEMA},
                **{
                    column: row[column]
                    for column in HISTORICAL_PLAUSIBILITY_REFERENCE_SCHEMA
                    if column
                    not in {
                        "projection_component",
                        "role",
                        "workload_measure",
                        "workload_unit",
                    }
                },
                "war_identity_difference": row["war_identity_difference"],
                **flags,
                "plausibility_status": status,
                "plausibility_reasons": ",".join(reasons),
            }
        )
    annual = pl.DataFrame(annual_rows, schema=PROJECTION_PLAUSIBILITY_SCHEMA).sort(
        ["player_id", "season", "projection_component"]
    )

    path_rows: list[dict[str, object]] = []
    for group in annual.partition_by("player_id", maintain_order=True):
        first = group.row(0, named=True)
        reviews = group.filter(pl.col("plausibility_status") != "available").height
        path_rows.append(
            {
                "as_of_date": first["as_of_date"],
                "player_id": first["player_id"],
                "forecast_start_season": min(years),
                "forecast_end_season": max(years),
                "component_rows": group.height,
                "expected_war": float(group.get_column("expected_war").sum()),
                "controlled_expected_war": float(
                    group.filter(pl.col("is_controlled_season"))
                    .get_column("expected_war")
                    .sum()
                ),
                "review_rows": reviews,
                "coverage_tiers": ",".join(
                    sorted(set(group.get_column("coverage_tier").to_list()))
                ),
                "path_status": "available" if reviews == 0 else "review",
            }
        )
    paths = pl.DataFrame(path_rows, schema=PROJECTION_PATH_SUMMARY_SCHEMA).sort(
        "player_id"
    )
    reviews = annual.filter(pl.col("plausibility_status") != "available")
    return ProjectionGuardrailResult(annual=annual, paths=paths, reviews=reviews)
