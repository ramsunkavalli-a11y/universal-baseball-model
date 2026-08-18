"""Transparent next-season batting position/role transition smoothing.

This module implements the frozen development challenger in
``docs/position-role-transition-challenger-contract.md``. It has no
hyperparameter search and no source I/O.
"""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from universal_baseball.position_role_profile import BATTING_ROLE_POSITIONS


ROLE_VECTOR_LENGTH = len(BATTING_ROLE_POSITIONS)


def validate_role_vector(values: np.ndarray) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if vector.shape != (ROLE_VECTOR_LENGTH,):
        raise ValueError(
            f"role vector must have shape ({ROLE_VECTOR_LENGTH},), got {vector.shape}"
        )
    if not np.isfinite(vector).all():
        raise ValueError("role vector contains non-finite values")
    if (vector < -1e-12).any():
        raise ValueError("role vector contains negative probabilities")
    if abs(float(vector.sum()) - 1.0) > 1e-9:
        raise ValueError("role vector probabilities must sum to one")
    return np.clip(vector, 0.0, 1.0)


def fit_primary_destination_means(
    samples: dict[str, Iterable[np.ndarray]],
) -> tuple[dict[str, np.ndarray], dict[str, int]]:
    """Fit one mean next-season role vector per current primary position."""

    means: dict[str, np.ndarray] = {}
    counts: dict[str, int] = {}
    for position in BATTING_ROLE_POSITIONS:
        vectors = [validate_role_vector(value) for value in samples.get(position, [])]
        if not vectors:
            raise ValueError(
                f"training transitions contain no destination profiles for {position}"
            )
        matrix = np.vstack(vectors)
        mean = matrix.mean(axis=0)
        mean = mean / mean.sum()
        means[position] = validate_role_vector(mean)
        counts[position] = int(matrix.shape[0])
    extra = sorted(set(samples) - set(BATTING_ROLE_POSITIONS))
    if extra:
        raise ValueError(f"unexpected primary positions in training samples: {extra}")
    return means, counts


def transition_smoothed_prediction(
    current_profile: np.ndarray,
    *,
    primary_share: float,
    destination_mean: np.ndarray,
) -> np.ndarray:
    """Blend carry-forward with the frozen primary-position transition mean."""

    current = validate_role_vector(current_profile)
    destination = validate_role_vector(destination_mean)
    share = float(primary_share)
    if not np.isfinite(share) or not 0.0 <= share <= 1.0:
        raise ValueError(f"primary_share must be in [0, 1], got {primary_share!r}")
    prediction = share * current + (1.0 - share) * destination
    prediction = prediction / prediction.sum()
    return validate_role_vector(prediction)


def total_variation_distance(predicted: np.ndarray, observed: np.ndarray) -> float:
    predicted = validate_role_vector(predicted)
    observed = validate_role_vector(observed)
    return float(0.5 * np.abs(predicted - observed).sum())


def summed_squared_error(predicted: np.ndarray, observed: np.ndarray) -> float:
    predicted = validate_role_vector(predicted)
    observed = validate_role_vector(observed)
    return float(np.square(predicted - observed).sum())


def primary_position(values: np.ndarray) -> str:
    vector = validate_role_vector(values)
    return BATTING_ROLE_POSITIONS[int(np.argmax(vector))]
