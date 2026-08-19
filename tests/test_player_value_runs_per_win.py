from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_runs_per_win import (
    RUNS_PER_WIN_CONVENTION_ID,
    calculate_v1_runs_per_win,
)


def test_four_point_five_runs_per_nine_maps_to_nine_point_seven_five_rpw() -> None:
    # 900 runs in 1800 innings = 4.5 runs per nine innings.
    result = calculate_v1_runs_per_win(900, 1800, reference_season=2024)
    assert result.convention_id == RUNS_PER_WIN_CONVENTION_ID
    assert result.mlb_runs_per_9_innings == pytest.approx(4.5)
    assert result.runs_per_win == pytest.approx(9.75)
    assert result.reference_season == 2024


def test_zero_runs_is_valid_with_positive_innings() -> None:
    result = calculate_v1_runs_per_win(0, 100)
    assert result.mlb_runs_per_9_innings == 0.0
    assert result.runs_per_win == pytest.approx(3.0)


@pytest.mark.parametrize("runs", [-1, math.inf, -math.inf, math.nan, "nope", None])
def test_invalid_runs_are_rejected(runs: object) -> None:
    with pytest.raises(ValueError):
        calculate_v1_runs_per_win(runs, 100)


@pytest.mark.parametrize("innings", [0, -1, math.inf, -math.inf, math.nan, "nope", None])
def test_invalid_innings_are_rejected(innings: object) -> None:
    with pytest.raises(ValueError):
        calculate_v1_runs_per_win(100, innings)


def test_invalid_reference_season_is_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_v1_runs_per_win(100, 100, reference_season=0)
