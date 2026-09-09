from datetime import date

import polars as pl
import pytest

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
            "statutory_status": [
                "arbitration_eligible", "pre_arbitration", "pre_arbitration"
            ],
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


def test_attaches_exact_whole_player_uncertainty() -> None:
    hitters = pl.DataFrame(
        {"player_id": [1], "season": [2027], "expected_war": [1.5]}
    )
    pitchers = pl.DataFrame(
        {"player_id": [1], "season": [2027], "expected_war": [0.5]}
    )
    control = pl.DataFrame(
        {
            "as_of_date": [date(2026, 9, 8)], "player_id": [1],
            "organization_id": [100], "control_year": [2027],
            "service_days_before_year": [700],
            "statutory_status": ["arbitration_eligible"],
            "control_status": ["arbitration_eligible"],
            "projection_basis": ["full_service_future_scenario"],
        }
    )
    terms = pl.DataFrame(
        schema={
            "player_id": pl.Int64, "organization_id": pl.Int64,
            "payroll_year": pl.Int64, "amount_dollars": pl.Int64,
            "overlay_status": pl.String, "source_snapshot_id": pl.String,
        }
    )
    uncertainty = pl.DataFrame(
        {
            "player_id": [1], "season": [2027], "projected_war_mean": [2.0],
            "projected_war_lower": [-0.5], "projected_war_upper": [4.5],
        }
    )
    result = build_future_contract_economics_inputs(
        hitters, pitchers, control, terms, uncertainty
    )
    assert result.annual_inputs.item(0, "projected_war_lower") == -0.5
    assert result.annual_inputs.item(0, "projected_war_upper") == 4.5
    assert result.coverage["uncertainty_rows"] == 1


def test_attaches_only_resolved_option_buyout() -> None:
    hitters = pl.DataFrame(
        {"player_id": [1], "season": [2027], "expected_war": [1.5]}
    )
    pitchers = pl.DataFrame(
        schema={"player_id": pl.Int64, "season": pl.Int64, "expected_war": pl.Float64}
    )
    control = pl.DataFrame(
        {
            "as_of_date": [date(2026, 9, 8)], "player_id": [1],
            "organization_id": [100], "control_year": [2027],
            "service_days_before_year": [900], "control_status": ["club_option"],
            "statutory_status": ["free_agent_eligible"],
            "projection_basis": ["full_service_future_scenario"],
        }
    )
    terms = pl.DataFrame(
        {
            "player_id": [1], "organization_id": [100], "payroll_year": [2027],
            "amount_dollars": [10_000_000],
            "overlay_status": ["accepted_contract_overlay"],
            "source_snapshot_id": ["fg:test"],
        }
    )
    buyouts = pl.DataFrame(
        {
            "player_id": [1], "organization_id": [100], "season": [2027],
            "buyout_dollars": [2_000_000],
            "buyout_link_status": ["matched_exact_within_payroll"],
        }
    )
    result = build_future_contract_economics_inputs(
        hitters, pitchers, control, terms, option_buyouts=buyouts
    )
    assert result.annual_inputs.item(0, "buyout_dollars") == 2_000_000
    assert result.coverage["source_linked_buyout_rows"] == 1
    assert result.coverage["option_rows_with_buyout"] == 1
    assert result.coverage["option_rows_missing_buyout"] == 0


def test_secondary_term_fills_only_missing_nonconflicting_fact() -> None:
    hitters = pl.DataFrame(
        {"player_id": [1], "season": [2027], "expected_war": [1.5]}
    )
    pitchers = pl.DataFrame(
        schema={"player_id": pl.Int64, "season": pl.Int64, "expected_war": pl.Float64}
    )
    control = pl.DataFrame(
        {
            "as_of_date": [date(2026, 9, 8)], "player_id": [1],
            "organization_id": [100], "control_year": [2027],
            "service_days_before_year": [900], "control_status": ["club_option"],
            "statutory_status": ["free_agent_eligible"],
            "projection_basis": ["full_service_future_scenario"],
        }
    )
    terms = pl.DataFrame(
        {
            "player_id": [1], "organization_id": [100], "payroll_year": [2027],
            "amount_dollars": [10_000_000],
            "overlay_status": ["accepted_contract_overlay"],
            "source_snapshot_id": ["fg:test"],
        }
    )
    secondary = pl.DataFrame(
        {
            "player_id": [1], "player_name": ["One"],
            "organization_id": [100], "season": [2027],
            "expected_control_status": ["club_option"],
            "known_salary_dollars": [None], "buyout_dollars": [2_000_000],
            "source_url": ["https://example.test/options/2027"],
            "source_snapshot_id": ["secondary:test"],
        }
    )
    result = build_future_contract_economics_inputs(
        hitters,
        pitchers,
        control,
        terms,
        secondary_contract_terms=secondary,
    )
    assert result.annual_inputs.item(0, "buyout_dollars") == 2_000_000
    assert result.annual_inputs.item(0, "contract_source_id") == (
        "fg:test+secondary:test"
    )
    assert result.coverage["secondary_contract_term_rows"] == 1

    with pytest.raises(ValueError, match="status conflicts"):
        build_future_contract_economics_inputs(
            hitters,
            pitchers,
            control,
            terms,
            secondary_contract_terms=secondary.with_columns(
                pl.lit("player_option").alias("expected_control_status")
            ),
        )


def test_super_two_track_advances_through_four_arbitration_classes() -> None:
    hitters = pl.DataFrame(
        {
            "player_id": [1, 1, 1, 1],
            "season": [2027, 2028, 2029, 2030],
            "expected_war": [1.0] * 4,
        }
    )
    pitchers = pl.DataFrame(
        schema={"player_id": pl.Int64, "season": pl.Int64, "expected_war": pl.Float64}
    )
    control = pl.DataFrame(
        {
            "as_of_date": [date(2026, 9, 8)] * 4,
            "player_id": [1] * 4,
            "organization_id": [100] * 4,
            "control_year": [2027, 2028, 2029, 2030],
            "service_days_before_year": [2 * 172 + 100, 3 * 172, 4 * 172, 5 * 172],
            "statutory_status": [
                "super_two_eligible", "arbitration_eligible",
                "arbitration_eligible", "arbitration_eligible",
            ],
            "control_status": [
                "super_two_eligible", "arbitration_eligible",
                "arbitration_eligible", "arbitration_eligible",
            ],
            "projection_basis": ["full_service_future_scenario"] * 4,
        }
    )
    terms = pl.DataFrame(
        schema={
            "player_id": pl.Int64, "organization_id": pl.Int64,
            "payroll_year": pl.Int64, "amount_dollars": pl.Int64,
            "overlay_status": pl.String, "source_snapshot_id": pl.String,
        }
    )
    result = build_future_contract_economics_inputs(
        hitters, pitchers, control, terms
    )
    assert result.annual_inputs.get_column("arbitration_class").to_list() == [1, 2, 3, 4]
    assert result.coverage["projected_super_two_track_players"] == 1
