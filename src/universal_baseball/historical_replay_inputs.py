"""Build fail-closed annual economics inputs for a historical Opening Day replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import polars as pl

from universal_baseball.contract_economics import (
    ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA,
)
from universal_baseball.team_control import (
    FREE_AGENCY_SERVICE_YEARS,
    SERVICE_DAYS_PER_YEAR,
    STANDARD_ARBITRATION_SERVICE_YEARS,
)


MLB_TEAM_ID_BY_ABBREVIATION = {
    "ARI": 109,
    "ATL": 144,
    "ATH": 133,
    "BAL": 110,
    "BOS": 111,
    "CHC": 112,
    "CHW": 145,
    "CIN": 113,
    "CLE": 114,
    "COL": 115,
    "DET": 116,
    "HOU": 117,
    "KCR": 118,
    "LAA": 108,
    "LAD": 119,
    "MIA": 146,
    "MIL": 158,
    "MIN": 142,
    "NYM": 121,
    "NYY": 147,
    "PHI": 143,
    "PIT": 134,
    "SDP": 135,
    "SEA": 136,
    "SFG": 137,
    "STL": 138,
    "TBR": 139,
    "TEX": 140,
    "TOR": 141,
    "WSN": 120,
}

HISTORICAL_REPLAY_REVIEW_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "season": pl.Int64,
    "review_reason": pl.String,
}


@dataclass(frozen=True)
class HistoricalReplayInputBuild:
    annual_inputs: pl.DataFrame
    reviews: pl.DataFrame
    coverage: dict[str, int]


def _whole_player_war(
    hitter_paths: pl.DataFrame, pitcher_paths: pl.DataFrame
) -> pl.DataFrame:
    required = {"player_id", "season", "expected_war"}
    components = []
    for label, frame in (("hitter", hitter_paths), ("pitcher", pitcher_paths)):
        if missing := sorted(required - set(frame.columns)):
            raise ValueError(f"historical {label} paths missing fields: {missing}")
        component = frame.select(*sorted(required))
        if component.group_by("player_id", "season").len().filter(
            pl.col("len") != 1
        ).height:
            raise ValueError(f"historical {label} paths violate player-season grain")
        if component.filter(~pl.col("expected_war").is_finite()).height:
            raise ValueError(f"historical {label} paths contain invalid WAR")
        components.append(component)
    return (
        pl.concat(components)
        .group_by("player_id", "season")
        .agg(pl.col("expected_war").sum().alias("projected_war_mean"))
        .sort(["player_id", "season"])
    )


def _statutory_status(service_days: int, *, super_two_review: bool) -> str:
    if service_days >= FREE_AGENCY_SERVICE_YEARS * SERVICE_DAYS_PER_YEAR:
        return "free_agent_eligible"
    if service_days >= STANDARD_ARBITRATION_SERVICE_YEARS * SERVICE_DAYS_PER_YEAR:
        return "arbitration_eligible"
    if super_two_review and service_days >= 2 * SERVICE_DAYS_PER_YEAR:
        return "super_two_candidate"
    return "pre_arbitration"


def _arbitration_class(
    *, service_days: int | None, evidence_status: str
) -> int | None:
    if evidence_status.startswith("explicit_a"):
        return int(evidence_status[-1])
    if service_days is None:
        return None
    return max(1, min(4, service_days // SERVICE_DAYS_PER_YEAR - 2))


def build_historical_replay_economics_inputs(
    hitter_paths: pl.DataFrame,
    pitcher_paths: pl.DataFrame,
    opening_control: pl.DataFrame,
    valuation_terms: pl.DataFrame,
    *,
    as_of_date: date,
    projection_source_id: str,
) -> HistoricalReplayInputBuild:
    """Join projections to dated control and gated contract evidence.

    The Opening Day team is held fixed only for the projected incumbent-control
    path. Explicit free agency ends that path. Missing service, Super Two status,
    identities and option structure remain review instead of receiving assumptions.
    """

    opening_required = {
        "player_id",
        "team_abbreviation",
        "service_days",
        "source_snapshot_id",
    }
    term_required = {
        "player_id",
        "payroll_year",
        "accepted_salary_dollars",
        "contract_status",
        "evidence_status",
        "review_reason",
        "source_snapshot_id",
    }
    if missing := sorted(opening_required - set(opening_control.columns)):
        raise ValueError(f"historical opening control missing fields: {missing}")
    if missing := sorted(term_required - set(valuation_terms.columns)):
        raise ValueError(f"historical valuation terms missing fields: {missing}")
    if not projection_source_id:
        raise ValueError("historical projection source ID is required")
    if opening_control.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("historical opening control violates player grain")
    reported_teams = set(opening_control.get_column("team_abbreviation").to_list())
    unknown_teams = reported_teams - set(MLB_TEAM_ID_BY_ABBREVIATION) - {""}
    if unknown_teams:
        raise ValueError(f"historical opening control has unknown teams: {unknown_teams}")

    whole_player = _whole_player_war(hitter_paths, pitcher_paths)
    seasons = sorted(whole_player.get_column("season").unique().to_list())
    if not seasons or seasons[0] != as_of_date.year:
        raise ValueError("historical projection seasons must begin in the cutoff year")
    terms = valuation_terms.filter(pl.col("player_id").is_not_null()).select(
        *sorted(term_required)
    )
    if terms.group_by("player_id", "payroll_year").len().filter(
        pl.col("len") != 1
    ).height:
        raise ValueError("historical valuation terms violate player-year grain")
    term_lookup = {
        (int(row["player_id"]), int(row["payroll_year"])): row
        for row in terms.iter_rows(named=True)
    }
    war_lookup = {
        (int(row["player_id"]), int(row["season"])): float(
            row["projected_war_mean"]
        )
        for row in whole_player.iter_rows(named=True)
    }

    rows: list[dict[str, object]] = []
    reviews: list[dict[str, object]] = []
    opening_ids = set(opening_control.get_column("player_id").to_list())
    for player_id, season in whole_player.select("player_id", "season").iter_rows():
        if int(player_id) not in opening_ids:
            reviews.append(
                {
                    "as_of_date": as_of_date,
                    "player_id": int(player_id),
                    "season": int(season),
                    "review_reason": "missing_historical_opening_owner",
                }
            )

    for opening in opening_control.iter_rows(named=True):
        player_id = int(opening["player_id"])
        team_abbreviation = str(opening["team_abbreviation"])
        if not team_abbreviation:
            for season in seasons:
                if (player_id, int(season)) in war_lookup:
                    reviews.append(
                        {
                            "as_of_date": as_of_date,
                            "player_id": player_id,
                            "season": int(season),
                            "review_reason": "missing_historical_opening_owner",
                        }
                    )
            continue
        organization_id = MLB_TEAM_ID_BY_ABBREVIATION[team_abbreviation]
        opening_service = opening["service_days"]
        control_ended = False
        for season in seasons:
            war = war_lookup.get((player_id, int(season)))
            if war is None:
                reviews.append(
                    {
                        "as_of_date": as_of_date,
                        "player_id": player_id,
                        "season": int(season),
                        "review_reason": "opening_control_player_missing_projection",
                    }
                )
                continue
            service_days = (
                None
                if opening_service is None
                else int(opening_service)
                + (int(season) - as_of_date.year) * SERVICE_DAYS_PER_YEAR
            )
            term = term_lookup.get((player_id, int(season)))
            term_status = "" if term is None else str(term["contract_status"])
            evidence_status = "" if term is None else str(term["evidence_status"])
            known_salary = None if term is None else term["accepted_salary_dollars"]
            structure_review = ""

            if term_status == "guaranteed_contract":
                control_status = "guaranteed_contract"
            elif term_status == "arbitration_eligible":
                control_status = "arbitration_eligible"
            elif term_status == "free_agent":
                control_status = "free_agent"
                control_ended = True
            elif term_status == "option_unresolved":
                control_status = "vesting_option"
                structure_review = str(term["review_reason"])
            elif term_status in {"identity_unresolved", "contract_amount_unresolved"}:
                control_status = "historical_control_unresolved"
                structure_review = str(term["review_reason"] or term_status)
            elif control_ended:
                control_status = "free_agent"
            elif service_days is None:
                control_status = "historical_control_unresolved"
                structure_review = "missing_historical_opening_service"
            else:
                control_status = _statutory_status(
                    service_days, super_two_review=int(season) == as_of_date.year
                )
                if control_status == "super_two_candidate":
                    structure_review = "historical_super_two_status_unresolved"

            is_arbitration = control_status in {
                "arbitration_eligible",
                "super_two_eligible",
            }
            arbitration_class = (
                _arbitration_class(
                    service_days=service_days, evidence_status=evidence_status
                )
                if is_arbitration
                else None
            )
            prior_war = war_lookup.get((player_id, int(season) - 1))
            contract_sources = [str(opening["source_snapshot_id"])]
            if term is not None:
                contract_sources.append(str(term["source_snapshot_id"]))
            rows.append(
                {
                    "as_of_date": as_of_date,
                    "player_id": player_id,
                    "organization_id": organization_id,
                    "season": int(season),
                    "projected_war_mean": war,
                    "projected_war_lower": None,
                    "projected_war_upper": None,
                    "control_status": control_status,
                    "known_salary_dollars": known_salary,
                    "buyout_dollars": None,
                    "arbitration_class": arbitration_class,
                    "arbitration_salary_basis_war": (
                        prior_war if prior_war is not None else war
                    )
                    if is_arbitration
                    else None,
                    "arbitration_salary_basis_source": (
                        "prior_season_projected_war"
                        if is_arbitration and prior_war is not None
                        else "same_season_proxy_first_horizon"
                        if is_arbitration
                        else ""
                    ),
                    "projection_source_id": projection_source_id,
                    "contract_source_id": "+".join(contract_sources),
                    "contract_structure_review_reason": structure_review,
                }
            )

    annual = pl.DataFrame(
        rows, schema=ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA
    ).sort(["player_id", "season"])
    review_frame = pl.DataFrame(
        reviews, schema=HISTORICAL_REPLAY_REVIEW_SCHEMA
    ).sort(["player_id", "season"])
    return HistoricalReplayInputBuild(
        annual_inputs=annual,
        reviews=review_frame,
        coverage={
            "whole_player_projection_rows": whole_player.height,
            "control_owner_players": opening_control.height,
            "economics_input_rows": annual.height,
            "projection_rows_without_opening_owner": review_frame.filter(
                pl.col("review_reason") == "missing_historical_opening_owner"
            ).height,
            "opening_rows_without_projection": review_frame.filter(
                pl.col("review_reason")
                == "opening_control_player_missing_projection"
            ).height,
            "known_salary_rows": annual.filter(
                pl.col("known_salary_dollars").is_not_null()
            ).height,
            "prevaluation_review_rows": annual.filter(
                pl.col("contract_structure_review_reason") != ""
            ).height,
        },
    )
