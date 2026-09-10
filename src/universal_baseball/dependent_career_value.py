"""Deterministic dependent career-path simulation for pre-MLB player value."""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np
import polars as pl

from universal_baseball.cba_rules import CBARuleset


MODEL_ID = "dependent_pre_mlb_career_value_research_v1"
MASTER_SEED = 20260909
DEFAULT_DRAWS = 2048
TIERS = ("fringe", "meaningful_only", "established")
PITCHER_ROLES = ("starter", "swingman", "reliever")
ROLE_CODES = {
    "inactive": 0,
    "starter": 1,
    "swingman": 2,
    "reliever": 3,
    "hitter": 4,
    "unknown": 5,
}


def _path_library(
    annual_paths: pl.DataFrame,
    *,
    seasons: int,
) -> tuple[
    dict[tuple[str, str, str], tuple[np.ndarray, np.ndarray]],
    dict[tuple[str, str], tuple[np.ndarray, np.ndarray]],
]:
    required = {
        "path_player_id",
        "player_type",
        "outcome_tier_v2",
        "career_role",
        "path_year",
        "adjusted_workload",
        "annual_role",
        "window_end_year",
    }
    if missing := sorted(required - set(annual_paths.columns)):
        raise ValueError(f"annual career paths missing fields: {missing}")
    if seasons < 1:
        raise ValueError("simulation seasons must be positive")
    source = annual_paths.filter(pl.col("path_year") <= seasons)
    bad = source.group_by("path_player_id", "player_type").agg(
        pl.len().alias("rows"),
        pl.col("path_year").n_unique().alias("years"),
    ).filter((pl.col("rows") != seasons) | (pl.col("years") != seasons))
    if bad.height:
        raise ValueError("annual career paths must contain one complete ordered vector")

    role_cells: dict[tuple[str, str, str], list[tuple[np.ndarray, np.ndarray]]] = {}
    pooled_cells: dict[tuple[str, str], list[tuple[np.ndarray, np.ndarray]]] = {}
    for group in source.partition_by(
        ["path_player_id", "player_type"], maintain_order=True
    ):
        ordered = group.sort("path_year")
        first = ordered.row(0, named=True)
        vector = ordered.get_column("adjusted_workload").to_numpy().astype(float)
        if np.any(~np.isfinite(vector)) or np.any(vector < 0.0):
            raise ValueError("annual career workload must be finite and nonnegative")
        try:
            roles = np.asarray(
                [ROLE_CODES[str(value)] for value in ordered.get_column("annual_role")],
                dtype=np.int8,
            )
        except KeyError as exc:
            raise ValueError(f"unsupported historical annual role: {exc}") from exc
        player_type = str(first["player_type"])
        tier = str(first["outcome_tier_v2"])
        role = str(first["career_role"])
        role_cells.setdefault((player_type, tier, role), []).append((vector, roles))
        pooled_cells.setdefault((player_type, tier), []).append((vector, roles))
    def stack(
        cells: dict[tuple[str, ...], list[tuple[np.ndarray, np.ndarray]]],
    ) -> dict[tuple[str, ...], tuple[np.ndarray, np.ndarray]]:
        return {
            key: (
                np.stack([value[0] for value in values]),
                np.stack([value[1] for value in values]),
            )
            for key, values in cells.items()
        }
    return (
        stack(role_cells),
        stack(pooled_cells),
    )


def _rate_lookup(frame: pl.DataFrame) -> dict[int, tuple[float, float]]:
    required = {"player_id", "event_run_variance", "posterior_run_rate_variance"}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"career performance inputs missing fields: {missing}")
    summary = frame.group_by("player_id").agg(
        pl.col("event_run_variance").mean(),
        pl.col("posterior_run_rate_variance").mean(),
    )
    result: dict[int, tuple[float, float]] = {}
    for row in summary.iter_rows(named=True):
        values = (
            float(row["event_run_variance"]),
            float(row["posterior_run_rate_variance"]),
        )
        if any(not math.isfinite(value) or value < 0.0 for value in values):
            raise ValueError("career performance variances must be finite and nonnegative")
        result[int(row["player_id"])] = values
    return result


