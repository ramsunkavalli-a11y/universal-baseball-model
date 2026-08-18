"""Deterministic compositional primitives for batting Projection v1.

Projection v1 models one-year change in the frozen 12-component Current Talent
profile. Probabilities live on a simplex, so the Projection adjustment is fit in
a fixed 11-dimensional isometric log-ratio (ILR) coordinate system and mapped
back to a valid probability composition.

This module contains only deterministic geometry. It does not fit an age curve,
choose a model, score future outcomes, infer opportunity, or access 2025 data.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import exp, isfinite, log, sqrt

from universal_baseball.performance_season import ALL_CORE_BINS


PROJECTION_ILR_CORE_BIN_ORDER = tuple(ALL_CORE_BINS)
PROJECTION_ILR_PART_COUNT = len(PROJECTION_ILR_CORE_BIN_ORDER)
PROJECTION_ILR_COORDINATE_COUNT = PROJECTION_ILR_PART_COUNT - 1
PROJECTION_ILR_METHOD = "sequential_helmert_ilr_v1"


def sequential_helmert_ilr_basis(part_count: int) -> tuple[tuple[float, ...], ...]:
    """Return a deterministic ``part_count x (part_count - 1)`` ILR basis.

    Column ``j`` (zero based) contrasts the first ``j + 1`` parts with part
    ``j + 2``. The columns are orthonormal and each sums to zero, so they form an
    orthonormal basis for the CLR subspace.
    """

    if part_count < 2:
        raise ValueError("ILR requires at least two composition parts")

    rows: list[list[float]] = [
        [0.0 for _ in range(part_count - 1)] for _ in range(part_count)
    ]
    for column in range(part_count - 1):
        left_count = column + 1
        denominator = sqrt(float(left_count * (left_count + 1)))
        positive = 1.0 / denominator
        negative = -float(left_count) / denominator
        for row in range(left_count):
            rows[row][column] = positive
        rows[left_count][column] = negative
    return tuple(tuple(value for value in row) for row in rows)


PROJECTION_ILR_BASIS = sequential_helmert_ilr_basis(PROJECTION_ILR_PART_COUNT)


def _validate_probability_composition(probabilities: Sequence[float]) -> tuple[float, ...]:
    values = tuple(float(value) for value in probabilities)
    if len(values) < 2:
        raise ValueError("ILR probability composition requires at least two parts")
    if any(not isfinite(value) for value in values):
        raise ValueError("ILR probability composition contains non-finite values")
    if any(value <= 0.0 for value in values):
        raise ValueError("ILR probability composition must be strictly positive")
    total = sum(values)
    if not isfinite(total) or total <= 0.0:
        raise ValueError("ILR probability composition has invalid total")
    # Normalize instead of requiring an exact sum of one. The ILR transform is
    # scale-invariant, and explicit normalization makes the inverse contract
    # deterministic for harmless floating-point drift in probability sums.
    return tuple(value / total for value in values)


def ilr_transform(
    probabilities: Sequence[float],
    *,
    basis: Sequence[Sequence[float]] | None = None,
) -> tuple[float, ...]:
    """Map a strictly-positive composition to orthonormal ILR coordinates."""

    values = _validate_probability_composition(probabilities)
    part_count = len(values)
    matrix = (
        sequential_helmert_ilr_basis(part_count)
        if basis is None
        else tuple(tuple(float(value) for value in row) for row in basis)
    )
    if len(matrix) != part_count:
        raise ValueError("ILR basis row count must equal composition part count")
    coordinate_count = part_count - 1
    if any(len(row) != coordinate_count for row in matrix):
        raise ValueError("ILR basis must have part_count - 1 columns")

    logs = tuple(log(value) for value in values)
    return tuple(
        sum(matrix[row][column] * logs[row] for row in range(part_count))
        for column in range(coordinate_count)
    )


def inverse_ilr_transform(
    coordinates: Sequence[float],
    *,
    basis: Sequence[Sequence[float]] | None = None,
) -> tuple[float, ...]:
    """Map ILR coordinates back to a strictly-positive unit-sum composition."""

    values = tuple(float(value) for value in coordinates)
    if not values:
        raise ValueError("inverse ILR requires at least one coordinate")
    if any(not isfinite(value) for value in values):
        raise ValueError("inverse ILR coordinates contain non-finite values")

    part_count = len(values) + 1
    matrix = (
        sequential_helmert_ilr_basis(part_count)
        if basis is None
        else tuple(tuple(float(value) for value in row) for row in basis)
    )
    if len(matrix) != part_count:
        raise ValueError("ILR basis row count must equal coordinate count + 1")
    if any(len(row) != len(values) for row in matrix):
        raise ValueError("ILR basis column count must equal coordinate count")

    clr = tuple(
        sum(matrix[row][column] * values[column] for column in range(len(values)))
        for row in range(part_count)
    )
    maximum = max(clr)
    numerators = tuple(exp(value - maximum) for value in clr)
    denominator = sum(numerators)
    if not isfinite(denominator) or denominator <= 0.0:
        raise ValueError("inverse ILR softmax denominator is invalid")
    return tuple(value / denominator for value in numerators)


def projection_profile_to_ilr(probabilities_by_bin: Mapping[str, float]) -> tuple[float, ...]:
    """Transform one canonical 12-bin batting profile to Projection ILR space."""

    observed = set(str(key) for key in probabilities_by_bin)
    expected = set(PROJECTION_ILR_CORE_BIN_ORDER)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    if missing or extra:
        raise ValueError(
            f"Projection profile core-bin mismatch: missing={missing}, extra={extra}"
        )
    return ilr_transform(
        [float(probabilities_by_bin[core_bin]) for core_bin in PROJECTION_ILR_CORE_BIN_ORDER],
        basis=PROJECTION_ILR_BASIS,
    )


def projection_ilr_to_profile(coordinates: Sequence[float]) -> dict[str, float]:
    """Invert Projection ILR coordinates to the canonical 12-bin profile."""

    values = tuple(float(value) for value in coordinates)
    if len(values) != PROJECTION_ILR_COORDINATE_COUNT:
        raise ValueError(
            "Projection ILR coordinate count mismatch: "
            f"observed={len(values)}, expected={PROJECTION_ILR_COORDINATE_COUNT}"
        )
    probabilities = inverse_ilr_transform(values, basis=PROJECTION_ILR_BASIS)
    return dict(zip(PROJECTION_ILR_CORE_BIN_ORDER, probabilities, strict=True))
