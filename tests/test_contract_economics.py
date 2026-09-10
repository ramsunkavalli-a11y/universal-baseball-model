from datetime import date

import polars as pl
import pytest

from universal_baseball.cba_rules import (
    CBA_2022_2026,
    CBA_2027_2032_PLANNING_SCENARIO,
)
from universal_baseball.contract_economics import (
    ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA,
    ContractEconomicsAssumptions,
    value_annual_contract_states,
)


ASSUMPTIONS = ContractEconomicsAssumptions(
    assumptions_id="test_economics_v0",
    market_model_id="test_linear_10m_per_war",
    arbitration_model_id="test_configured_shares",
    dollars_per_war_by_year={2026: 10_000_000.0},
    arbitration_share_by_class={1: 0.25, 2: 0.4, 3: 0.6, 4: 0.8},
    annual_discount_rate=0.05,
)


def _input(
    *,
    player_id: int = 1,
    war: float = 1.0,
    status: str,
    salary: int | None = None,
    buyout: int | None = None,
    arbitration_class: int | None = None,
    arbitration_basis_war: float | None = None,
    lower: float | None = 0.0,
    upper: float | None = 2.0,
) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "as_of_date": date(2026, 9, 8),
                "player_id": player_id,
                "organization_id": 135,
                "season": 2026,
                "projected_war_mean": war,
                "projected_war_lower": lower,
                "projected_war_upper": upper,
                "control_status": status,
                "known_salary_dollars": salary,
                "buyout_dollars": buyout,
                "arbitration_class": arbitration_class,
                "arbitration_salary_basis_war": (
                    war if arbitration_basis_war is None else arbitration_basis_war
                ),
                "arbitration_salary_basis_source": "test_prior_season",
                "projection_source_id": "projection:test",
                "contract_source_id": "contract:test",
                "contract_structure_review_reason": "",
            }
        ],
        schema=ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA,
    )


def _annual(**kwargs: object) -> dict[str, object]:
    result = value_annual_contract_states(
        _input(**kwargs), cba_ruleset=CBA_2022_2026, assumptions=ASSUMPTIONS
    )
    assert result.reviews.is_empty()
    return result.annual.row(0, named=True)


def test_cba_ruleset_has_official_2022_2026_minimum_schedule() -> None:
    assert CBA_2022_2026.minimum_salary(2022) == 700_000
    assert CBA_2022_2026.minimum_salary(2026) == 780_000


def test_post_2026_rules_are_explicitly_nonofficial_scenario() -> None:
    scenario = CBA_2027_2032_PLANNING_SCENARIO
    assert scenario.ruleset_kind == "research_planning_scenario_not_cba_fact"
    assert scenario.minimum_salary(2027) == 803_400
    assert scenario.minimum_salary(2032) == 931_361


def test_guaranteed_contract_retains_bad_state_liability() -> None:
    row = _annual(status="guaranteed_contract", salary=15_000_000)
    assert row["fa_equivalent_value_dollars"] == 10_000_000
    assert row["contract_control_value_dollars"] == -5_000_000
    assert row["optionality_premium_dollars"] == 0
    assert row["decision_at_mean"] == "guaranteed"


def test_pre_arbitration_non_tender_preserves_club_optionality() -> None:
    row = _annual(status="pre_arbitration", war=-1.0, lower=-2.0, upper=1.0)
    assert row["salary_basis"] == "cba_minimum"
    assert row["static_surplus_dollars"] == -780_000
    assert row["contract_control_value_dollars"] == 0
    assert row["optionality_premium_dollars"] == 780_000
    assert row["decision_at_mean"] == "non_tender"
    assert row["contract_value_upper_dollars"] == 9_220_000


def test_arbitration_approximation_is_explicit_and_tenderable() -> None:
    row = _annual(status="arbitration", war=2.0, arbitration_class=1)
    assert row["salary_basis"] == (
        "configured_arbitration_share_of_test_prior_season"
    )
    assert row["salary_cost_dollars"] == 5_000_000
    assert row["contract_control_value_dollars"] == 15_000_000
    assert row["decision_at_mean"] == "tender"


