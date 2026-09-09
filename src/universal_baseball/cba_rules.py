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
CBA_2027_2032_PLANNING_SCENARIO = CBARuleset(
    ruleset_id="post_2026_cba_planning_scenario_3pct",
    effective_start_year=2027,
    effective_end_year=2032,
    major_league_minimum_salary=MappingProxyType(
        {
            2027: 803_400,
            2028: 827_502,
            2029: 852_327,
            2030: 877_897,
            2031: 904_234,
            2032: 931_361,
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
    ruleset_kind="research_planning_scenario_not_cba_fact",
)
