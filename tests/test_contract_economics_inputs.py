from datetime import date

import polars as pl

from universal_baseball.contract_economics_inputs import (
    build_future_contract_economics_inputs,
)


def test_builds_whole_player_economics_inputs_and_sums_two_way_war() -> None:
    hitters = pl.DataFrame(
        {"player_id": [1, 2], "season": [2027, 2027], "expected_war": [1.5, 0.2]}
    )
    pitchers = pl.DataFrame(
        {"player_id": [1, 3], "season": [2027, 2027], "expected_war": [0.5, 0.8]}
    )
    control = pl.DataFrame(
        {
            "as_of_date": [date(2026, 9, 8)] * 3,
            "player_id": [1, 2, 4],
            "organization_id": [100, 100, 101],
            "control_year": [2027, 2027, 2027],
            "service_days_before_year": [700, 100, 50],
            "control_status": ["arbitration_eligible", "pre_arbitration", "pre_arbitration"],
            "projection_basis": ["full_service_future_scenario"] * 3,
        }
    )
    terms = pl.DataFrame(
        {
            "player_id": [1],
            "organization_id": [100],
            "payroll_year": [2027],
            "amount_dollars": [5_000_000],
            "overlay_status": ["accepted_contract_overlay"],
            "source_snapshot_id": ["fg:test"],
        }
    )
    result = build_future_contract_economics_inputs(hitters, pitchers, control, terms)
    assert result.annual_inputs.height == 2
    player_one = result.annual_inputs.filter(pl.col("player_id") == 1)
    assert player_one.item(0, "projected_war_mean") == 2.0
    assert player_one.item(0, "arbitration_class") == 2
    assert player_one.item(0, "known_salary_dollars") == 5_000_000
    assert result.coverage["projection_rows_without_control"] == 1
    assert result.coverage["control_rows_without_projection"] == 1