def test_arbitration_salary_uses_prior_performance_not_current_projection() -> None:
    row = _annual(
        status="arbitration", war=3.0, arbitration_class=1,
        arbitration_basis_war=1.0, upper=4.0,
    )
    assert row["salary_cost_dollars"] == 2_500_000
    assert row["fa_equivalent_value_dollars"] == 30_000_000


def test_club_option_selects_decline_branch_and_buyout() -> None:
    row = _annual(status="club_option", salary=15_000_000, buyout=2_000_000)
    assert row["static_surplus_dollars"] == -5_000_000
    assert row["salary_cost_dollars"] == 2_000_000
    assert row["contract_control_value_dollars"] == -2_000_000
    assert row["optionality_premium_dollars"] == 3_000_000
    assert row["decision_at_mean"] == "decline_club_option"


def test_player_option_exposes_adverse_optionality() -> None:
    row = _annual(
        status="player_option", war=2.0, salary=12_000_000, buyout=0
    )
    assert row["static_surplus_dollars"] == 8_000_000
    assert row["contract_control_value_dollars"] == 0
    assert row["optionality_premium_dollars"] == -8_000_000
    assert row["decision_at_mean"] == "player_leaves"


def test_free_agent_has_market_value_but_no_incumbent_control_value() -> None:
    row = _annual(status="free_agent")
    assert row["fa_equivalent_value_dollars"] == 10_000_000
    assert row["contract_control_value_dollars"] == 0
    assert row["decision_at_mean"] == "no_incumbent_rights"


def test_mutual_option_uses_conservative_expiration_outcome() -> None:
    row = _annual(
        status="mutual_option", war=2.0, salary=10_000_000, buyout=1_000_000
    )
    assert row["salary_cost_dollars"] == 1_000_000
    assert row["contract_control_value_dollars"] == -1_000_000
    assert row["decision_at_mean"] == "decline_mutual_option"


def test_mutual_option_without_buyout_fails_closed_and_blocks_aggregate() -> None:
    result = value_annual_contract_states(
        _input(status="mutual_option", salary=10_000_000),
        cba_ruleset=CBA_2022_2026,
        assumptions=ASSUMPTIONS,
    )
    assert result.reviews.height == 1
    assert "explicit buyout" in result.reviews.item(0, "review_reason")
    assert result.aggregate.item(0, "calculation_status") == "review"
    assert result.aggregate.item(0, "contract_control_value_dollars") is None
    assert result.aggregate.item(0, "calculated_annual_rows") == 0
    assert result.aggregate.item(
        0, "calculated_discounted_contract_value_dollars"
    ) == 0


def test_reviewed_player_preserves_calculated_year_subtotal_without_ranking() -> None:
    source = pl.concat(
        [
            _input(status="guaranteed_contract", salary=5_000_000),
            _input(status="vesting_option", salary=12_000_000).with_columns(
                pl.lit(2027, dtype=pl.Int64).alias("season")
            ),
        ]
    )
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="partial_visibility",
        market_model_id="flat",
        arbitration_model_id="test",
        dollars_per_war_by_year={2026: 10_000_000.0, 2027: 10_000_000.0},
        arbitration_share_by_class={},
        annual_discount_rate=0.0,
    )
    result = value_annual_contract_states(
        source, cba_ruleset=CBA_2027_2032_PLANNING_SCENARIO, assumptions=assumptions
    )
    aggregate = result.aggregate.row(0, named=True)
    assert aggregate["calculation_status"] == "review"
    assert aggregate["contract_control_value_dollars"] is None
    assert aggregate["calculated_annual_rows"] == 1
    assert aggregate["review_rows"] == 1
    assert aggregate["calculated_salary_cost_dollars"] == 5_000_000
    assert aggregate["calculated_discounted_contract_value_dollars"] == 5_000_000


