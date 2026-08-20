from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_positional_adjustment import (
    BREF_FULL_SEASON_DEFENSIVE_OUTS,
    BREF_SENSITIVITY_SCHEDULE_ID,
    FULL_SEASON_DEFENSIVE_OUTS,
    SCHEDULE_ID,
    calculate_bref_positional_sensitivity,
    calculate_v1_positional_adjustment,
)


def test_full_season_shortstop_matches_frozen_schedule() -> None:
    result = calculate_v1_positional_adjustment(
        {"SS": FULL_SEASON_DEFENSIVE_OUTS},
        projected_dh_role_events=0,
    )
    assert result.schedule_id == SCHEDULE_ID
    assert result.runs_by_position["SS"] == pytest.approx(7.5)
    assert result.total_runs == pytest.approx(7.5)


def test_full_season_first_base_matches_frozen_schedule() -> None:
    result = calculate_v1_positional_adjustment(
        {"1B": FULL_SEASON_DEFENSIVE_OUTS},
        projected_dh_role_events=0,
    )
    assert result.runs_by_position["1B"] == pytest.approx(-12.5)
    assert result.total_runs == pytest.approx(-12.5)


def test_full_season_dh_matches_frozen_schedule() -> None:
    result = calculate_v1_positional_adjustment(
        {},
        projected_dh_role_events=162,
    )
    assert result.runs_by_position["DH"] == pytest.approx(-17.5)
    assert result.total_runs == pytest.approx(-17.5)


def test_baseball_reference_raw_schedule_sensitivity() -> None:
    result = calculate_bref_positional_sensitivity(
        {"C": BREF_FULL_SEASON_DEFENSIVE_OUTS},
        projected_dh_role_events=150,
    )
    assert result.schedule_id == BREF_SENSITIVITY_SCHEDULE_ID
    assert result.runs_by_position["C"] == pytest.approx(9.0)
    assert result.runs_by_position["DH"] == pytest.approx(-15.0)
    assert result.total_runs == pytest.approx(-6.0)


def test_multi_position_components_sum_without_renormalization() -> None:
    result = calculate_v1_positional_adjustment(
        {
            "SS": FULL_SEASON_DEFENSIVE_OUTS / 2,
            "1B": FULL_SEASON_DEFENSIVE_OUTS / 4,
        },
        projected_dh_role_events=40.5,
    )
    expected = (7.5 / 2) + (-12.5 / 4) + (-17.5 / 4)
    assert result.runs_by_position["SS"] == pytest.approx(3.75)
    assert result.runs_by_position["1B"] == pytest.approx(-3.125)
    assert result.runs_by_position["DH"] == pytest.approx(-4.375)
    assert result.total_runs == pytest.approx(expected)


def test_missing_positions_are_zero() -> None:
    result = calculate_v1_positional_adjustment({}, projected_dh_role_events=0)
    assert result.total_runs == 0.0
    assert all(value == 0.0 for value in result.runs_by_position.values())


@pytest.mark.parametrize("value", [-1, math.inf, -math.inf, math.nan, "nope"])
def test_invalid_dh_exposure_is_rejected(value: object) -> None:
    with pytest.raises(ValueError):
        calculate_v1_positional_adjustment({}, projected_dh_role_events=value)


def test_unknown_defensive_position_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported defensive position"):
        calculate_v1_positional_adjustment({"DH": 27}, projected_dh_role_events=0)


def test_negative_defensive_outs_are_rejected() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        calculate_v1_positional_adjustment({"CF": -1}, projected_dh_role_events=0)
