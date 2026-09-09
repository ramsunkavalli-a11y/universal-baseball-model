"""Team-neutral multi-year pitcher arrival, role, and BF paths."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import floor, isfinite
from typing import Iterable

import polars as pl

from universal_baseball.hitter_opportunity_paths import hitter_level_tier
from universal_baseball.projection_guardrails import PROJECTION_PATH_SCHEMA
from universal_baseball.player_value_uncertainty import (
    NB2_ALPHA,
    zero_truncated_nb2_variance,
)


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
    "conditional_mlb_bf_variance": pl.Float64,
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

SELECTED_PITCHER_NEXT_YEAR_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "predicted_any_mlb_bf_probability": pl.Float64,
    "predicted_positive_mlb_bf_mean": pl.Float64,
}

PITCHER_MLB_OUTCOME_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "player_id": pl.Int64,
    "pitching_bf": pl.Float64,
    "pitching_games": pl.Int64,
    "pitching_starts": pl.Int64,
}

PITCHER_OPPORTUNITY_PATH_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "season": pl.Int64,
    "horizon": pl.Int64,
    "mlb_active_probability": pl.Float64,
    "conditional_mlb_bf": pl.Float64,
    "conditional_mlb_bf_variance": pl.Float64,
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


def build_pitcher_opportunity_history(
    snapshots: pl.DataFrame,
    mlb_outcomes: pl.DataFrame,
    *,
    horizons: Iterable[int],
    completed_seasons: Iterable[int],
) -> pl.DataFrame:
    """Attach future MLB BF/games/starts, retaining completed-season zeros."""

    wanted = tuple(sorted(set(int(value) for value in horizons)))
    complete = {int(value) for value in completed_seasons}
    if not wanted or any(value < 1 for value in wanted):
        raise ValueError("pitcher opportunity horizons must be positive")
    missing_snapshots = sorted(
        (set(PITCHER_OPPORTUNITY_UNIVERSE_SCHEMA) | {"snapshot_year"})
        - set(snapshots.columns)
    )
    if missing_snapshots:
        raise ValueError(f"pitcher opportunity snapshots missing fields: {missing_snapshots}")
    missing_outcomes = sorted(set(PITCHER_MLB_OUTCOME_SCHEMA) - set(mlb_outcomes.columns))
    if missing_outcomes:
        raise ValueError(f"pitcher MLB outcomes missing fields: {missing_outcomes}")
    snapshot_schema = {"snapshot_year": pl.Int64, **PITCHER_OPPORTUNITY_UNIVERSE_SCHEMA}
    cohorts = snapshots.select(list(snapshot_schema)).cast(snapshot_schema, strict=True)
    outcomes = mlb_outcomes.select(list(PITCHER_MLB_OUTCOME_SCHEMA)).cast(
        PITCHER_MLB_OUTCOME_SCHEMA, strict=True
    )
    if cohorts.is_empty() or cohorts.group_by(
        ["snapshot_year", "player_id"]
    ).len().filter(pl.col("len") != 1).height:
        raise ValueError("pitcher opportunity snapshots are empty or violate grain")
    if outcomes.group_by(["season", "player_id"]).len().filter(pl.col("len") != 1).height:
        raise ValueError("pitcher MLB outcomes violate season-player grain")
    if outcomes.filter(
        (pl.col("pitching_bf") < 0)
        | (pl.col("pitching_games") < 0)
        | (pl.col("pitching_starts") < 0)
        | (pl.col("pitching_starts") > pl.col("pitching_games"))
    ).height:
        raise ValueError("pitcher MLB outcomes contain invalid values")
    grid = cohorts.join(
        pl.DataFrame({"horizon": wanted}, schema={"horizon": pl.Int64}), how="cross"
    ).with_columns((pl.col("snapshot_year") + pl.col("horizon")).alias("target_year"))
    grid = grid.filter(pl.col("target_year").is_in(sorted(complete)))
    if grid.is_empty():
        raise ValueError("pitcher opportunity has no certified complete target rows")
    missing_horizons = sorted(set(wanted) - set(grid["horizon"].unique().to_list()))
    if missing_horizons:
        raise ValueError(
            f"pitcher opportunity has no certified targets for horizons: {missing_horizons}"
        )
    targets = outcomes.rename({"season": "target_year"})
    return (
        grid.join(targets, on=["target_year", "player_id"], how="left", validate="m:1")
        .with_columns(
            pl.col("pitching_bf").fill_null(0.0),
            pl.col("pitching_games").fill_null(0),
            pl.col("pitching_starts").fill_null(0),
        )
        .select(
            "snapshot_year",
            "player_id",
            "age_years",
            "as_of_level_group",
            "as_of_role",
            "horizon",
            pl.col("pitching_bf").alias("future_mlb_bf"),
            pl.col("pitching_games").alias("future_mlb_games"),
            pl.col("pitching_starts").alias("future_mlb_starts"),
        )
        .cast(PITCHER_OPPORTUNITY_HISTORY_SCHEMA, strict=True)
        .sort(["snapshot_year", "player_id", "horizon"])
    )


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
    parent: tuple[float, float, float, tuple[float, float, float]] | None,
    participation_prior: float,
    workload_prior: float,
    role_prior: float,
) -> tuple[float, float, float, tuple[float, float, float]]:
    n = group.height
    active = group.filter(pl.col("future_mlb_bf") > 0)
    active_n = active.height
    role_counts = {
        role: active.filter(pl.col("future_role") == role).height for role in PITCHER_ROLES
    }
    if parent is None:
        if active_n == 0:
            raise ValueError("pitcher opportunity horizon has no active pitchers")
        workload = float(active.get_column("future_mlb_bf").mean())
        return (
            active_n / n,
            workload,
            float(active.get_column("future_mlb_bf").var(ddof=0) or 0.0),
            tuple(role_counts[role] / active_n for role in PITCHER_ROLES),
        )
    parent_probability, parent_bf, parent_bf_variance, parent_roles = parent
    probability = (active_n + participation_prior * parent_probability) / (
        n + participation_prior
    )
    workload = (
        float(active.get_column("future_mlb_bf").sum()) + workload_prior * parent_bf
    ) / (active_n + workload_prior)
    second_moment = (
        float((active.get_column("future_mlb_bf") ** 2).sum() or 0.0)
        + workload_prior * (parent_bf_variance + parent_bf * parent_bf)
    ) / (active_n + workload_prior)
    workload_variance = max(0.0, second_moment - workload * workload)
    roles = tuple(
        (role_counts[role] + role_prior * parent_roles[index]) / (active_n + role_prior)
        for index, role in enumerate(PITCHER_ROLES)
    )
    return probability, workload, workload_variance, roles


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
        parent: tuple[float, float, float, tuple[float, float, float]] | None,
    ) -> tuple[float, float, float, tuple[float, float, float]]:
        summary = _summarize(
            group,
            parent=parent,
            participation_prior=participation_prior_players,
            workload_prior=workload_prior_active_pitchers,
            role_prior=role_prior_active_pitchers,
        )
        probability, workload, workload_variance, role_probabilities = summary
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
                "conditional_mlb_bf_variance": workload_variance,
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


def _selected_predictions(
    frame: pl.DataFrame | None,
) -> dict[tuple[int, int], tuple[float, float, float, str | None, str | None]]:
    if frame is None:
        return {}
    missing = sorted(set(SELECTED_PITCHER_NEXT_YEAR_SCHEMA) - set(frame.columns))
    if missing:
        raise ValueError(f"selected pitcher predictions missing fields: {missing}")
    optional_alpha = "model_nb_alpha" in frame.columns
    optional_horizon = "horizon" in frame.columns
    optional_model_id = "model_id" in frame.columns
    optional_model_status = "model_status" in frame.columns
    schema = {
        **SELECTED_PITCHER_NEXT_YEAR_SCHEMA,
        **({"model_nb_alpha": pl.Float64} if optional_alpha else {}),
        **({"horizon": pl.Int64} if optional_horizon else {}),
        **({"model_id": pl.String} if optional_model_id else {}),
        **({"model_status": pl.String} if optional_model_status else {}),
    }
    selected = frame.select(list(schema)).cast(schema, strict=True)
    if selected.group_by(
        ["player_id", "horizon"] if optional_horizon else ["player_id"]
    ).len().filter(pl.col("len") != 1).height or sum(
        selected.null_count().row(0)
    ):
        raise ValueError("selected pitcher predictions violate player grain")
    result: dict[
        tuple[int, int], tuple[float, float, float, str | None, str | None]
    ] = {}
    for row in selected.iter_rows(named=True):
        player_id = int(row["player_id"])
        probability = float(row["predicted_any_mlb_bf_probability"])
        workload = float(row["predicted_positive_mlb_bf_mean"])
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
            raise ValueError("selected pitcher predictions contain invalid values")
        result[(player_id, horizon)] = (
            probability,
            workload,
            alpha,
            model_id,
            model_status,
        )
    return result


def score_pitcher_opportunity_paths(
    universe: pl.DataFrame,
    fit: PitcherOpportunityFit,
    *,
    as_of_date: date,
    forecast_year: int,
    selected_next_year: pl.DataFrame | None = None,
    selected_model_id: str = "pitcher_opportunity_v1",
    selected_model_status: str = "selected",
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
    selected = _selected_predictions(selected_next_year)
    universe_ids = set(players.get_column("player_id").to_list())
    if {player_id for player_id, _horizon in selected} - universe_ids:
        raise ValueError("selected pitcher predictions contain players outside the universe")
    if {horizon for _player_id, horizon in selected} - set(fit.horizons):
        raise ValueError("selected pitcher predictions contain unsupported horizons")
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
            workload_variance = float(reference["conditional_mlb_bf_variance"])
            probability_model = "pitcher_opportunity_v1:historical_arrival_survival"
            workload_model = "pitcher_opportunity_v1:historical_positive_bf"
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
                probability_model = (
                    f"{model_id}:{model_status}:participation"
                )
                workload_model = f"{model_id}:{model_status}:positive_bf"
            output.append(
                {
                    "as_of_date": as_of_date,
                    "player_id": player_id,
                    "season": forecast_year + horizon - 1,
                    "horizon": horizon,
                    "mlb_active_probability": probability,
                    "conditional_mlb_bf": workload,
                    "conditional_mlb_bf_variance": workload_variance,
                    "expected_mlb_bf": probability * workload,
                    **{
                        f"{role_name}_probability_if_active": role_values[role_name]
                        for role_name in PITCHER_ROLES
                    },
                    "projected_role": projected_role,
                    "coverage_tier": coverage,
                    "probability_model_id": probability_model,
                    "workload_model_id": workload_model,
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