def _annual_arrival_probabilities(six_year_probability: float, seasons: int) -> np.ndarray:
    if not 0.0 <= six_year_probability <= 1.0:
        raise ValueError("six-year arrival probability must lie in [0, 1]")
    if six_year_probability == 0.0:
        return np.zeros(seasons, dtype=float)
    if six_year_probability == 1.0:
        result = np.zeros(seasons, dtype=float)
        result[0] = 1.0
        return result
    hazard = 1.0 - (1.0 - six_year_probability) ** (1.0 / seasons)
    return np.asarray(
        [(1.0 - hazard) ** year * hazard for year in range(seasons)],
        dtype=float,
    )


def _sample_categories(
    rng: np.random.Generator,
    probabilities: np.ndarray,
    draws: int,
) -> np.ndarray:
    if np.any(probabilities < 0.0) or not math.isclose(
        float(probabilities.sum()), 1.0, rel_tol=0.0, abs_tol=1e-9
    ):
        raise ValueError("category probabilities must form a simplex")
    return rng.choice(len(probabilities), size=draws, p=probabilities)


def _player_rate(row: dict[str, object]) -> tuple[float, float]:
    player_type = str(row["model_player_type"])
    if player_type == "hitter":
        assumed_workload = 6.0 * (
            450.0 if str(row.get("primary_position") or "") == "C" else 550.0
        )
        full_war = float(row.get("hitter_six_control_year_war_if_arrived") or 0.0)
        return full_war / assumed_workload, 600.0
    starter = max(0.0, float(row.get("starter_probability") or 0.0))
    reliever = max(0.0, float(row.get("reliever_probability") or 0.0))
    swingman = max(0.0, 1.0 - starter - reliever)
    total = starter + swingman + reliever
    if total <= 0.0:
        raise ValueError("pitcher role probabilities have no mass")
    assumed_workload = 6.0 * (
        800.0 * starter / total
        + 450.0 * swingman / total
        + 250.0 * reliever / total
    )
    full_war = float(row.get("pitcher_six_control_year_war_if_arrived") or 0.0)
    return full_war / assumed_workload, 800.0


