"""Named free-agent market references and transparent future scenarios."""

from __future__ import annotations

import math
from types import MappingProxyType


FANGRAPHS_2026_MARKET_SOURCE_URL = (
    "https://blogs.fangraphs.com/what-are-teams-paying-for-a-win-in-free-agency-"
    "2026-edition/"
)
FANGRAPHS_2026_MARKET_REFERENCE_ID = "fangraphs_clemens_2026_three_tier"
FANGRAPHS_2026_DOLLARS_PER_WAR = MappingProxyType(
    {
        "0-1": 6_740_000.0,
        "1-2": 8_510_000.0,
        "2+": 12_840_000.0,
    }
)
FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR = MappingProxyType(
    {
        2020: 10_850_000.0,
        2021: 6_700_000.0,
        2022: 11_240_000.0,
        2023: 10_340_000.0,
        2024: 12_080_000.0,
        2025: 11_920_000.0,
        2026: 11_230_000.0,
    }
)


def market_war_tier(projected_war: float) -> str:
    """Assign the published whole-season 0–1, 1–2, or 2+ WAR tier."""

    war = float(projected_war)
    if not math.isfinite(war):
        raise ValueError("projected WAR must be finite")
    if war < 1.0:
        return "0-1"
    if war < 2.0:
        return "1-2"
    return "2+"


def build_fangraphs_2026_market_scenario(
    *,
    start_season: int,
    end_season: int,
    annual_growth_rate: float,
) -> dict[int, dict[str, float]]:
    """Extend the 2026 reference under an explicit, non-CBA growth assumption."""

    if start_season < 2026 or end_season < start_season:
        raise ValueError("market scenario requires 2026-or-later ordered seasons")
    growth = float(annual_growth_rate)
    if not math.isfinite(growth) or growth < 0:
        raise ValueError("annual market growth must be finite and nonnegative")
    return {
        season: {
            tier: rate * (1.0 + growth) ** (season - 2026)
            for tier, rate in FANGRAPHS_2026_DOLLARS_PER_WAR.items()
        }
        for season in range(start_season, end_season + 1)
    }
