"""Transparent future team-control paths from a dated current snapshot."""

from __future__ import annotations

from datetime import date

import polars as pl

from universal_baseball.team_control import (
    FREE_AGENCY_SERVICE_YEARS,
    SERVICE_DAYS_PER_YEAR,
    STANDARD_ARBITRATION_SERVICE_YEARS,
)


CONTROL_PATH_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "organization_id": pl.Int64,
    "control_year": pl.Int64,
    "service_days_before_year": pl.Int64,
    "statutory_status": pl.String,
    "contract_status": pl.String,
    "control_status": pl.String,
    "projection_basis": pl.String,
}


def resolve_service_balances(players: pl.DataFrame) -> pl.DataFrame:
    """Resolve a dated service balance without inventing prior MLB service.

    FanGraphs supplies the opening balance when available. A player with no
    official MLB debut has a zero opening balance; current StatsAPI service is
    then added. Debuted players lacking the opening balance remain unresolved.
    """

    required = {"baseline_service_days", "current_service_days", "mlb_debut_date"}
    if missing := sorted(required - set(players.columns)):
        raise ValueError(f"service-balance players missing columns: {missing}")
    return players.with_columns(
        pl.col("current_service_days").fill_null(0),
    ).with_columns(
        pl.when(pl.col("baseline_service_days").is_not_null())
        .then(pl.col("baseline_service_days") + pl.col("current_service_days"))
        .when(pl.col("mlb_debut_date").is_null())
        .then(pl.col("current_service_days"))
        .otherwise(pl.lit(None, dtype=pl.Int64))
        .cast(pl.Int64)
        .alias("service_days"),
        pl.when(pl.col("baseline_service_days").is_not_null())
        .then(pl.lit("fangraphs_opening_balance_plus_statsapi_current"))
        .when(pl.col("mlb_debut_date").is_null())
        .then(pl.lit("official_no_mlb_debut_zero_opening_plus_statsapi_current"))
        .otherwise(pl.lit("unresolved_prior_mlb_service"))
        .alias("service_time_basis"),
    )


def _statutory_status(service_days: int, *, super_two_next_year: bool) -> str:
    if service_days >= FREE_AGENCY_SERVICE_YEARS * SERVICE_DAYS_PER_YEAR:
        return "free_agent_eligible"
    if service_days >= STANDARD_ARBITRATION_SERVICE_YEARS * SERVICE_DAYS_PER_YEAR:
        return "arbitration_eligible"
    if super_two_next_year:
        return "super_two_eligible"
    return "pre_arbitration"


def _contract_status(term: dict[str, object] | None) -> str:
    if term is None:
        return ""
    clauses = set(str(term.get("clause_types") or "").split(",")) - {""}
    if "player_option" in clauses:
        return "player_option"
    if "mutual_option" in clauses:
        return "mutual_option"
    if "vesting_option" in clauses:
        return "vesting_option"
    if "club_option" in clauses or "fallback_club_option" in clauses:
        return "club_option"
    label = str(term.get("term_label") or "")
    if term.get("amount_dollars") is not None:
        return "guaranteed_contract"
    if label == "free_agent":
        return "free_agent"
    if label.startswith("arbitration_"):
        return "arbitration"
    if label == "pre_arbitration":
        return "pre_arbitration"
    return ""


def project_future_control_path(
    players: pl.DataFrame,
    contract_years: pl.DataFrame,
    *,
    as_of_date: date,
    through_year: int,
) -> pl.DataFrame:
    """Project control under an explicit full-service future scenario.

    Contract terms override the statutory label for the matching current organization.
    The projection does not guess future options, injuries, demotions or transactions.
    """

    required = {
        "player_id",
        "organization_id",
        "service_days",
        "current_service_days",
        "super_two_selected",
    }
    missing = sorted(required - set(players.columns))
    if missing:
        raise ValueError(f"control path players missing columns: {missing}")
    term_required = {
        "player_id",
        "organization_id",
        "payroll_year",
        "amount_dollars",
        "term_label",
        "clause_types",
    }
    missing_terms = sorted(term_required - set(contract_years.columns))
    if missing_terms:
        raise ValueError(f"control path contract years missing columns: {missing_terms}")
    if through_year <= as_of_date.year:
        raise ValueError("through_year must be after the snapshot year")
    if players.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("control path players have duplicate identities")

    terms = {
        (int(row["player_id"]), int(row["organization_id"]), int(row["payroll_year"])): row
        for row in contract_years.iter_rows(named=True)
        if row["player_id"] is not None and row["organization_id"] is not None
    }
    rows: list[dict[str, object]] = []
    for player in players.iter_rows(named=True):
        if player["organization_id"] is None or player["service_days"] is None:
            continue
        player_id = int(player["player_id"])
        organization_id = int(player["organization_id"])
        current_service = int(player["current_service_days"] or 0)
        year_end_service = int(player["service_days"]) + max(
            SERVICE_DAYS_PER_YEAR - current_service, 0
        )
        for control_year in range(as_of_date.year + 1, through_year + 1):
            service_before = year_end_service + (
                control_year - as_of_date.year - 1
            ) * SERVICE_DAYS_PER_YEAR
            statutory = _statutory_status(
                service_before,
                super_two_next_year=bool(player["super_two_selected"])
                and control_year == as_of_date.year + 1,
            )
            contract = _contract_status(
                terms.get((player_id, organization_id, control_year))
            )
            rows.append(
                {
                    "as_of_date": as_of_date,
                    "player_id": player_id,
                    "organization_id": organization_id,
                    "control_year": control_year,
                    "service_days_before_year": service_before,
                    "statutory_status": statutory,
                    "contract_status": contract,
                    "control_status": contract or statutory,
                    "projection_basis": "full_service_future_scenario",
                }
            )
    return (
        pl.DataFrame(rows, schema=CONTROL_PATH_SCHEMA)
        if rows
        else pl.DataFrame(schema=CONTROL_PATH_SCHEMA)
    ).sort(["player_id", "control_year"])
