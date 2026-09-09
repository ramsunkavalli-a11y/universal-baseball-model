from universal_baseball.free_agent_market import (
    FANGRAPHS_2026_DOLLARS_PER_WAR,
    FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR,
)

from scripts.materialize_current_and_future_contract_economics import (
    build_assumptions,
)


def test_integrated_scenario_uses_flat_current_and_tiered_future_market() -> None:
    assumptions = build_assumptions(
        as_of_year=2026,
        end_season=2028,
        buyout_payload={
            "assumptions": [
                {
                    "control_status": "club_option",
                    "buyout_share_of_option_salary": 0.1,
                }
            ]
        },
    )

    assert assumptions.dollars_per_war_by_year == {
        2026: FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR[2026]
    }
    assert 2026 not in assumptions.tiered_dollars_per_war_by_year
    assert assumptions.tiered_dollars_per_war_by_year[2027]["2+"] == (
        FANGRAPHS_2026_DOLLARS_PER_WAR["2+"] * 1.03
    )
    assert assumptions.missing_buyout_share_by_status == {"club_option": 0.1}
