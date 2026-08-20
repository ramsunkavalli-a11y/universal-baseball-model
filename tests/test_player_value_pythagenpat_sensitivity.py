from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_pythagenpat_sensitivity import (
    PYTHAGENPAT_SENSITIVITY_ID,
    calculate_position_player_pythagenpat_sensitivity,
    pythagenpat_win_percentage,
)


def test_equal_run_rates_are_average() -> None:
    assert pythagenpat_win_percentage(4.5, 4.5) == pytest.approx(0.5)


def test_better_run_differential_increases_win_percentage() -> None:
    assert pythagenpat_win_percentage(5.0, 4.0) > 0.5
    assert pythagenpat_win_percentage(4.0, 5.0) < 0.5


@pytest.mark.parametrize("value", [0, -1, math.inf, -math.inf, math.nan, "bad"])
def test_invalid_pythagenpat_rates_are_rejected(value: object) -> None:
    with pytest.raises(ValueError):
        pythagenpat_win_percentage(value, 4.5)


def test_position_player_comparison_uses_both_sides_and_replacement() -> None:
    result = calculate_position_player_pythagenpat_sensitivity(
        projected_pa=600,
        projected_defensive_outs=3600,
        batting_runs=15,
        baserunning_runs=2,
        defense_runs=8,
        positional_runs=-3,
        centering_runs=1,
        replacement_runs_per_pa=0.03,
        league_team_runs_per_game=4.4,
    )
    assert result.sensitivity_id == PYTHAGENPAT_SENSITIVITY_ID
    assert result.estimated_innings == pytest.approx(1260)
    assert result.estimated_games == pytest.approx(140)
    assert result.offensive_runs == pytest.approx(15)
    assert result.fielding_runs == pytest.approx(8)
    assert result.replacement_runs == pytest.approx(18)
    assert result.player_runs_scored_per_game == pytest.approx(4.4 + 15 / 140)
    assert result.player_runs_allowed_per_game == pytest.approx(4.4 - 8 / 140)
    assert result.wins_above_average > 0
    assert result.replacement_wins > 0
    assert result.war == pytest.approx(result.wins_above_average + result.replacement_wins)


def test_available_defensive_innings_can_set_larger_estimate() -> None:
    result = calculate_position_player_pythagenpat_sensitivity(
        projected_pa=100,
        projected_defensive_outs=900,
        batting_runs=0,
        baserunning_runs=0,
        defense_runs=0,
        positional_runs=0,
        centering_runs=0,
        replacement_runs_per_pa=0,
        league_team_runs_per_game=4.4,
    )
    assert result.estimated_innings == pytest.approx(300)
    assert result.estimated_games == pytest.approx(300 / 9)
    assert result.war == pytest.approx(0)


def test_zero_exposure_row_is_explicit_zero() -> None:
    result = calculate_position_player_pythagenpat_sensitivity(
        projected_pa=0,
        projected_defensive_outs=0,
        batting_runs=0,
        baserunning_runs=0,
        defense_runs=0,
        positional_runs=0,
        centering_runs=0,
        replacement_runs_per_pa=0.03,
        league_team_runs_per_game=4.4,
    )
    assert result.estimated_games == 0
    assert result.player_win_percentage == 0.5
    assert result.war == 0


def test_zero_pa_with_nonzero_component_fails_closed() -> None:
    with pytest.raises(ValueError, match="zero-PA"):
        calculate_position_player_pythagenpat_sensitivity(
            projected_pa=0,
            projected_defensive_outs=0,
            batting_runs=1,
            baserunning_runs=0,
            defense_runs=0,
            positional_runs=0,
            centering_runs=0,
            replacement_runs_per_pa=0.03,
            league_team_runs_per_game=4.4,
        )

