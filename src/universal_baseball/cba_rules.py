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
