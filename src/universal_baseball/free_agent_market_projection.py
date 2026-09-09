"""Chronology-safe WAR forecasts for a clean one-year free-agent sample."""

from __future__ import annotations

import math
from typing import Mapping

import polars as pl

from universal_baseball.conditional_war_rates import (
    build_hitter_conditional_war_rates,
    build_pitcher_conditional_war_rates,
)


FREE_AGENT_MINIMUM_SALARY = {
    2020: 563_500,
    2021: 570_500,
    2022: 700_000,
    2023: 720_000,
    2024: 740_000,
    2025: 760_000,
    2026: 780_000,
}
ONE_YEAR_MARKET_PROJECTION_ID = "statsapi_321_rate_workload_one_year_fa_v1"
_SHORT_SEASON_WORKLOAD_FACTORS = {2020: 162.0 / 60.0}
_POSITION_CODES = {
    "C": "2",
    "1B": "3",
    "2B": "4",
    "3B": "5",
    "SS": "6",
    "LF": "7",
    "CF": "8",
    "RF": "9",
    "OF": "O",
    "DH": "10",
}


def classify_one_year_market_rows(market: pl.DataFrame) -> pl.DataFrame:
    """Label the predeclared one-year fitting sample and every exclusion."""

    required = {
        "free_agent_year",
        "source_row_sequence",
        "fangraphs_id",
        "player_id",
        "player_name",
        "position",
        "age",
        "contract_years",
        "contract_effective_total_dollars",
        "contract_value_status",
        "identity_status",
    }
    if missing := sorted(required - set(market.columns)):
        raise ValueError(f"free-agent market rows missing columns: {missing}")
    reported = market.filter(
        pl.col("contract_value_status") == "reported_guaranteed_terms"
    )
    contract_counts = reported.group_by("free_agent_year", "player_id").len().rename(
        {"len": "reported_contract_rows_in_class"}
    )
    result = market.join(
        contract_counts,
        on=["free_agent_year", "player_id"],
        how="left",
    ).with_columns(
        pl.col("reported_contract_rows_in_class").fill_null(0),
        pl.col("free_agent_year").replace_strict(
            FREE_AGENT_MINIMUM_SALARY,
            default=None,
            return_dtype=pl.Int64,
        ).alias("major_league_minimum_salary"),
    ).with_columns(
        pl.when(pl.col("contract_value_status") != "reported_guaranteed_terms")
        .then(pl.lit("terms_not_reported_major_league"))
        .when(pl.col("contract_years") != 1)
        .then(pl.lit("not_one_year"))
        .when(pl.col("reported_contract_rows_in_class") != 1)
        .then(pl.lit("multiple_contracts_in_class"))
        .when(pl.col("identity_status") != "matched_unique")
        .then(pl.lit("identity_not_unique"))
        .when(pl.col("major_league_minimum_salary").is_null())
        .then(pl.lit("minimum_salary_not_versioned"))
        .when(
            pl.col("contract_effective_total_dollars")
            < pl.col("major_league_minimum_salary")
        )
        .then(pl.lit("below_major_league_minimum"))
        .otherwise(pl.lit("eligible"))
        .alias("sample_status")
    ).with_columns((pl.col("sample_status") == "eligible").alias("sample_eligible"))
    if result.filter(
        pl.col("sample_eligible")
        & (
            pl.col("player_id").is_null()
            | pl.col("age").is_null()
            | pl.col("contract_effective_total_dollars").is_null()
        )
    ).height:
        raise ValueError("eligible one-year rows contain missing required values")
    return result.sort(["free_agent_year", "source_row_sequence"])


def _role_flags(position: str) -> tuple[bool, bool]:
    tokens = {token for token in str(position).split("/") if token}
    pitcher = bool(tokens & {"SP", "RP"})
    hitter = bool(tokens & set(_POSITION_CODES))
    return hitter, pitcher


def _position_code(position: str) -> str:
    for token in str(position).split("/"):
        if token in _POSITION_CODES:
            return _POSITION_CODES[token]
    return ""


def _weighted_workload(
    history: pl.DataFrame,
    *,
    player_ids: list[int],
    target_season: int,
    workload_column: str,
) -> dict[int, float]:
    """Return fixed-denominator 3/2/1 workload, treating missing seasons as zero."""

    source = history.filter(
        pl.col("player_id").is_in(player_ids)
        & pl.col("season").is_between(target_season - 3, target_season - 1)
    ).group_by("season", "player_id").agg(pl.col(workload_column).sum())
    if source.is_empty():
        return {player_id: 0.0 for player_id in player_ids}
    source = source.with_columns(
        (target_season - pl.col("season")).replace_strict(
            {1: 3.0, 2: 2.0, 3: 1.0}, return_dtype=pl.Float64
        ).alias("recency_weight"),
        pl.col("season").replace_strict(
            _SHORT_SEASON_WORKLOAD_FACTORS,
            default=1.0,
            return_dtype=pl.Float64,
        ).alias("schedule_factor"),
    ).with_columns(
        (
            pl.col(workload_column)
            * pl.col("recency_weight")
            * pl.col("schedule_factor")
        ).alias("weighted_workload")
    )
    totals = {
        int(row["player_id"]): float(row["weighted_workload"]) / 6.0
        for row in source.group_by("player_id")
        .agg(pl.col("weighted_workload").sum())
        .iter_rows(named=True)
    }
    return {player_id: totals.get(player_id, 0.0) for player_id in player_ids}


