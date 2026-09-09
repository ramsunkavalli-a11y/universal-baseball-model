"""Universal, team-neutral multi-year hitter MLB opportunity paths.

The selected Playing Time v1 hurdle model remains the preferred next-season
forecast where its required inputs exist.  This module fills the rest of the
rights universe, and later horizons, from pre-cutoff historical cohorts.  It
does not use team depth, change batting skill, or cap plate appearances.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import floor, isfinite
from typing import Iterable

import polars as pl

from universal_baseball.projection_guardrails import PROJECTION_PATH_SCHEMA
from universal_baseball.player_value_uncertainty import (
    NB2_ALPHA,
    zero_truncated_nb2_variance,
)


HITTER_OPPORTUNITY_HISTORY_SCHEMA: dict[str, pl.DataType] = {
    "snapshot_year": pl.Int64,
    "player_id": pl.Int64,
    "age_years": pl.Float64,
    "as_of_level_group": pl.String,
    "horizon": pl.Int64,
    "future_mlb_pa": pl.Float64,
}

HITTER_OPPORTUNITY_SNAPSHOT_SCHEMA: dict[str, pl.DataType] = {
    "snapshot_year": pl.Int64,
    "player_id": pl.Int64,
    "age_years": pl.Float64,
    "as_of_level_group": pl.String,
}

HITTER_MLB_PA_OUTCOME_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "player_id": pl.Int64,
    "batting_pa": pl.Float64,
}

HITTER_OPPORTUNITY_UNIVERSE_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "age_years": pl.Float64,
    "as_of_level_group": pl.String,
}

SELECTED_NEXT_YEAR_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "predicted_any_mlb_pa_probability": pl.Float64,
    "predicted_positive_mlb_pa_mean": pl.Float64,
}

HITTER_OPPORTUNITY_REFERENCE_SCHEMA: dict[str, pl.DataType] = {
    "horizon": pl.Int64,
    "level_tier": pl.String,
    "age_band_start": pl.Int64,
    "reference_level": pl.String,
    "observation_count": pl.Int64,
    "positive_count": pl.Int64,
    "mlb_active_probability": pl.Float64,
    "conditional_mlb_pa": pl.Float64,
    "conditional_mlb_pa_variance": pl.Float64,
}

HITTER_OPPORTUNITY_PATH_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "season": pl.Int64,
    "horizon": pl.Int64,
    "mlb_active_probability": pl.Float64,
    "conditional_mlb_pa": pl.Float64,
    "conditional_mlb_pa_variance": pl.Float64,
    "expected_mlb_pa": pl.Float64,
    "coverage_tier": pl.String,
    "probability_model_id": pl.String,
    "workload_model_id": pl.String,
    "uses_current_team_depth": pl.Boolean,
}

HITTER_CONDITIONAL_WAR_RATE_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "conditional_war_per_600_pa": pl.Float64,
    "talent_model_id": pl.String,
}

HITTER_CONTROL_SEASON_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "is_controlled_season": pl.Boolean,
}


@dataclass(frozen=True, slots=True)
class HitterOpportunityFit:
    references: pl.DataFrame
    horizons: tuple[int, ...]
    age_band_width: int
    participation_prior_players: float
    workload_prior_positive_players: float


def hitter_level_tier(value: object) -> str:
    """Map source labels to broad, stable opportunity states."""

    if value is None:
        return "UNKNOWN"
    normalized = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    if normalized in {"MLB", "MAJOR", "MAJORS", "MAJOR_LEAGUE"}:
        return "MLB"
    if normalized in {"AAA", "TRIPLE_A"}:
        return "AAA"
    if normalized in {"AA", "DOUBLE_A"}:
        return "AA"
    if normalized in {
        "A_OR_BELOW",
        "A",
        "HIGH_A",
        "SINGLE_A",
        "LOW_A",
        "ROOKIE",
        "ROOKIE_COMPLEX",
    }:
        return "A_OR_BELOW"
    if normalized in {"INACTIVE", "RETIRED", "RESTRICTED", "NO_ACTIVE_LEVEL"}:
        return "INACTIVE"
    return "UNKNOWN"


def _age_band(age: object, width: int) -> int | None:
    if age is None:
        return None
    numeric = float(age)
    if not isfinite(numeric) or not 15.0 <= numeric <= 60.0:
        raise ValueError("hitter opportunity age must be between 15 and 60 when known")
    return int(floor(numeric / width) * width)


def _smoothed_rate(successes: float, count: int, prior: float, strength: float) -> float:
    return (float(successes) + strength * float(prior)) / (int(count) + strength)


def _smoothed_variance(
    values: pl.Series,
    *,
    mean: float,
    prior_mean: float,
    prior_variance: float,
    strength: float,
) -> float:
    """Shrink the conditional second moment with the same workload prior."""

    second_sum = float((values.cast(pl.Float64) ** 2).sum() or 0.0)
    prior_second = prior_variance + prior_mean * prior_mean
    second = (second_sum + strength * prior_second) / (len(values) + strength)
    return max(0.0, second - mean * mean)


def build_hitter_opportunity_history(
    snapshots: pl.DataFrame,
    mlb_pa_outcomes: pl.DataFrame,
    *,
    horizons: Iterable[int],
    completed_seasons: Iterable[int],
) -> pl.DataFrame:
    """Attach future MLB PA, including zero, to dated affiliated-player cohorts."""

    wanted_horizons = tuple(sorted(set(int(value) for value in horizons)))
    complete = {int(value) for value in completed_seasons}
    if not wanted_horizons or any(value < 1 for value in wanted_horizons):
        raise ValueError("hitter opportunity horizons must be positive")

    def select_contract(
        frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str
    ) -> pl.DataFrame:
        missing = sorted(set(schema) - set(frame.columns))
        if missing:
            raise ValueError(f"{label} missing fields: {missing}")
        return frame.select(list(schema)).cast(schema, strict=True)

    cohorts = select_contract(
        snapshots, HITTER_OPPORTUNITY_SNAPSHOT_SCHEMA, "hitter opportunity snapshots"
    )
    outcomes = select_contract(
        mlb_pa_outcomes, HITTER_MLB_PA_OUTCOME_SCHEMA, "hitter MLB PA outcomes"
    )
    if cohorts.is_empty():
        raise ValueError("hitter opportunity snapshots must not be empty")
    if (
        cohorts.group_by(["snapshot_year", "player_id"])
        .len()
        .filter(pl.col("len") != 1)
        .height
    ):
        raise ValueError("hitter opportunity snapshots violate snapshot-player grain")
    if sum(
        cohorts.select("snapshot_year", "player_id", "as_of_level_group")
        .null_count()
        .row(0)
    ) or cohorts.filter(pl.col("player_id") <= 0).height:
        raise ValueError("hitter opportunity snapshots contain invalid values")
    if (
        outcomes.group_by(["season", "player_id"])
        .len()
        .filter(pl.col("len") != 1)
        .height
    ):
        raise ValueError("hitter MLB PA outcomes violate season-player grain")
    if outcomes.filter(
        pl.col("season").is_null()
        | pl.col("player_id").is_null()
        | (pl.col("player_id") <= 0)
        | pl.col("batting_pa").is_null()
        | ~pl.col("batting_pa").is_finite()
        | (pl.col("batting_pa") < 0)
    ).height:
        raise ValueError("hitter MLB PA outcomes contain invalid values")

    grid = cohorts.join(
        pl.DataFrame({"horizon": wanted_horizons}, schema={"horizon": pl.Int64}),
        how="cross",
    ).with_columns((pl.col("snapshot_year") + pl.col("horizon")).alias("target_year"))
    grid = grid.filter(pl.col("target_year").is_in(sorted(complete)))
    if grid.is_empty():
        raise ValueError("hitter opportunity has no certified complete target rows")
    missing_horizons = sorted(set(wanted_horizons) - set(grid["horizon"].unique().to_list()))
    if missing_horizons:
        raise ValueError(
            f"hitter opportunity has no certified targets for horizons: {missing_horizons}"
        )
    target_outcomes = outcomes.rename(
        {"season": "target_year", "batting_pa": "future_mlb_pa"}
    )
    return (
        grid.join(
            target_outcomes,
            on=["target_year", "player_id"],
            how="left",
            validate="m:1",
        )
        .with_columns(pl.col("future_mlb_pa").fill_null(0.0))
        .select(list(HITTER_OPPORTUNITY_HISTORY_SCHEMA))
        .cast(HITTER_OPPORTUNITY_HISTORY_SCHEMA, strict=True)
        .sort(["snapshot_year", "player_id", "horizon"])
    )


def fit_hitter_opportunity_fallbacks(
    history: pl.DataFrame,
    *,
    forecast_year: int,
    horizons: Iterable[int],
    age_band_width: int = 2,
    participation_prior_players: float = 50.0,
    workload_prior_positive_players: float = 20.0,
) -> HitterOpportunityFit:
    """Fit horizon-specific empirical fallbacks from known historical outcomes.

    Age/level cells shrink to their level-and-horizon cohort.  Level cohorts
    shrink to the complete horizon cohort.  This supplies delayed arrival and
    attrition directly from observed outcomes without a team-depth feature.
    """

    wanted_horizons = tuple(sorted(set(int(value) for value in horizons)))
    if not wanted_horizons or any(value < 1 for value in wanted_horizons):
        raise ValueError("hitter opportunity horizons must be positive")
    if age_band_width < 1:
        raise ValueError("hitter opportunity age-band width must be positive")
    if participation_prior_players <= 0 or workload_prior_positive_players <= 0:
        raise ValueError("hitter opportunity prior strengths must be positive")
    missing = sorted(set(HITTER_OPPORTUNITY_HISTORY_SCHEMA) - set(history.columns))
    if missing:
        raise ValueError(f"hitter opportunity history missing fields: {missing}")
    source = history.select(list(HITTER_OPPORTUNITY_HISTORY_SCHEMA)).cast(
        HITTER_OPPORTUNITY_HISTORY_SCHEMA, strict=True
    )
    if source.is_empty():
        raise ValueError("hitter opportunity history must not be empty")
    required_non_null = [
        "snapshot_year",
        "player_id",
        "as_of_level_group",
        "horizon",
        "future_mlb_pa",
    ]
    if sum(source.select(required_non_null).null_count().row(0)):
        raise ValueError("hitter opportunity history has null required values")
    if (
        source.group_by(["snapshot_year", "player_id", "horizon"])
        .len()
        .filter(pl.col("len") != 1)
        .height
    ):
        raise ValueError("hitter opportunity history violates player-snapshot-horizon grain")

    prepared_rows: list[dict[str, object]] = []
    for row in source.iter_rows(named=True):
        horizon = int(row["horizon"])
        target_year = int(row["snapshot_year"]) + horizon
        pa = float(row["future_mlb_pa"])
        if int(row["player_id"]) <= 0 or horizon < 1 or not isfinite(pa) or pa < 0:
            raise ValueError("hitter opportunity history has invalid values")
        if target_year >= forecast_year:
            raise ValueError("hitter opportunity history crosses the forecast cutoff")
        prepared_rows.append(
            {
                **row,
                "level_tier": hitter_level_tier(row["as_of_level_group"]),
                "age_band_start": _age_band(row["age_years"], age_band_width),
                "active": 1 if pa > 0 else 0,
            }
        )
    prepared = pl.DataFrame(prepared_rows)
    observed_horizons = set(prepared.get_column("horizon").unique().to_list())
    missing_horizons = sorted(set(wanted_horizons) - observed_horizons)
    if missing_horizons:
        raise ValueError(f"hitter opportunity history lacks horizons: {missing_horizons}")
    prepared = prepared.filter(pl.col("horizon").is_in(wanted_horizons))

    rows: list[dict[str, object]] = []
    for horizon in wanted_horizons:
        horizon_rows = prepared.filter(pl.col("horizon") == horizon)
        horizon_n = horizon_rows.height
        horizon_positive = horizon_rows.filter(pl.col("active") == 1)
        horizon_positive_n = horizon_positive.height
        if horizon_positive_n == 0:
            raise ValueError(f"hitter opportunity horizon {horizon} has no positive MLB PA")
        population_probability = float(horizon_positive_n / horizon_n)
        population_workload = float(horizon_positive.get_column("future_mlb_pa").mean())
        population_workload_variance = float(
            horizon_positive.get_column("future_mlb_pa").var(ddof=0) or 0.0
        )
        rows.append(
            {
                "horizon": horizon,
                "level_tier": "ALL",
                "age_band_start": None,
                "reference_level": "population",
                "observation_count": horizon_n,
                "positive_count": horizon_positive_n,
                "mlb_active_probability": population_probability,
                "conditional_mlb_pa": population_workload,
                "conditional_mlb_pa_variance": population_workload_variance,
            }
        )

        for level_rows in horizon_rows.partition_by("level_tier", maintain_order=True):
            level = str(level_rows.item(0, "level_tier"))
            level_n = level_rows.height
            level_positive = level_rows.filter(pl.col("active") == 1)
            level_positive_n = level_positive.height
            level_probability = _smoothed_rate(
                level_positive_n,
                level_n,
                population_probability,
                participation_prior_players,
            )
            level_workload = _smoothed_rate(
                float(level_positive.get_column("future_mlb_pa").sum()),
                level_positive_n,
                population_workload,
                workload_prior_positive_players,
            )
            level_workload_variance = _smoothed_variance(
                level_positive.get_column("future_mlb_pa"),
                mean=level_workload,
                prior_mean=population_workload,
                prior_variance=population_workload_variance,
                strength=workload_prior_positive_players,
            )
            rows.append(
                {
                    "horizon": horizon,
                    "level_tier": level,
                    "age_band_start": None,
                    "reference_level": "level",
                    "observation_count": level_n,
                    "positive_count": level_positive_n,
                    "mlb_active_probability": level_probability,
                    "conditional_mlb_pa": level_workload,
                    "conditional_mlb_pa_variance": level_workload_variance,
                }
            )
            known_age = level_rows.filter(pl.col("age_band_start").is_not_null())
            for cell in known_age.partition_by("age_band_start", maintain_order=True):
                age_band = int(cell.item(0, "age_band_start"))
                cell_n = cell.height
                cell_positive = cell.filter(pl.col("active") == 1)
                cell_positive_n = cell_positive.height
                cell_workload = _smoothed_rate(
                    float(cell_positive.get_column("future_mlb_pa").sum()),
                    cell_positive_n,
                    level_workload,
                    workload_prior_positive_players,
                )
                rows.append(
                    {
                        "horizon": horizon,
                        "level_tier": level,
                        "age_band_start": age_band,
                        "reference_level": "age_level",
                        "observation_count": cell_n,
                        "positive_count": cell_positive_n,
                        "mlb_active_probability": _smoothed_rate(
                            cell_positive_n,
                            cell_n,
                            level_probability,
                            participation_prior_players,
                        ),
                        "conditional_mlb_pa": cell_workload,
                        "conditional_mlb_pa_variance": _smoothed_variance(
                            cell_positive.get_column("future_mlb_pa"),
                            mean=cell_workload,
                            prior_mean=level_workload,
                            prior_variance=level_workload_variance,
                            strength=workload_prior_positive_players,
                        ),
                    }
                )

    references = pl.DataFrame(rows, schema=HITTER_OPPORTUNITY_REFERENCE_SCHEMA).sort(
        ["horizon", "level_tier", "age_band_start"], nulls_last=False
    )
    return HitterOpportunityFit(
        references=references,
        horizons=wanted_horizons,
        age_band_width=age_band_width,
        participation_prior_players=float(participation_prior_players),
        workload_prior_positive_players=float(workload_prior_positive_players),
    )


def _selected_predictions(
    frame: pl.DataFrame | None,
) -> dict[tuple[int, int], tuple[float, float, float, str | None, str | None]]:
    if frame is None:
        return {}
    missing = sorted(set(SELECTED_NEXT_YEAR_SCHEMA) - set(frame.columns))
    if missing:
        raise ValueError(f"selected next-year predictions missing fields: {missing}")
    optional_alpha = "model_nb_alpha" in frame.columns
    optional_horizon = "horizon" in frame.columns
    optional_model_id = "model_id" in frame.columns
    optional_model_status = "model_status" in frame.columns
    schema = {
        **SELECTED_NEXT_YEAR_SCHEMA,
        **({"model_nb_alpha": pl.Float64} if optional_alpha else {}),
        **({"horizon": pl.Int64} if optional_horizon else {}),
        **({"model_id": pl.String} if optional_model_id else {}),
        **({"model_status": pl.String} if optional_model_status else {}),
    }
    selected = frame.select(list(schema)).cast(schema, strict=True)
    if (
        selected.group_by(
            ["player_id", "horizon"] if optional_horizon else ["player_id"]
        ).len().filter(pl.col("len") != 1).height
        or sum(selected.null_count().row(0))
    ):
        raise ValueError("selected next-year predictions violate player grain")
    result: dict[
        tuple[int, int], tuple[float, float, float, str | None, str | None]
    ] = {}
    for row in selected.iter_rows(named=True):
        player_id = int(row["player_id"])
        probability = float(row["predicted_any_mlb_pa_probability"])
        workload = float(row["predicted_positive_mlb_pa_mean"])
        alpha = float(row["model_nb_alpha"]) if optional_alpha else NB2_ALPHA
        horizon = int(row["horizon"]) if optional_horizon else 1
        model_id = str(row["model_id"]) if optional_model_id else None
        model_status = str(row["model_status"]) if optional_model_status else None
        if (
            player_id <= 0
            or not isfinite(probability)
            or not 0.0 <= probability <= 1.0
            or not isfinite(workload)
            or workload < 0.0
            or not isfinite(alpha)
            or alpha <= 0.0
            or horizon <= 0
        ):
            raise ValueError("selected next-year predictions contain invalid values")
        result[(player_id, horizon)] = (
            probability,
            workload,
            alpha,
            model_id,
            model_status,
        )
    return result


def score_hitter_opportunity_paths(
    universe: pl.DataFrame,
    fit: HitterOpportunityFit,
    *,
    as_of_date: date,
    forecast_year: int,
    selected_next_year: pl.DataFrame | None = None,
    selected_model_id: str = "playing_time_v1",
    selected_model_status: str = "selected",
) -> pl.DataFrame:
    """Score every hitter at every fitted horizon with explicit source labels."""

    missing = sorted(set(HITTER_OPPORTUNITY_UNIVERSE_SCHEMA) - set(universe.columns))
    if missing:
        raise ValueError(f"hitter opportunity universe missing fields: {missing}")
    players = universe.select(list(HITTER_OPPORTUNITY_UNIVERSE_SCHEMA)).cast(
        HITTER_OPPORTUNITY_UNIVERSE_SCHEMA, strict=True
    )
    if players.is_empty():
        raise ValueError("hitter opportunity universe must not be empty")
    if (
        players.group_by("player_id").len().filter(pl.col("len") != 1).height
        or players.filter(pl.col("player_id").is_null() | (pl.col("player_id") <= 0)).height
    ):
        raise ValueError("hitter opportunity universe has invalid or duplicate player IDs")
    selected = _selected_predictions(selected_next_year)
    universe_ids = set(players.get_column("player_id").to_list())
    if {player_id for player_id, _horizon in selected} - universe_ids:
        raise ValueError("selected next-year predictions contain players outside the universe")
    if {horizon for _player_id, horizon in selected} - set(fit.horizons):
        raise ValueError("selected hitter predictions contain unsupported horizons")

    lookup = {
        (
            int(row["horizon"]),
            str(row["level_tier"]),
            row["age_band_start"],
            str(row["reference_level"]),
        ): (
            float(row["mlb_active_probability"]),
            float(row["conditional_mlb_pa"]),
            float(row["conditional_mlb_pa_variance"]),
        )
        for row in fit.references.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for player in players.iter_rows(named=True):
        player_id = int(player["player_id"])
        level = hitter_level_tier(player["as_of_level_group"])
        age_band = _age_band(player["age_years"], fit.age_band_width)
        for horizon in fit.horizons:
            selected_key = (player_id, horizon)
            if selected_key in selected:
                probability, workload, alpha, row_model_id, row_model_status = selected[
                    selected_key
                ]
                workload_variance = (
                    zero_truncated_nb2_variance(workload, alpha=alpha)
                    if workload > 1.0
                    else 0.0
                )
                coverage = (
                    "selected_next_year_model"
                    if horizon == 1
                    else "selected_direct_horizon_model"
                )
                model_id = row_model_id or selected_model_id
                model_status = row_model_status or selected_model_status
                probability_model = f"{model_id}:{model_status}:participation"
                workload_model = f"{model_id}:{model_status}:positive_pa"
            else:
                age_key = (horizon, level, age_band, "age_level")
                level_key = (horizon, level, None, "level")
                population_key = (horizon, "ALL", None, "population")
                if age_band is not None and age_key in lookup:
                    probability, workload, workload_variance = lookup[age_key]
                    coverage = "age_level_historical_fallback"
                elif level_key in lookup:
                    probability, workload, workload_variance = lookup[level_key]
                    coverage = "level_historical_fallback"
                else:
                    probability, workload, workload_variance = lookup[population_key]
                    coverage = "population_historical_fallback"
                probability_model = "hitter_opportunity_v1:historical_arrival_survival"
                workload_model = "hitter_opportunity_v1:historical_positive_pa"
            rows.append(
                {
                    "as_of_date": as_of_date,
                    "player_id": player_id,
                    "season": int(forecast_year) + horizon - 1,
                    "horizon": horizon,
                    "mlb_active_probability": probability,
                    "conditional_mlb_pa": workload,
                    "conditional_mlb_pa_variance": workload_variance,
                    "expected_mlb_pa": probability * workload,
                    "coverage_tier": coverage,
                    "probability_model_id": probability_model,
                    "workload_model_id": workload_model,
                    "uses_current_team_depth": False,
                }
            )
    return pl.DataFrame(rows, schema=HITTER_OPPORTUNITY_PATH_SCHEMA).sort(
        ["player_id", "season"]
    )


def compose_hitter_projection_paths(
    opportunity: pl.DataFrame,
    conditional_rates: pl.DataFrame,
    control_seasons: pl.DataFrame,
) -> pl.DataFrame:
    """Combine team-neutral opportunity, WAR rate, and control without hiding terms."""

    def select_contract(
        frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str
    ) -> pl.DataFrame:
        missing = sorted(set(schema) - set(frame.columns))
        if missing:
            raise ValueError(f"{label} missing fields: {missing}")
        selected = frame.select(list(schema)).cast(schema, strict=True)
        if (
            selected.group_by(["player_id", "season"])
            .len()
            .filter(pl.col("len") != 1)
            .height
        ):
            raise ValueError(f"{label} violates player-season grain")
        return selected

    workload = select_contract(
        opportunity, HITTER_OPPORTUNITY_PATH_SCHEMA, "hitter opportunity path"
    )
    rates = select_contract(
        conditional_rates, HITTER_CONDITIONAL_WAR_RATE_SCHEMA, "hitter WAR rates"
    )
    control = select_contract(
        control_seasons, HITTER_CONTROL_SEASON_SCHEMA, "hitter control seasons"
    )
    if workload.is_empty():
        raise ValueError("hitter opportunity path must not be empty")
    workload_keys = set(workload.select("player_id", "season").iter_rows())
    if set(rates.select("player_id", "season").iter_rows()) != workload_keys:
        raise ValueError("hitter WAR-rate coverage differs from opportunity coverage")
    if set(control.select("player_id", "season").iter_rows()) != workload_keys:
        raise ValueError("hitter control coverage differs from opportunity coverage")
    if rates.filter(
        pl.col("conditional_war_per_600_pa").is_null()
        | ~pl.col("conditional_war_per_600_pa").is_finite()
        | pl.col("talent_model_id").is_null()
        | (pl.col("talent_model_id") == "")
    ).height:
        raise ValueError("hitter WAR rates contain invalid values")
    if control.select(pl.all().null_count()).row(0) != (0, 0, 0):
        raise ValueError("hitter control seasons contain null values")

    return (
        workload.join(rates, on=["player_id", "season"], how="inner", validate="1:1")
        .join(control, on=["player_id", "season"], how="inner", validate="1:1")
        .with_columns(
            pl.lit("hitter").alias("projection_component"),
            pl.lit("position_player").alias("role"),
            pl.lit("PA").alias("workload_measure"),
            pl.lit(600.0).alias("workload_unit"),
        )
        .with_columns(
            pl.col("mlb_active_probability"),
            pl.col("conditional_war_per_600_pa").alias("conditional_war_rate"),
            pl.col("conditional_mlb_pa").alias("conditional_workload"),
            (
                pl.col("mlb_active_probability")
                * pl.col("conditional_war_per_600_pa")
                * pl.col("conditional_mlb_pa")
                / 600.0
            ).alias("expected_war"),
        )
        .select(list(PROJECTION_PATH_SCHEMA))
        .cast(PROJECTION_PATH_SCHEMA, strict=True)
        .sort(["player_id", "season"])
    )
