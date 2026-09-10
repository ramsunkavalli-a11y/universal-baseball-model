"""Versioned Collective Bargaining Agreement rules used by economics layers."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class CBARuleset:
    """Small immutable CBA surface; a successor agreement requires a new instance."""

    ruleset_id: str
    effective_start_year: int
    effective_end_year: int
    major_league_minimum_salary: Mapping[int, int]
    service_days_per_year: int
    option_days_per_year: int
    standard_option_years: int
    fourth_option_full_seasons_threshold: int
    full_pro_season_active_days: int
    full_pro_season_min_active_days: int
    standard_arbitration_service_years: int
    free_agency_service_years: int
    super_two_min_service_years: int
    super_two_share: float
    super_two_min_current_days: int
    source_url: str
    ruleset_kind: str = "official_cba"

    def minimum_salary(self, season: int) -> int:
        """Return the official minimum or fail outside the ruleset's coverage."""

        try:
            return int(self.major_league_minimum_salary[season])
        except KeyError as exc:
            raise ValueError(
                f"{self.ruleset_id} does not define the MLB minimum for {season}"
            ) from exc


CBA_2022_2026 = CBARuleset(
    ruleset_id="mlb_cba_2022_2026",
    effective_start_year=2022,
    effective_end_year=2026,
    major_league_minimum_salary=MappingProxyType(
        {
            2022: 700_000,
            2023: 720_000,
            2024: 740_000,
            2025: 760_000,
            2026: 780_000,
        }
    ),
    service_days_per_year=172,
    option_days_per_year=20,
    standard_option_years=3,
    fourth_option_full_seasons_threshold=5,
    full_pro_season_active_days=90,
    full_pro_season_min_active_days=30,
    standard_arbitration_service_years=3,
    free_agency_service_years=6,
    super_two_min_service_years=2,
    super_two_share=0.22,
    super_two_min_current_days=86,
    source_url=(
        "https://www.mlbplayers.com/_files/ugd/"
        "4d23dc_d6dfc2344d2042de973e37de62484da5.pdf"
    ),
)


# Research continuity only. The successor agreement was not available at the
# 2026-09-09 cutoff, so these values and unchanged eligibility rules are assumptions,
# not CBA facts. A signed agreement must create a new official ruleset.
def build_post_2026_cba_planning_scenario(
    *, end_year: int, annual_minimum_growth: float = 0.03
) -> CBARuleset:
    """Extend current CBA mechanics as an explicit non-factual planning scenario."""

    if end_year < 2027 or annual_minimum_growth < 0:
        raise ValueError("post-2026 planning scenario requires a valid end year and growth")
    minimums = {
        season: round(
            CBA_2022_2026.major_league_minimum_salary[2026]
            * (1.0 + annual_minimum_growth) ** (season - 2026)
        )
        for season in range(2027, end_year + 1)
    }
    suffix = "3pct" if annual_minimum_growth == 0.03 else f"{annual_minimum_growth:.6f}"
    ruleset_id = (
        "post_2026_cba_planning_scenario_3pct"
        if end_year == 2032 and annual_minimum_growth == 0.03
        else f"post_2026_cba_planning_scenario_{suffix}_through_{end_year}"
    )
    return CBARuleset(
        ruleset_id=ruleset_id,
        effective_start_year=2027,
        effective_end_year=end_year,
        major_league_minimum_salary=MappingProxyType(minimums),
        service_days_per_year=CBA_2022_2026.service_days_per_year,
        option_days_per_year=CBA_2022_2026.option_days_per_year,
        standard_option_years=CBA_2022_2026.standard_option_years,
        fourth_option_full_seasons_threshold=(
            CBA_2022_2026.fourth_option_full_seasons_threshold
        ),
        full_pro_season_active_days=CBA_2022_2026.full_pro_season_active_days,
        full_pro_season_min_active_days=CBA_2022_2026.full_pro_season_min_active_days,
        standard_arbitration_service_years=(
            CBA_2022_2026.standard_arbitration_service_years
        ),
        free_agency_service_years=CBA_2022_2026.free_agency_service_years,
        super_two_min_service_years=CBA_2022_2026.super_two_min_service_years,
        super_two_share=CBA_2022_2026.super_two_share,
        super_two_min_current_days=CBA_2022_2026.super_two_min_current_days,
        source_url=CBA_2022_2026.source_url,
        ruleset_kind="research_planning_scenario_not_cba_fact",
    )


CBA_2027_2032_PLANNING_SCENARIO = build_post_2026_cba_planning_scenario(
    end_year=2032
)


# Historical replay only. The 2025-2026 values are official CBA facts; later
# minimums and unchanged eligibility rules are the same explicit 3% continuity
# assumptions used by the current research scenario.
CBA_2025_2029_HISTORICAL_REPLAY_SCENARIO = CBARuleset(
    ruleset_id="historical_2025_replay_official_then_post2026_planning_3pct",
    effective_start_year=2025,
    effective_end_year=2029,
    major_league_minimum_salary=MappingProxyType(
        {
            2025: CBA_2022_2026.major_league_minimum_salary[2025],
            2026: CBA_2022_2026.major_league_minimum_salary[2026],
            2027: CBA_2027_2032_PLANNING_SCENARIO.major_league_minimum_salary[2027],
            2028: CBA_2027_2032_PLANNING_SCENARIO.major_league_minimum_salary[2028],
            2029: CBA_2027_2032_PLANNING_SCENARIO.major_league_minimum_salary[2029],
        }
    ),
    service_days_per_year=CBA_2022_2026.service_days_per_year,
    option_days_per_year=CBA_2022_2026.option_days_per_year,
    standard_option_years=CBA_2022_2026.standard_option_years,
    fourth_option_full_seasons_threshold=(
        CBA_2022_2026.fourth_option_full_seasons_threshold
    ),
    full_pro_season_active_days=CBA_2022_2026.full_pro_season_active_days,
    full_pro_season_min_active_days=CBA_2022_2026.full_pro_season_min_active_days,
    standard_arbitration_service_years=(
        CBA_2022_2026.standard_arbitration_service_years
    ),
    free_agency_service_years=CBA_2022_2026.free_agency_service_years,
    super_two_min_service_years=CBA_2022_2026.super_two_min_service_years,
    super_two_share=CBA_2022_2026.super_two_share,
    super_two_min_current_days=CBA_2022_2026.super_two_min_current_days,
    source_url=CBA_2022_2026.source_url,
    ruleset_kind="historical_replay_mixed_official_and_planning_scenario",
)
