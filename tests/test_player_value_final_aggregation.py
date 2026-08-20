from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_final_aggregation import (
    FINAL_AGGREGATION_ID,
    calculate_final_player_value,
)


def test_final_additive_identity() -> None:
    result = calculate_final_player_value(
        batting_runs=10,
        baserunning_runs=2,
        defense_runs=3,
        positional_runs=-4,
        centering_runs=0.5,
        park_runs=0,
        replacement_runs=18.5,
        runs_per_win=10,
    )
    assert result.aggregation_id == FINAL_AGGREGATION_ID
    assert result.runs_above_replacement == pytest.approx(30)
    assert result.war == pytest.approx(3)


def test_zero_row_remains_zero() -> None:
    result = calculate_final_player_value(
        batting_runs=0,
        baserunning_runs=0,
        defense_runs=0,
        positional_runs=0,
        centering_runs=0,
        park_runs=0,
        replacement_runs=0,
        runs_per_win=9.682629939156854,
    )
    assert result.runs_above_replacement == 0
    assert result.war == 0


@pytest.mark.parametrize("rpw", [0, -1, math.inf, -math.inf, math.nan, "bad"])
def test_invalid_runs_per_win_is_rejected(rpw: object) -> None:
    with pytest.raises(ValueError):
        calculate_final_player_value(
            batting_runs=0,
            baserunning_runs=0,
            defense_runs=0,
            positional_runs=0,
            centering_runs=0,
            park_runs=0,
            replacement_runs=0,
            runs_per_win=rpw,
        )


@pytest.mark.parametrize("component", [math.inf, -math.inf, math.nan, "bad"])
def test_invalid_component_is_rejected(component: object) -> None:
    with pytest.raises(ValueError):
        calculate_final_player_value(
            batting_runs=component,
            baserunning_runs=0,
            defense_runs=0,
            positional_runs=0,
            centering_runs=0,
            park_runs=0,
            replacement_runs=0,
            runs_per_win=10,
        )