def test_named_missing_buyout_share_keeps_estimate_explicit() -> None:
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="test_buyout_imputation",
        market_model_id="test_linear_10m_per_war",
        arbitration_model_id="test",
        dollars_per_war_by_year={2026: 10_000_000.0},
        arbitration_share_by_class={},
        annual_discount_rate=0.0,
        missing_buyout_share_by_status={"club_option": 0.1},
    )
    result = value_annual_contract_states(
        _input(status="club_option", salary=15_000_000),
        cba_ruleset=CBA_2022_2026,
        assumptions=assumptions,
    )
    row = result.annual.row(0, named=True)
    assert row["calculation_status"] == "available"
    assert row["salary_cost_dollars"] == 1_500_000
    assert row["salary_basis"] == "known_contract_assumed_club_option_buyout_share"
    assert row["decision_at_mean"] == "decline_club_option"


def test_invalid_missing_buyout_share_fails_closed() -> None:
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="bad_buyout_imputation",
        market_model_id="test",
        arbitration_model_id="test",
        dollars_per_war_by_year={2026: 10_000_000.0},
        arbitration_share_by_class={},
        annual_discount_rate=0.0,
        missing_buyout_share_by_status={"guaranteed_contract": 0.1},
    )
    with pytest.raises(ValueError, match="missing-buyout shares"):
        value_annual_contract_states(
            _input(status="guaranteed_contract", salary=15_000_000),
            cba_ruleset=CBA_2022_2026,
            assumptions=assumptions,
        )


def test_source_structure_disagreement_blocks_value() -> None:
    source = _input(status="club_option", salary=10_000_000, buyout=0).with_columns(
        pl.lit("secondary source identifies a player opt-out").alias(
            "contract_structure_review_reason"
        )
    )
    result = value_annual_contract_states(
        source, cba_ruleset=CBA_2022_2026, assumptions=ASSUMPTIONS
    )
    assert result.reviews.height == 1
    assert result.reviews.item(0, "review_reason") == (
        "secondary source identifies a player opt-out"
    )


def test_post_2026_minimum_requires_a_successor_ruleset() -> None:
    source = _input(status="pre_arbitration").with_columns(
        pl.lit(2027).alias("season")
    )
    future_assumptions = ContractEconomicsAssumptions(
        assumptions_id="future_test",
        market_model_id="future_market_test",
        arbitration_model_id="future_arb_test",
        dollars_per_war_by_year={2027: 10_000_000.0},
        arbitration_share_by_class={1: 0.25},
        annual_discount_rate=0.05,
    )
    result = value_annual_contract_states(
        source, cba_ruleset=CBA_2022_2026, assumptions=future_assumptions
    )
    assert result.reviews.height == 1
    assert "does not define the MLB minimum for 2027" in result.reviews.item(
        0, "review_reason"
    )


def test_discounting_is_explicit() -> None:
    source = _input(status="guaranteed_contract", salary=5_000_000).with_columns(
        pl.lit(date(2025, 12, 31)).cast(pl.Date).alias("as_of_date")
    )
    result = value_annual_contract_states(
        source, cba_ruleset=CBA_2022_2026, assumptions=ASSUMPTIONS
    )
    assert result.annual.item(0, "discount_factor") == 1 / 1.05
    assert result.annual.item(0, "discounted_contract_value_dollars") == pytest.approx(
        5_000_000 / 1.05
    )
    assert result.aggregate.item(
        0, "discounted_contract_value_lower_dollars"
    ) == pytest.approx(-5_000_000 / 1.05)
    assert result.aggregate.item(
        0, "discounted_contract_value_upper_dollars"
    ) == pytest.approx(15_000_000 / 1.05)


