"""Named Phase 1 arbitration salary reference."""

from __future__ import annotations

from types import MappingProxyType


FANGRAPHS_2026_ARBITRATION_SOURCE_URL = (
    "https://blogs.fangraphs.com/the-details-of-our-new-prospect-valuation-"
    "methodology/"
)
FANGRAPHS_2026_ARBITRATION_MODEL_ID = (
    "fangraphs_2026_prior_war_value_arbitration_shares"
)
FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS = MappingProxyType(
    {1: 0.15, 2: 0.35, 3: 0.50, 4: 0.75}
)
