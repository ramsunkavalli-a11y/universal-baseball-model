"""Team-neutral multi-year pitcher arrival, role, and BF paths."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import floor, isfinite
from typing import Iterable

import polars as pl

from universal_baseball.hitter_opportunity_paths import hitter_level_tier
from universal_baseball.projection_guardrails import PROJECTION_PATH_SCHEMA


PITCHER_ROLES = ("starter", "swingman", "reliever")

PITCHER_OPPORTUNITY_HISTORY_SCHEMA: dict[str, pl.DataType] = {
    "snapshot_year": pl.Int64,
    "player_id": pl.Int64,
    "age_years": pl.Float64,
    "as_of_level_group": pl.String,
    "as_of_role": pl.String,
    "horizon": pl.Int64,
    "future_mlb_bf": pl.Float64,
    "future_mlb_games": pl.Int64,
    "future_mlb_starts": pl.Int64,
}

PITCHER_OPPORTUNITY_REFERENCE_SCHEMA: dict[str, pl.DataType] = {
    "horizon": pl.Int64,
    "level_tier": pl.String,
    "as_of_role": pl.String,
    "age_band_start": pl.Int64,
    "reference_level": pl.String,
    "observation_count": pl.Int64,
    "positive_count": pl.Int64,
    "mlb_active_probability": pl.Float64,
    "conditional_mlb_bf": pl.Float64,
    "starter_probability_if_active": pl.Float64,
    "swingman_probability_if_active": pl.Float64,
    "reliever_probability_if_active": pl.Float64,
}

PITCHER_OPPORTUNITY_UNIVERSE_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "age_years": pl.Float64,
    "as_of_level_group": pl.String,
    "as_of_role": pl.String,
}

PITCHER_OPPORTUNITY_PATH_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "season": pl.Int64,
    "horizon": pl.Int64,
    "mlb_active_probability": pl.Float64,
    "conditional_mlb_bf": pl.Float64,
    "expected_mlb_bf": pl.Float64,
    "starter_probability_if_active": pl.Float64,
    "swingman_probability_if_active": pl.Float64,
    "reliever_probability_if_active": pl.Float64,
    "projected_role": pl.String,
    "coverage_tier": pl.String,
    "probability_model_id": pl.String,
    "workload_model_id": pl.String,
    "role_model_id": pl.String,
    "uses_current_team_depth": pl.Boolean,
}

PITCHER_CONDITIONAL_WAR_RATE_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "conditional_war_per_800_bf": pl.Float64,
    "talent_model_id": pl.String,
}

PITCHER_CONTROL_SEASON_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "is_controlled_season": pl.Boolean,
}


@dataclass(frozen=True, slots=True)
class PitcherOpportunityFit:
    references: pl.DataFrame
    horizons: tuple[int, ...]
    age_band_width: int


def pitcher_role(*, games: int, starts: int) -> str:
    """Classify observed use: majority starts, no starts, or mixed use."""

    if games <= 0 or starts < 0 or starts > games:
        raise ValueError("pitcher role requires positive games and valid starts")
    if starts == 0:
        return "reliever"
    if starts * 2 >= games:
        return "starter"
    return "swingman"


def normalize_pitcher_role(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in PITCHER_ROLES:
        return normalized
    return "unknown"


def _age_band(value: object, width: int) -> int | None:
    if value is None:
        return None
    age = float(value)
    if not isfinite(age) or not 15.0 <= age <= 60.0:
        raise ValueError("pitcher opportunity age must be between 15 and 60 when known")
    return int(floor(age / width) * width)


def _summarize(
    group: pl.DataFrame,
    *,
    parent: tuple[float, float, tuple[float, float, float]] | None,
    participation_prior: float,
    workload_prior: float,
    role_prior: float,
) -> tuple[float, float, tuple[float, float, float]]:
    n = group.height
    active = group.filter(pl.col("future_mlb_bf") > 0)
    active_n = active.height
    role_counts = {
        role: active.filter(pl.col("future_role") == role).height for role in PITCHER_ROLES
    }
    if parent is None:
        if active_n == 0:
            raise ValueError("pitcher opportunity horizon has no active pitchers")
        return (
            active_n / n,
            float(active.get_column("future_mlb_bf").mean()),
            tuple(role_counts[role] / active_n for role in PITCHER_ROLES),
        )
    parent_probability, parent_bf, parent_roles = parent
    probability = (active_n + participation_prior * parent_probability) / (
        n + participation_prior
    )
    workload = (
        float(active.get_column("future_mlb_bf").sum()) + workload_prior * parent_bf
    ) / (active_n + workload_prior)
    roles = tuple(
        (role_counts[role] + role_prior * parent_roles[index]) / (active_n + role_prior)
        for index, role in enumerate(PITCHER_ROLES)
    )
    return probability, workload, roles


def fit_pitcher_opportunity_fallbacks(
    history: pl.DataFrame,
    *,
    forecast_year: int,
    horizons: Iterable[int],
    age_band_width: int = 2,
    participation_prior_players: float = 50.0,
    workload_prior_active_pitchers: float = 20.0,
    role_prior_active_pitchers: float = 20.0,
) -> PitcherOpportunityFit:
    """Fit arrival, survival, BF, and role paths from pre-cutoff cohorts."""

    wanted = tuple(sorted(set(int(value) for value in horizons)))
    if not wanted or any(value < 1 for value in wanted):
        raise ValueError("pitcher opportunity horizons must be positive")
    if age_band_width < 1 or min(
        participation_prior_players,
        workload_prior_active_pitchers,
        role_prior_active_pitchers,
    ) <= 0:
        raise ValueError("pitcher opportunity widths and prior strengths must be positive")
    missing = sorted(set(PITCHER_OPPORTUNITY_HISTORY_SCHEMA) - set(history.columns))
    if missing:
        raise ValueError(f"pitcher opportunity history missing fields: {missing}")
    source = history.select(list(PITCHER_OPPORTUNITY_HISTORY_SCHEMA)).cast(
        PITCHER_OPPORTUNITY_HISTORY_SCHEMA, strict=True
    )
    if source.is_empty() or sum(
        source.select(
            "snapshot_year",
            "player_id",
            "as_of_level_group",
            "as_of_role",
            "horizon",
            "future_mlb_bf",
            "future_mlb_games",
            "future_mlb_starts",
        ).null_count().row(0)
    ):
        raise ValueError("pitcher opportunity history is empty or has null required values")
    if (
        source.group_by(["snapshot_year", "player_id", "horizon"])
        .len()
        .filter(pl.col("len") != 1)
        .height
    ):
        raise ValueError("pitcher opportunity history violates player-snapshot-horizon grain")

    prepared = []
    for row in source.iter_rows(named=True):
        bf = float(row["future_mlb_bf"])
        games = int(row["future_mlb_games"])
        starts = int(row["future_mlb_starts"])
        horizon = int(row["horizon"])
        if (
            int(row["player_id"]) <= 0
            or horizon < 1
            or not isfinite(bf)
            or bf < 0
            or games < 0
            or starts < 0
            or starts > games
            or (bf > 0) != (games > 0)
        ):
            raise ValueError("pitcher opportunity history has invalid outcomes")
        if int(row["snapshot_year"]) + horizon >= forecast_year:
            raise ValueError("pitcher opportunity history crosses the forecast cutoff")
        prepared.append(
            {
                **row,
                "level_tier": hitter_level_tier(row["as_of_level_group"]),
                "normalized_as_of_role": normalize_pitcher_role(row["as_of_role"]),
                "age_band_start": _age_band(row["age_years"], age_band_width),
                "future_role": pitcher_role(games=games, starts=starts) if bf > 0 else None,
            }
        )
    data = pl.DataFrame(prepared)
    absent = sorted(set(wanted) - set(data.get_column("horizon").unique().to_list()))
    if absent:
        raise ValueError(f"pitcher opportunity history lacks horizons: {absent}")
    data = data.filter(pl.col("horizon").is_in(wanted))

    rows: list[dict[str, object]] = []

    def add_reference(
        group: pl.DataFrame,
        *,
        horizon: int,
        level: str,
        role: str,
        age_band: int | None,
        reference_level: str,
        parent: tuple[float, float, tuple[float, float, float]] | None,
    ) -> tuple[float, float, tuple[float, float, float]]:
        summary = _summarize(
            group,
            parent=parent,
            participation_prior=participation_prior_players,
            workload_prior=workload_prior_active_pitchers,
            role_prior=role_prior_active_pitchers,
        )
        probability, workload, role_probabilities = summary
        rows.append(
            {
                "horizon": horizon,
                "level_tier": level,
                "as_of_role": role,
                "age_band_start": age_band,
                "reference_level": reference_level,
                "observation_count": group.height,
                "positive_count": group.filter(pl.col("future_mlb_bf") > 0).height,
                "mlb_active_probability": probability,
                "conditional_mlb_bf": workload,
                "starter_probability_if_active": role_probabilities[0],
                "swingman_probability_if_active": role_probabilities[1],
                "reliever_probability_if_active": role_probabilities[2],
            }
        )
        return summary

    for horizon in wanted:
        horizon_rows = data.filter(pl.col("horizon") == horizon)
        population = add_reference(
            horizon_rows,
            horizon=horizon,
            level="ALL",
            role="all",
            age_band=None,
            reference_level="population",
            parent=None,
        )
        for level_rows in horizon_rows.partition_by("level_tier", maintain_order=True):
            level = str(level_rows.item(0, "level_tier"))
            level_summary = add_reference(
                level_rows,
                horizon=horizon,
                level=level,
                role="all",
                age_band=None,
                reference_level="level",
                parent=population,
            )
            for role_rows in level_rows.partition_by(
                "normalized_as_of_role", maintain_order=True
            ):
                role = str(role_rows.item(0, "normalized_as_of_role"))
                role_summary = add_reference(
                    role_rows,
                    horizon=horizon,
                    level=level,
                    role=role,
                    age_band=None,
                    reference_level="level_role",
                    parent=level_summary,
                )
                known_age = role_rows.filter(pl.col("age_band_start").is_not_null())
                for cell in known_age.partition_by("age_band_start", maintain_order=True):
                    add_reference(
                        cell,
                        horizon=horizon,
                        level=level,
                        role=role,
                        age_band=int(cell.item(0, "age_band_start")),
                        reference_level="age_level_role",
                        parent=role_summary,
                    )
    return PitcherOpportunityFit(
        references=pl.DataFrame(rows, schema=PITCHER_OPPORTUNITY_REFERENCE_SCHEMA).sort(
            ["horizon", "level_tier", "as_of_role", "age_band_start"], nulls_last=False
        ),
        horizons=wanted,
        age_band_width=age_band_width,
    )


def score_pitcher_opportunity_paths(
    universe: pl.DataFrame,
    fit: PitcherOpportunityFit,
    *,
    as_of_date: date,
    forecast_year: int,
) -> pl.DataFrame:
    """Score every pitcher-year, preserving role uncertainty and fallback source."""

    missing = sorted(set(PITCHER_OPPORTUNITY_UNIVERSE_SCHEMA) - set(universe.columns))
    if missing:
        raise ValueError(f"pitcher opportunity universe missing fields: {missing}")
    players = universe.select(list(PITCHER_OPPORTUNITY_UNIVERSE_SCHEMA)).cast(
        PITCHER_OPPORTUNITY_UNIVERSE_SCHEMA, strict=True
    )
    if players.is_empty() or players.filter(
        pl.col("player_id").is_null() | (pl.col("player_id") <= 0)
    ).height or players.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("pitcher opportunity universe has invalid or duplicate players")
    lookup = {
        (
            int(row["horizon"]),
            str(row["level_tier"]),
            str(row["as_of_role"]),
            row["age_band_start"],
            str(row["reference_level"]),
        ): row
        for row in fit.references.iter_rows(named=True)
    }
    output = []
    for player in players.iter_rows(named=True):
        player_id = int(player["player_id"])
        level = hitter_level_tier(player["as_of_level_group"])
        role = normalize_pitcher_role(player["as_of_role"])
        age_band = _age_band(player["age_years"], fit.age_band_width)
        for horizon in fit.horizons:
            candidates = [
                ((horizon, level, role, age_band, "age_level_role"), "age_level_role_historical_fallback"),
                ((horizon, level, role, None, "level_role"), "level_role_historical_fallback"),
                ((horizon, level, "all", None, "level"), "level_historical_fallback"),
                ((horizon, "ALL", "all", None, "population"), "population_historical_fallback"),
            ]
            reference = None
            coverage = ""
            for key, label in candidates:
                if key in lookup:
                    reference = lookup[key]
                    coverage = label
                    break
            if reference is None:
                raise ValueError("pitcher opportunity fit lacks a population fallback")
            role_values = {
                role_name: float(reference[f"{role_name}_probability_if_active"])
                for role_name in PITCHER_ROLES
            }
            projected_role = max(PITCHER_ROLES, key=lambda value: role_values[value])
            probability = float(reference["mlb_active_probability"])
            workload = float(reference["conditional_mlb_bf"])
            output.append(
                {
                    "as_of_date": as_of_date,
                    "player_id": player_id,
                    "season": forecast_year + horizon - 1,
                    "horizon": horizon,
                    "mlb_active_probability": probability,
                    "conditional_mlb_bf": workload,
                    "expected_mlb_bf": probability * workload,
                    **{
                        f"{role_name}_probability_if_active": role_values[role_name]
                        for role_name in PITCHER_ROLES
                    },
                    "projected_role": projected_role,
                    "coverage_tier": coverage,
                    "probability_model_id": "pitcher_opportunity_v1:historical_arrival_survival",
                    "workload_model_id": "pitcher_opportunity_v1:historical_positive_bf",
                    "role_model_id": "pitcher_opportunity_v1:historical_role_transition",
                    "uses_current_team_depth": False,
                }
            )
    return pl.DataFrame(output, schema=PITCHER_OPPORTUNITY_PATH_SCHEMA).sort(
        ["player_id", "season"]
    )


def compose_pitcher_projection_paths(
    opportunity: pl.DataFrame,
    conditional_rates: pl.DataFrame,
    control_seasons: pl.DataFrame,
) -> pl.DataFrame:
    """Place pitcher opportunity and conditional WAR rate in the shared contract."""

    def contracted(
        frame: pl.DataFrame, schema: dict[str, pl.DataType], label: str
    ) -> pl.DataFrame:
        missing = sorted(set(schema) - set(frame.columns))
        if missing:
            raise ValueError(f"{label} missing fields: {missing}")
        result = frame.select(list(schema)).cast(schema, strict=True)
        if result.group_by(["player_id", "season"]).len().filter(pl.col("len") != 1).height:
            raise ValueError(f"{label} violates player-season grain")
        return result

    workload = contracted(
        opportunity, PITCHER_OPPORTUNITY_PATH_SCHEMA, "pitcher opportunity path"
    )
    rates = contracted(
        conditional_rates, PITCHER_CONDITIONAL_WAR_RATE_SCHEMA, "pitcher WAR rates"
    )
    control = contracted(
        control_seasons, PITCHER_CONTROL_SEASON_SCHEMA, "pitcher control seasons"
    )
    keys = set(workload.select("player_id", "season").iter_rows())
    if not keys or set(rates.select("player_id", "season").iter_rows()) != keys:
        raise ValueError("pitcher WAR-rate coverage differs from opportunity coverage")
    if set(control.select("player_id", "season").iter_rows()) != keys:
        raise ValueError("pitcher control coverage differs from opportunity coverage")
    if rates.filter(
        ~pl.col("conditional_war_per_800_bf").is_finite()
        | pl.col("talent_model_id").is_null()
        | (pl.col("talent_model_id") == "")
    ).height:
        raise ValueError("pitcher WAR rates contain invalid values")
    return (
        workload.join(rates, on=["player_id", "season"], how="inner", validate="1:1")
        .join(control, on=["player_id", "season"], how="inner", validate="1:1")
        .with_columns(
            pl.lit("pitcher").alias("projection_component"),
            pl.col("projected_role").alias("role"),
            pl.lit("BF").alias("workload_measure"),
            pl.col("conditional_war_per_800_bf").alias("conditional_war_rate"),
            pl.col("conditional_mlb_bf").alias("conditional_workload"),
            pl.lit(800.0).alias("workload_unit"),
            (
                pl.col("mlb_active_probability")
                * pl.col("conditional_war_per_800_bf")
                * pl.col("conditional_mlb_bf")
                / 800.0
            ).alias("expected_war"),
        )
        .select(list(PROJECTION_PATH_SCHEMA))
        .cast(PROJECTION_PATH_SCHEMA, strict=True)
        .sort(["player_id", "season"])
    )
