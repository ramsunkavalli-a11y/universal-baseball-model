import pytest

from universal_baseball.free_agent_market import (
    FANGRAPHS_2026_DOLLARS_PER_WAR,
    build_fangraphs_2026_market_scenario,
    market_war_tier,
)


def test_market_tiers_use_whole_season_projected_war() -> None:
    assert market_war_tier(-1.0) == "0-1"
    assert market_war_tier(0.999) == "0-1"
    assert market_war_tier(1.0) == "1-2"
    assert market_war_tier(2.0) == "2+"


def test_market_scenario_preserves_reference_and_explicit_growth() -> None:
    result = build_fangraphs_2026_market_scenario(
        start_season=2026, end_season=2028, annual_growth_rate=0.03
    )
    assert result[2026] == dict(FANGRAPHS_2026_DOLLARS_PER_WAR)
    assert result[2028]["2+"] == pytest.approx(12_840_000 * 1.03**2)
