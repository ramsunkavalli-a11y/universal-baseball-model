from __future__ import annotations

import math

import pytest

from universal_baseball.player_value_mlb_centering import (
    CENTERING_ID,
    CENTERING_TOLERANCE_RUNS,
    MLBCenteringReference,
    ReferencePlayerComponents,
    build_fixed_mlb_centering_reference,
    calculate_mlb_centering_runs,
)


def _rows() -> list[ReferencePlayerComponents]:
    return [
        ReferencePlayerComponents(
            player_id=1,
            projected_expected_mlb_pa=500.0,
            batting_runs=10.0,
            baserunning_runs=2.0,
            defense_runs=-3.0,
            positional_runs=-5.0,
        ),
        ReferencePlayerComponents(
            player_id=2,
            projected_expected_mlb_pa=300.0,
            batting_runs=-4.0,
            baserunning_runs=1.0,
            defense_runs=2.0,
            positional_runs=-1.0,
        ),
    ]


def test_reference_uses_exactly_four_above_average_components() -> None:
    result = build_fixed_mlb_centering_reference(_rows())
    assert isinstance(result, MLBCenteringReference)
    assert result.centering_id == CENTERING_ID
    assert result.reference_season == 2024
    assert result.reference_player_count == 2
    assert result.aggregate_projected_mlb_pa == pytest.approx(800.0)
    assert result.aggregate_batting_runs == pytest.approx(6.0)
    assert result.aggregate_baserunning_runs == pytest.approx(3.0)
    assert result.aggregate_defense_runs == pytest.approx(-1.0)
    assert result.aggregate_positional_runs == pytest.approx(-6.0)
    assert result.aggregate_raw_above_average_runs == pytest.approx(2.0)
    assert result.centering_runs_per_pa == pytest.approx(-2.0 / 800.0)
    assert result.aggregate_centering_runs == pytest.approx(-2.0)
    assert abs(result.post_centering_residual_runs) <= CENTERING_TOLERANCE_RUNS


def test_application_scales_only_by_projected_pa() -> None:
    rate = -0.004
    assert calculate_mlb_centering_runs(
        600.0,
        centering_runs_per_pa=rate,
    ) == pytest.approx(-2.4)
    assert calculate_mlb_centering_runs(
        0.0,
        centering_runs_per_pa=rate,
    ) == 0.0


def test_zero_raw_reference_produces_zero_centering_rate() -> None:
    rows = [
        ReferencePlayerComponents(
            player_id=10,
            projected_expected_mlb_pa=600.0,
            batting_runs=5.0,
            baserunning_runs=-1.0,
            defense_runs=-2.0,
            positional_runs=-2.0,
        )
    ]
    result = build_fixed_mlb_centering_reference(rows)
    assert result.aggregate_raw_above_average_runs == pytest.approx(0.0)
    assert result.centering_runs_per_pa == pytest.approx(0.0)
    assert result.aggregate_centering_runs == pytest.approx(0.0)


def test_duplicate_reference_player_is_rejected() -> None:
    rows = _rows()
    rows.append(rows[0])
    with pytest.raises(ValueError, match="duplicate reference player_id"):
        build_fixed_mlb_centering_reference(rows)


def test_empty_or_zero_pa_reference_is_rejected() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        build_fixed_mlb_centering_reference([])

    rows = [
        ReferencePlayerComponents(
            player_id=1,
            projected_expected_mlb_pa=0.0,
            batting_runs=0.0,
            baserunning_runs=0.0,
            defense_runs=0.0,
            positional_runs=0.0,
        )
    ]
    with pytest.raises(ValueError, match="aggregate projected MLB PA must be positive"):
        build_fixed_mlb_centering_reference(rows)


@pytest.mark.parametrize("bad_pa", [-1.0, math.inf, -math.inf, math.nan, "nope"])
def test_invalid_reference_pa_is_rejected(bad_pa: object) -> None:
    rows = [
        ReferencePlayerComponents(
            player_id=1,
            projected_expected_mlb_pa=bad_pa,  # type: ignore[arg-type]
            batting_runs=0.0,
            baserunning_runs=0.0,
            defense_runs=0.0,
            positional_runs=0.0,
        )
    ]
    with pytest.raises(ValueError):
        build_fixed_mlb_centering_reference(rows)


@pytest.mark.parametrize("field", ["batting_runs", "baserunning_runs", "defense_runs", "positional_runs"])
def test_nonfinite_component_is_rejected(field: str) -> None:
    values = {
        "player_id": 1,
        "projected_expected_mlb_pa": 100.0,
        "batting_runs": 0.0,
        "baserunning_runs": 0.0,
        "defense_runs": 0.0,
        "positional_runs": 0.0,
    }
    values[field] = math.nan
    row = ReferencePlayerComponents(**values)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must be finite"):
        build_fixed_mlb_centering_reference([row])


@pytest.mark.parametrize("bad_pa", [-1.0, math.inf, math.nan])
def test_invalid_production_pa_is_rejected(bad_pa: float) -> None:
    with pytest.raises(ValueError):
        calculate_mlb_centering_runs(
            bad_pa,
            centering_runs_per_pa=0.0,
        )


def test_nonfinite_centering_rate_is_rejected() -> None:
    with pytest.raises(ValueError, match="centering_runs_per_pa must be finite"):
        calculate_mlb_centering_runs(
            600.0,
            centering_runs_per_pa=math.inf,
        )
