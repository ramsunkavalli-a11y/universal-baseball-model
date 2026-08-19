from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_replacement_level import (
    REPLACEMENT_LEVEL_CONVENTION_ID,
    REPLACEMENT_RUNS_PER_600_PA,
    calculate_v1_replacement_level,
)


def test_full_600_pa_matches_frozen_replacement_gap() -> None:
    result = calculate_v1_replacement_level(600)
    assert result.convention_id == REPLACEMENT_LEVEL_CONVENTION_ID
    assert result.replacement_runs_per_600_pa == pytest.approx(REPLACEMENT_RUNS_PER_600_PA)
    assert result.replacement_runs == pytest.approx(20.5)


def test_zero_projected_mlb_pa_produces_zero_replacement_runs() -> None:
    result = calculate_v1_replacement_level(0)
    assert result.replacement_runs == 0.0


def test_replacement_runs_scale_linearly_with_projected_mlb_pa() -> None:
    result = calculate_v1_replacement_level(300)
    assert result.replacement_runs == pytest.approx(10.25)


@pytest.mark.parametrize("value", [-1, math.inf, -math.inf, math.nan, "nope", None])
def test_invalid_projected_mlb_pa_is_rejected(value: object) -> None:
    with pytest.raises(ValueError, match="finite nonnegative"):
        calculate_v1_replacement_level(value)