def test_tiered_market_uses_mean_war_tier_for_all_sensitivities() -> None:
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="tier_test",
        market_model_id="three_tier_test",
        arbitration_model_id="test",
        dollars_per_war_by_year={},
        arbitration_share_by_class={},
        annual_discount_rate=0.0,
        tiered_dollars_per_war_by_year={
            2026: {"0-1": 6_000_000, "1-2": 8_000_000, "2+": 12_000_000}
        },
    )
    source = _input(
        status="guaranteed_contract", war=2.0, salary=10_000_000,
        lower=0.5, upper=3.0,
    ).with_columns(
        pl.lit(date(2025, 12, 31)).cast(pl.Date).alias("as_of_date")
    )
    result = value_annual_contract_states(
        source,
        cba_ruleset=CBA_2022_2026,
        assumptions=assumptions,
    ).annual.row(0, named=True)
    assert result["market_war_tier"] == "2+"
    assert result["dollars_per_war"] == 12_000_000
    assert result["contract_value_lower_dollars"] == -4_000_000
    assert result["contract_value_upper_dollars"] == 26_000_000


def test_tiered_market_rejects_rest_of_season_war_as_tier_input() -> None:
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="tier_test",
        market_model_id="three_tier_test",
        arbitration_model_id="test",
        dollars_per_war_by_year={},
        arbitration_share_by_class={},
        annual_discount_rate=0.0,
        tiered_dollars_per_war_by_year={
            2026: {"0-1": 6_000_000, "1-2": 8_000_000, "2+": 12_000_000}
        },
    )
    result = value_annual_contract_states(
        _input(status="current_season_committed", salary=5_000_000),
        cba_ruleset=CBA_2022_2026,
        assumptions=assumptions,
    )
    assert result.reviews.height == 1
    assert "full-season WAR tier" in result.reviews.item(0, "review_reason")


def test_market_tier_can_stay_anchored_to_first_full_future_season() -> None:
    source = pl.concat(
        [
            _input(
                status="guaranteed_contract", war=2.1, salary=1, lower=0.0, upper=3.0
            ).with_columns(
                pl.lit(2027).alias("season")
            ),
            _input(
                status="guaranteed_contract", war=1.9, salary=1, lower=0.0, upper=3.0
            ).with_columns(
                pl.lit(2028).alias("season")
            ),
        ]
    )
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="anchored",
        market_model_id="tiered",
        arbitration_model_id="arb",
        dollars_per_war_by_year={},
        tiered_dollars_per_war_by_year={
            2027: {"0-1": 6_000_000, "1-2": 8_000_000, "2+": 12_000_000},
            2028: {"0-1": 6_000_000, "1-2": 8_000_000, "2+": 12_000_000},
        },
        arbitration_share_by_class={},
        annual_discount_rate=0.1,
        market_tier_assignment="first_full_future_season",
    )

    result = value_annual_contract_states(
        source,
        cba_ruleset=CBA_2027_2032_PLANNING_SCENARIO,
        assumptions=assumptions,
    ).annual

    assert result.get_column("market_war_tier").to_list() == ["2+", "2+"]
    assert result.get_column("dollars_per_war").to_list() == [12_000_000, 12_000_000]


def test_phase2_non_tender_ends_later_incumbent_rights() -> None:
    source = pl.concat(
        [
            _input(status="pre_arbitration", war=0.0).with_columns(
                pl.lit(2027).alias("season")
            ),
            _input(status="pre_arbitration", war=2.0).with_columns(
                pl.lit(2028).alias("season")
            ),
        ]
    )
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="sequential",
        market_model_id="flat",
        arbitration_model_id="arb",
        dollars_per_war_by_year={2027: 10_000_000, 2028: 10_000_000},
        arbitration_share_by_class={},
        annual_discount_rate=0.1,
        sequential_non_tender=True,
    )

    result = value_annual_contract_states(
        source,
        cba_ruleset=CBA_2027_2032_PLANNING_SCENARIO,
        assumptions=assumptions,
    ).annual

    assert result.get_column("decision_at_mean").to_list() == [
        "non_tender",
        "prior_non_tender_no_incumbent_rights",
    ]
    assert result.item(1, "discounted_contract_value_dollars") == 0