def build_one_year_signing_time_war(
    classified_market: pl.DataFrame,
    hitting_history: pl.DataFrame,
    pitching_history: pl.DataFrame,
    *,
    reference_environments: Mapping[int, Mapping[str, float]],
) -> pl.DataFrame:
    """Recreate a team-neutral forecast using only evidence before each contract year."""

    contracts = classified_market.filter(pl.col("sample_eligible"))
    if contracts.is_empty():
        raise ValueError("one-year market sample is empty")
    if contracts.group_by("free_agent_year", "player_id").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("eligible one-year market sample violates player-year grain")

    rows: list[dict[str, object]] = []
    for target_season in sorted(contracts.get_column("free_agent_year").unique()):
        year = int(target_season)
        reference_year = year - 1
        try:
            environment = reference_environments[reference_year]
        except KeyError as exc:
            raise ValueError(
                f"missing reference environment for {reference_year}"
            ) from exc
        required_environment = {
            "batting_plate_appearances",
            "pitching_batters_faced",
            "runs_per_win",
        }
        if missing := sorted(required_environment - set(environment)):
            raise ValueError(
                f"reference environment {reference_year} missing fields: {missing}"
            )
        year_rows = contracts.filter(pl.col("free_agent_year") == year)
        roles = {
            int(row["player_id"]): _role_flags(str(row["position"]))
            for row in year_rows.iter_rows(named=True)
        }
        hitter_rows = year_rows.filter(
            pl.col("player_id").map_elements(
                lambda player_id: roles[int(player_id)][0],
                return_dtype=pl.Boolean,
            )
        )
        pitcher_rows = year_rows.filter(
            pl.col("player_id").map_elements(
                lambda player_id: roles[int(player_id)][1],
                return_dtype=pl.Boolean,
            )
        )
        hitter_rate: dict[int, float] = {}
        hitter_workload: dict[int, float] = {}
        if not hitter_rows.is_empty():
            hitter_players = hitter_rows.select(
                pl.col("player_id"),
                pl.col("age").cast(pl.Float64).alias("age_years"),
                pl.col("position").map_elements(
                    _position_code, return_dtype=pl.String
                ).alias("position_code"),
            )
            rates = build_hitter_conditional_war_rates(
                hitter_players,
                hitting_history.filter(pl.col("season") < year),
                current_season=year,
                forecast_seasons=(year,),
                reference_plate_appearances=int(
                    environment["batting_plate_appearances"]
                ),
                runs_per_win=float(environment["runs_per_win"]),
                evidence_anchor_season=reference_year,
                reference_season=reference_year,
            )
            hitter_rate = {
                int(row["player_id"]): float(row["conditional_war_per_600_pa"])
                for row in rates.iter_rows(named=True)
            }
            hitter_workload = _weighted_workload(
                hitting_history,
                player_ids=hitter_players.get_column("player_id").to_list(),
                target_season=year,
                workload_column="batting_plate_appearances",
            )

        pitcher_rate: dict[int, float] = {}
        pitcher_workload: dict[int, float] = {}
        if not pitcher_rows.is_empty():
            pitcher_players = pitcher_rows.select(
                pl.col("player_id"),
                pl.col("age").cast(pl.Float64).alias("age_years"),
            )
            rates = build_pitcher_conditional_war_rates(
                pitcher_players,
                pitching_history.filter(pl.col("season") < year),
                current_season=year,
                forecast_seasons=(year,),
                reference_batters_faced=int(
                    environment["pitching_batters_faced"]
                ),
                runs_per_win=float(environment["runs_per_win"]),
                evidence_anchor_season=reference_year,
                reference_season=reference_year,
            )
            pitcher_rate = {
                int(row["player_id"]): float(row["conditional_war_per_800_bf"])
                for row in rates.iter_rows(named=True)
            }
            pitcher_workload = _weighted_workload(
                pitching_history,
                player_ids=pitcher_players.get_column("player_id").to_list(),
                target_season=year,
                workload_column="pitching_batters_faced",
            )

        for contract in year_rows.iter_rows(named=True):
            player_id = int(contract["player_id"])
            hitter_role, pitcher_role = roles[player_id]
            hitter_pa = hitter_workload.get(player_id, 0.0)
            pitcher_bf = pitcher_workload.get(player_id, 0.0)
            hitter_war = hitter_rate.get(player_id, 0.0) * hitter_pa / 600.0
            pitcher_war = pitcher_rate.get(player_id, 0.0) * pitcher_bf / 800.0
            expected_war = hitter_war + pitcher_war
            if not hitter_role and not pitcher_role:
                forecast_status = "unsupported_position"
            elif hitter_pa <= 0 and pitcher_bf <= 0:
                forecast_status = "no_recent_mlb_workload"
            elif not math.isfinite(expected_war):
                raise RuntimeError("one-year market forecast produced nonfinite WAR")
            else:
                forecast_status = "available"
            rows.append(
                {
                    **contract,
                    "fangraphs_projected_war": contract.get("projected_war"),
                    "hitter_role": hitter_role,
                    "pitcher_role": pitcher_role,
                    "projected_pa": hitter_pa,
                    "projected_bf": pitcher_bf,
                    "projected_hitter_war": hitter_war,
                    "projected_pitcher_war": pitcher_war,
                    "projected_war": expected_war,
                    "forecast_status": forecast_status,
                    "market_fit_eligible": forecast_status == "available",
                    "projection_model_id": ONE_YEAR_MARKET_PROJECTION_ID,
                    "evidence_cutoff_season": reference_year,
                    "reference_environment_season": reference_year,
                    "team_depth_used": False,
                    "historical_defense_policy": "position_only_skill_neutral",
                    "historical_baserunning_policy": "league_average_zero",
                }
            )
    return pl.DataFrame(rows, infer_schema_length=None).sort(
        ["free_agent_year", "source_row_sequence"]
    )
