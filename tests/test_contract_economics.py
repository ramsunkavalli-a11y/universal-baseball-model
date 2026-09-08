from datetime import date

import polars as pl
import pytest

from universal_baseball.cba_rules import CBA_2022_2026
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
                "projection_source_id": "projection:test",
                "contract_source_id": "contract:test",
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
    assert row["salary_basis"] == "configured_arbitration_share"
    assert row["salary_cost_dollars"] == 5_000_000
    assert row["contract_control_value_dollars"] == 15_000_000
    assert row["decision_at_mean"] == "tender"


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


def test_unresolved_option_state_fails_closed_and_blocks_aggregate() -> None:
    result = value_annual_contract_states(
        _input(status="mutual_option", salary=10_000_000, buyout=1_000_000),
        cba_ruleset=CBA_2022_2026,
        assumptions=ASSUMPTIONS,
    )
    assert result.reviews.height == 1
    assert "trigger/decision model" in result.reviews.item(0, "review_reason")
    assert result.aggregate.item(0, "calculation_status") == "review"
    assert result.aggregate.item(0, "contract_control_value_dollars") is None


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
