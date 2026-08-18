from math import isclose

import pytest

from universal_baseball.projection_composition import (
    PROJECTION_ILR_BASIS,
    PROJECTION_ILR_COORDINATE_COUNT,
    PROJECTION_ILR_CORE_BIN_ORDER,
    ilr_transform,
    inverse_ilr_transform,
    projection_ilr_to_profile,
    projection_profile_to_ilr,
    sequential_helmert_ilr_basis,
)


def test_projection_ilr_basis_is_zero_sum_and_orthonormal() -> None:
    basis = PROJECTION_ILR_BASIS
    row_count = len(basis)
    column_count = len(basis[0])
    assert row_count == len(PROJECTION_ILR_CORE_BIN_ORDER)
    assert column_count == PROJECTION_ILR_COORDINATE_COUNT

    for column in range(column_count):
        assert isclose(
            sum(basis[row][column] for row in range(row_count)),
            0.0,
            abs_tol=1e-12,
        )
        for other in range(column_count):
            dot = sum(
                basis[row][column] * basis[row][other]
                for row in range(row_count)
            )
            assert isclose(dot, 1.0 if column == other else 0.0, abs_tol=1e-12)


def test_ilr_uniform_composition_maps_to_zero() -> None:
    probabilities = [1.0 / 12.0] * 12
    coordinates = ilr_transform(probabilities)
    assert len(coordinates) == 11
    assert all(isclose(value, 0.0, abs_tol=1e-12) for value in coordinates)


def test_ilr_round_trip_recovers_probability_composition() -> None:
    probabilities = [
        0.09,
        0.21,
        0.03,
        0.07,
        0.08,
        0.04,
        0.06,
        0.05,
        0.07,
        0.10,
        0.08,
        0.12,
    ]
    assert isclose(sum(probabilities), 1.0, abs_tol=1e-12)
    rebuilt = inverse_ilr_transform(ilr_transform(probabilities))
    assert isclose(sum(rebuilt), 1.0, abs_tol=1e-12)
    for expected, actual in zip(probabilities, rebuilt, strict=True):
        assert isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-12)


def test_ilr_transform_is_scale_invariant() -> None:
    probabilities = [float(index + 1) for index in range(12)]
    scaled = [value * 37.0 for value in probabilities]
    first = ilr_transform(probabilities)
    second = ilr_transform(scaled)
    for left, right in zip(first, second, strict=True):
        assert isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def test_projection_profile_helpers_freeze_core_bin_order() -> None:
    raw = {core_bin: float(index + 1) for index, core_bin in enumerate(reversed(PROJECTION_ILR_CORE_BIN_ORDER))}
    coordinates = projection_profile_to_ilr(raw)
    rebuilt = projection_ilr_to_profile(coordinates)
    expected_total = sum(raw.values())
    assert tuple(rebuilt) == PROJECTION_ILR_CORE_BIN_ORDER
    for core_bin in PROJECTION_ILR_CORE_BIN_ORDER:
        assert isclose(
            rebuilt[core_bin],
            raw[core_bin] / expected_total,
            rel_tol=1e-12,
            abs_tol=1e-12,
        )


def test_projection_ilr_fails_closed_on_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        ilr_transform([0.5, 0.5, 0.0])
    with pytest.raises(ValueError, match="coordinate count mismatch"):
        projection_ilr_to_profile([0.0] * 10)
    incomplete = {
        core_bin: 1.0 for core_bin in PROJECTION_ILR_CORE_BIN_ORDER[:-1]
    }
    with pytest.raises(ValueError, match="core-bin mismatch"):
        projection_profile_to_ilr(incomplete)
    with pytest.raises(ValueError, match="at least two"):
        sequential_helmert_ilr_basis(1)