def simulate_dependent_pre_mlb_value(
    nested: pl.DataFrame,
    annual_paths: pl.DataFrame,
    hitter_rates: pl.DataFrame,
    pitcher_rates: pl.DataFrame,
    *,
    forecast_seasons: tuple[int, ...],
    cba_ruleset: CBARuleset,
    market_rates: Mapping[int, Mapping[str, float]],
    arbitration_shares: Mapping[int, float],
    runs_per_win: float,
    annual_discount_rate: float = 0.10,
    minimum_role_players: int = 30,
    draws: int = DEFAULT_DRAWS,
    master_seed: int = MASTER_SEED,
    star_war_threshold: float = 18.0,
    arrival_horizon_years: int = 6,
    career_path_years: int = 6,
) -> pl.DataFrame:
    """Simulate linked arrival, career workload, performance, control and value."""

    if not forecast_seasons or tuple(sorted(forecast_seasons)) != forecast_seasons:
        raise ValueError("forecast seasons must be nonempty and ordered")
    if len(set(forecast_seasons)) != len(forecast_seasons):
        raise ValueError("forecast seasons must be unique")
    if arrival_horizon_years < 1 or career_path_years < 1:
        raise ValueError("arrival and career horizons must be positive")
    if len(forecast_seasons) < arrival_horizon_years + career_path_years - 1:
        raise ValueError(
            "forecast seasons must cover the arrival window plus full career path"
        )
    if draws < 2 or draws % 2:
        raise ValueError("draws must be an even number >= 2")
    if not math.isfinite(runs_per_win) or runs_per_win <= 0.0:
        raise ValueError("runs_per_win must be finite and positive")
    if not math.isfinite(annual_discount_rate) or annual_discount_rate < 0.0:
        raise ValueError("annual discount rate must be finite and nonnegative")
    if minimum_role_players < 1:
        raise ValueError("minimum role players must be positive")
    required = {
        "player_id",
        "model_player_type",
        "primary_position",
        "ordered_arrival_probability",
        "fringe_probability",
        "meaningful_only_probability",
        "established_probability",
        "starter_probability",
        "reliever_probability",
        "hitter_six_control_year_war_if_arrived",
        "pitcher_six_control_year_war_if_arrived",
    }
    if missing := sorted(required - set(nested.columns)):
        raise ValueError(f"nested career values missing fields: {missing}")
    role_library, pooled_library = _path_library(
        annual_paths, seasons=career_path_years
    )
    rate_lookups = {
        "hitter": _rate_lookup(hitter_rates),
        "pitcher": _rate_lookup(pitcher_rates),
    }
    half = draws // 2
    rows: list[dict[str, object]] = []
    applicable = nested.filter(pl.col("ordered_arrival_probability").is_not_null())
    for row in applicable.iter_rows(named=True):
        player_id = int(row["player_id"])
        player_type = str(row["model_player_type"])
        if player_type not in {"hitter", "pitcher"}:
            raise ValueError(f"unsupported player type: {player_type}")
        event_variance, posterior_variance = rate_lookups[player_type][player_id]
        rate, _ = _player_rate(row)
        arrival_probability = float(row["ordered_arrival_probability"])
        tier_masses = np.asarray(
            [float(row[f"{tier}_probability"]) for tier in TIERS], dtype=float
        )
        if np.any(tier_masses < 0.0) or not math.isclose(
            float(tier_masses.sum()), arrival_probability, abs_tol=1e-8
        ):
            raise ValueError(f"tier probabilities do not partition arrival for {player_id}")
        annual_arrival = _annual_arrival_probabilities(
            arrival_probability, arrival_horizon_years
        )
        no_arrival = max(0.0, 1.0 - float(annual_arrival.sum()))
        rng = np.random.Generator(
            np.random.PCG64(np.random.SeedSequence([master_seed, player_id]))
        )
        arrival_index = _sample_categories(
            rng, np.append(annual_arrival, no_arrival), half
        )
        tier_conditional = (
            tier_masses / arrival_probability
            if arrival_probability > 0.0
            else np.asarray([1.0, 0.0, 0.0])
        )
        tier_index = _sample_categories(rng, tier_conditional, half)
        if player_type == "pitcher":
            starter = max(0.0, float(row.get("starter_probability") or 0.0))
            reliever = max(0.0, float(row.get("reliever_probability") or 0.0))
            role_probabilities = np.asarray(
                [starter, max(0.0, 1.0 - starter - reliever), reliever], dtype=float
            )
            role_probabilities /= role_probabilities.sum()
            role_index = _sample_categories(rng, role_probabilities, half)
            roles = PITCHER_ROLES
        else:
            role_index = np.zeros(half, dtype=int)
            roles = ("hitter",)

        workload_half = np.zeros((half, len(forecast_seasons)), dtype=float)
        annual_role_half = np.zeros(
            (half, len(forecast_seasons)), dtype=np.int8
        )
        role_fallback_draws = 0
        for tier_number, tier in enumerate(TIERS):
            for role_number, role in enumerate(roles):
                mask = (
                    (arrival_index < arrival_horizon_years)
                    & (tier_index == tier_number)
                    & (role_index == role_number)
                )
                count = int(mask.sum())
                if not count:
                    continue
                cell = role_library.get((player_type, tier, role))
                if cell is None or cell[0].shape[0] < minimum_role_players:
                    cell = pooled_library.get((player_type, tier))
                    role_fallback_draws += count
                if cell is None or not cell[0].shape[0]:
                    raise ValueError(f"missing career paths for {player_type}/{tier}/{role}")
                selected_index = rng.integers(0, cell[0].shape[0], size=count)
                selected_workload = cell[0][selected_index]
                selected_roles = cell[1][selected_index]
                target_rows = np.flatnonzero(mask)
                for target, source_vector, source_roles in zip(
                    target_rows, selected_workload, selected_roles, strict=True
                ):
                    offset = int(arrival_index[target])
                    workload_half[target, offset : offset + career_path_years] = (
                        source_vector[:career_path_years]
                    )
                    annual_role_half[
                        target, offset : offset + career_path_years
                    ] = source_roles[:career_path_years]
        workloads = np.repeat(workload_half, 2, axis=0)
        annual_roles = np.repeat(annual_role_half, 2, axis=0)
        persistent_half = rng.standard_normal(half)
        persistent = np.column_stack((persistent_half, -persistent_half)).reshape(-1)
        event_half = rng.standard_normal((half, len(forecast_seasons)))
        event_noise = np.stack((event_half, -event_half), axis=1).reshape(
            draws, len(forecast_seasons)
        )
        war = (
            workloads * rate
            + workloads * persistent[:, None] * math.sqrt(posterior_variance) / runs_per_win
            + event_noise * np.sqrt(workloads * event_variance) / runs_per_win
        )

        value = np.zeros(draws, dtype=float)
        cost = np.zeros(draws, dtype=float)
        controlled_war = np.zeros(draws, dtype=float)
        service_years = np.zeros(draws, dtype=np.int16)
        prior_market_value = np.zeros(draws, dtype=float)
        for year_index, season in enumerate(forecast_seasons):
            annual_war = war[:, year_index]
            has_workload = workloads[:, year_index] > 0.0
            active = has_workload & (
                service_years < cba_ruleset.free_agency_service_years
            )
            season_rates = market_rates.get(season)
            if season_rates is None:
                raise ValueError(f"missing market rate for {season}")
            rate_array = np.where(
                annual_war < 1.0,
                float(season_rates["0-1"]),
                np.where(
                    annual_war < 2.0,
                    float(season_rates["1-2"]),
                    float(season_rates["2+"]),
                ),
            )
            market_value = np.maximum(annual_war, 0.0) * rate_array
            minimum_salary = float(cba_ruleset.minimum_salary(season))
            salary = np.full(draws, minimum_salary, dtype=float)
            arbitration = active & (
                service_years >= cba_ruleset.standard_arbitration_service_years
            )
            for arbitration_class, share in arbitration_shares.items():
                class_mask = arbitration & (service_years - 2 == arbitration_class)
                salary[class_mask] = np.maximum(
                    minimum_salary, prior_market_value[class_mask] * float(share)
                )
            surplus = market_value - salary
            discount = 1.0 / (
                (1.0 + annual_discount_rate) ** (season - forecast_seasons[0] + 1)
            )
            value[active] += surplus[active] * discount
            cost[active] += salary[active] * discount
            controlled_war[active] += annual_war[active]
            service_years[active] += 1
            prior_market_value = np.where(active, market_value, 0.0)

        value_quantiles = np.quantile(value, [0.10, 0.50, 0.90], method="linear")
        war_quantiles = np.quantile(
            controlled_war, [0.10, 0.50, 0.90], method="linear"
        )
        conditional_arrival_year = (
            float(
                sum(
                    season * probability
                    for season, probability in zip(
                        forecast_seasons[:arrival_horizon_years],
                        annual_arrival,
                        strict=True,
                    )
                )
                / arrival_probability
            )
            if arrival_probability > 0.0
            else None
        )
        if player_type == "pitcher":
            any_starter_probability: float | None = float(
                (annual_roles == ROLE_CODES["starter"]).any(axis=1).mean()
            )
            active_role = np.isin(
                annual_roles,
                [
                    ROLE_CODES["starter"],
                    ROLE_CODES["swingman"],
                    ROLE_CODES["reliever"],
                ],
            )
            role_change = (
                (annual_roles[:, 1:] != annual_roles[:, :-1])
                & active_role[:, 1:]
                & active_role[:, :-1]
            ).any(axis=1)
            role_transition_probability: float | None = float(role_change.mean())
        else:
            any_starter_probability = None
            role_transition_probability = None
        rows.append(
            {
                "player_id": player_id,
                "model_player_type": player_type,
                "mean_discounted_surplus_value_dollars": float(value.mean()),
                "p10_discounted_surplus_value_dollars": float(value_quantiles[0]),
                "median_discounted_surplus_value_dollars": float(value_quantiles[1]),
                "p90_discounted_surplus_value_dollars": float(value_quantiles[2]),
                "mean_controlled_war": float(controlled_war.mean()),
                "p10_controlled_war": float(war_quantiles[0]),
                "median_controlled_war": float(war_quantiles[1]),
                "p90_controlled_war": float(war_quantiles[2]),
                "expected_discounted_cost_dollars": float(cost.mean()),
                "arrival_probability": arrival_probability,
                "simulated_arrival_probability": float(
                    (arrival_index < arrival_horizon_years).mean()
                ),
                "no_arrival_probability": 1.0 - arrival_probability,
                "bust_probability": 1.0 - float(
                    row["meaningful_only_probability"]
                    + row["established_probability"]
                ),
                "limited_probability": float(row["fringe_probability"]),
                "meaningful_only_probability": float(row["meaningful_only_probability"]),
                "regular_probability": float(row["established_probability"]),
                "star_probability": float(
                    (controlled_war >= star_war_threshold).mean()
                ),
                "conditional_mean_arrival_year": conditional_arrival_year,
                "any_starter_role_probability": any_starter_probability,
                "active_role_transition_probability": role_transition_probability,
                "simulation_draws": draws,
                "role_fallback_draw_share": role_fallback_draws / half,
                "model_id": MODEL_ID,
            }
        )
    result = pl.DataFrame(rows, infer_schema_length=None).sort("player_id")
    if result.get_column("player_id").n_unique() != result.height:
        raise RuntimeError("dependent career output violates player grain")
    probability_columns = (
        "arrival_probability",
        "simulated_arrival_probability",
        "no_arrival_probability",
        "bust_probability",
        "limited_probability",
        "meaningful_only_probability",
        "regular_probability",
        "star_probability",
        "role_fallback_draw_share",
    )
    if result.filter(
        pl.any_horizontal(
            pl.col(column).is_null()
            | ~pl.col(column).is_finite()
            | (pl.col(column) < 0.0)
            | (pl.col(column) > 1.0)
            for column in probability_columns
        )
        | (
            (
                pl.col("arrival_probability")
                + pl.col("no_arrival_probability")
                - 1.0
            ).abs()
            > 1e-8
        )
        | (
            (
                pl.col("limited_probability")
                + pl.col("meaningful_only_probability")
                + pl.col("regular_probability")
                - pl.col("arrival_probability")
            ).abs()
            > 1e-8
        )
        | (
            pl.col("star_probability")
            > pl.col("simulated_arrival_probability") + 1e-8
        )
    ).height:
        raise RuntimeError("dependent career output violates probability laws")
    numeric_columns = (
        "mean_discounted_surplus_value_dollars",
        "p10_discounted_surplus_value_dollars",
        "median_discounted_surplus_value_dollars",
        "p90_discounted_surplus_value_dollars",
        "mean_controlled_war",
        "p10_controlled_war",
        "median_controlled_war",
        "p90_controlled_war",
        "expected_discounted_cost_dollars",
    )
    if result.filter(
        pl.any_horizontal(
            pl.col(column).is_null() | ~pl.col(column).is_finite()
            for column in numeric_columns
        )
        | (
            pl.col("p10_discounted_surplus_value_dollars")
            > pl.col("median_discounted_surplus_value_dollars")
        )
        | (
            pl.col("median_discounted_surplus_value_dollars")
            > pl.col("p90_discounted_surplus_value_dollars")
        )
        | (pl.col("p10_controlled_war") > pl.col("median_controlled_war"))
        | (pl.col("median_controlled_war") > pl.col("p90_controlled_war"))
        | (pl.col("expected_discounted_cost_dollars") < 0.0)
    ).height:
        raise RuntimeError("dependent career output violates numeric or quantile laws")
    return result
