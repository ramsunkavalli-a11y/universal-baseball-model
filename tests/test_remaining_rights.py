from datetime import date

import polars as pl
import pytest

from universal_baseball.cba_rules import CBA_2022_2026
from universal_baseball.contract_economics import (
    ContractEconomicsAssumptions,
    value_annual_contract_states,
)
from universal_baseball.remaining_rights import (
    REMAINING_RIGHTS_INPUT_SCHEMA,
    build_remaining_rights_inputs,
)


def _rows() -> pl.DataFrame:
    common = {
        "as_of_date": date(2026, 9, 8),
        "player_id": 1,
        "organization_id": 135,
        "buyout_dollars": None,
        "arbitration_class": None,
        "projection_source_id": "projection:test",
        "contract_source_id": "contract:test",
    }
    return pl.DataFrame(
        [
            {
                **common,
                "season": 2026,
                "forecast_scope": "remaining_current_season",
                "realized_war_to_date": 4.0,
                "projected_remaining_war_mean": 0.5,
                "projected_remaining_war_lower": 0.0,
                "projected_remaining_war_upper": 1.0,
                "control_status": "pre_arbitration",
                "salary_obligation_dollars": 100_000,
            },
            {
                **common,
                "season": 2027,
                "forecast_scope": "full_future_season",
                "realized_war_to_date": 0.0,
                "projected_remaining_war_mean": 3.0,
                "projected_remaining_war_lower": 1.0,
                "projected_remaining_war_upper": 5.0,
                "control_status": "arbitration",
                "salary_obligation_dollars": 5_000_000,
            },
        ],
        schema=REMAINING_RIGHTS_INPUT_SCHEMA,
    )


def test_realized_current_war_is_reported_but_excluded_from_value() -> None:
    result = build_remaining_rights_inputs(_rows())
    current = result.timeline.filter(pl.col("season") == 2026)
    economics = result.economics_inputs.filter(pl.col("season") == 2026)
    assert current.item(0, "war_excluded_as_already_realized") == 4.0
    assert current.item(0, "war_entering_rights_value") == 0.5
    assert economics.item(0, "projected_war_mean") == 0.5
    assert economics.item(0, "known_salary_dollars") == 100_000
    assert economics.item(0, "control_status") == "current_season_committed"


def test_current_committed_state_has_no_midseason_non_tender_option() -> None:
    inputs = build_remaining_rights_inputs(_rows()).economics_inputs.filter(
        pl.col("season") == 2026
    )
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="test",
        market_model_id="test_market",
        arbitration_model_id="test_arb",
        dollars_per_war_by_year={2026: 10_000_000.0},
        arbitration_share_by_class={1: 0.3},
        annual_discount_rate=0.0,
    )
    valued = value_annual_contract_states(
        inputs, cba_ruleset=CBA_2022_2026, assumptions=assumptions
    ).annual
    assert valued.item(0, "decision_at_mean") == "current_season_committed"
    assert valued.item(0, "salary_cost_dollars") == 100_000


def test_current_realized_war_may_be_unavailable_without_entering_value() -> None:
    source = _rows().with_columns(
        pl.when(pl.col("season") == 2026)
        .then(pl.lit(None, dtype=pl.Float64))
        .otherwise(pl.col("realized_war_to_date"))
        .alias("realized_war_to_date")
    )
    result = build_remaining_rights_inputs(source)
    current = result.timeline.filter(pl.col("season") == 2026)
    economics = result.economics_inputs.filter(pl.col("season") == 2026)
    assert current.item(0, "war_excluded_as_already_realized") is None
    assert current.item(0, "timeline_status") == (
        "remaining_only_realized_war_unavailable"
    )
    assert economics.item(0, "projected_war_mean") == 0.5


def test_current_controlled_season_requires_remaining_salary() -> None:
    source = _rows().with_columns(
        pl.when(pl.col("season") == 2026)
        .then(pl.lit(None, dtype=pl.Int64))
        .otherwise(pl.col("salary_obligation_dollars"))
        .alias("salary_obligation_dollars")
    )
    with pytest.raises(ValueError, match="remaining salary"):
        build_remaining_rights_inputs(source)


def test_future_season_cannot_contain_realized_war() -> None:
    source = _rows().with_columns(
        pl.when(pl.col("season") == 2027)
        .then(pl.lit(1.0))
        .otherwise(pl.col("realized_war_to_date"))
        .alias("realized_war_to_date")
    )
    with pytest.raises(ValueError, match="cannot contain realized WAR"):
        build_remaining_rights_inputs(source)


def test_future_season_requires_explicit_zero_realized_war() -> None:
    source = _rows().with_columns(
        pl.when(pl.col("season") == 2027)
        .then(pl.lit(None, dtype=pl.Float64))
        .otherwise(pl.col("realized_war_to_date"))
        .alias("realized_war_to_date")
    )
    with pytest.raises(ValueError, match="cannot contain realized WAR"):
        build_remaining_rights_inputs(source)
