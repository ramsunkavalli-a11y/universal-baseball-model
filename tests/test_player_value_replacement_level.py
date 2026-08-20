from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_replacement_level import (
    BREF_POSITION_PLAYER_WAR_ALLOCATION_SENSITIVITY,
    LEGACY_REPLACEMENT_RUNS_PER_600_PA,
    POSITION_PLAYER_WAR_ALLOCATION,
    REPLACEMENT_LEVEL_CONVENTION_ID,
    build_replacement_reference,
    build_v1_replacement_reference,
    calculate_v1_replacement_level,
)


MLB_GAMES_2024 = 2429
MLB_PA_2024 = 182449
RPW_2024 = 9.682629939156854


def test_2024_reference_matches_fangraphs_war_pool_formula() -> None:
    ref = build_v1_replacement_reference(
        MLB_GAMES_2024,
        MLB_PA_2024,
        RPW_2024,
        reference_season=2024,
    )
    expected_pool = POSITION_PLAYER_WAR_ALLOCATION * MLB_GAMES_2024 / 2430
    expected_per_pa = expected_pool * RPW_2024 / MLB_PA_2024
    assert ref.convention_id == REPLACEMENT_LEVEL_CONVENTION_ID
    assert ref.replacement_war_pool == pytest.approx(expected_pool)
    assert ref.replacement_runs_per_pa == pytest.approx(expected_per_pa)
    assert ref.replacement_runs_per_600_pa == pytest.approx(18.142586140136086)


def test_full_600_pa_uses_reference_rate() -> None:
    ref = build_v1_replacement_reference(
        MLB_GAMES_2024,
        MLB_PA_2024,
        RPW_2024,
        reference_season=2024,
    )
    result = calculate_v1_replacement_level(600, ref)
    assert result.replacement_runs == pytest.approx(ref.replacement_runs_per_600_pa)
    assert result.replacement_runs_per_600_pa == pytest.approx(ref.replacement_runs_per_600_pa)
    assert result.reference_season == 2024


def test_zero_projected_mlb_pa_produces_zero_replacement_runs() -> None:
    ref = build_v1_replacement_reference(
        MLB_GAMES_2024,
        MLB_PA_2024,
        RPW_2024,
        reference_season=2024,
    )
    result = calculate_v1_replacement_level(0, ref)
    assert result.replacement_runs == 0.0


def test_replacement_runs_scale_linearly_with_projected_mlb_pa() -> None:
    ref = build_v1_replacement_reference(
        MLB_GAMES_2024,
        MLB_PA_2024,
        RPW_2024,
        reference_season=2024,
    )
    full = calculate_v1_replacement_level(600, ref)
    half = calculate_v1_replacement_level(300, ref)
    assert half.replacement_runs == pytest.approx(full.replacement_runs / 2.0)


def test_590_war_sensitivity_is_higher_than_binding_rate() -> None:
    binding = build_v1_replacement_reference(
        MLB_GAMES_2024,
        MLB_PA_2024,
        RPW_2024,
        reference_season=2024,
    )
    sensitivity = build_replacement_reference(
        MLB_GAMES_2024,
        MLB_PA_2024,
        RPW_2024,
        reference_season=2024,
        position_player_war_allocation=BREF_POSITION_PLAYER_WAR_ALLOCATION_SENSITIVITY,
        convention_id="baseball_reference_590_war_pool_sensitivity",
    )
    assert sensitivity.replacement_runs_per_600_pa == pytest.approx(18.779168109965422)
    assert sensitivity.replacement_runs_per_600_pa > binding.replacement_runs_per_600_pa
    assert LEGACY_REPLACEMENT_RUNS_PER_600_PA == 20.5


@pytest.mark.parametrize("value", [-1, math.inf, -math.inf, math.nan, "nope", None])
def test_invalid_projected_mlb_pa_is_rejected(value: object) -> None:
    ref = build_v1_replacement_reference(
        MLB_GAMES_2024,
        MLB_PA_2024,
        RPW_2024,
        reference_season=2024,
    )
    with pytest.raises(ValueError):
        calculate_v1_replacement_level(value, ref)


@pytest.mark.parametrize(
    "games, pa, rpw",
    [
        (0, MLB_PA_2024, RPW_2024),
        (2431, MLB_PA_2024, RPW_2024),
        (MLB_GAMES_2024, 0, RPW_2024),
        (MLB_GAMES_2024, MLB_PA_2024, 0),
        (math.nan, MLB_PA_2024, RPW_2024),
    ],
)
def test_invalid_reference_environment_is_rejected(games: object, pa: object, rpw: object) -> None:
    with pytest.raises(ValueError):
        build_v1_replacement_reference(games, pa, rpw, reference_season=2024)
