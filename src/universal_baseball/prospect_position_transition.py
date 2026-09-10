"""Chronology-safe minor-to-MLB hitter position-transition primitives."""

from __future__ import annotations

import numpy as np


POSITION_GROUPS = ("C", "MIDDLE_INFIELD", "CORNER", "OUTFIELD", "OTHER")
POSITION_TO_GROUP = {
    "C": "C",
    "2B": "MIDDLE_INFIELD",
    "SS": "MIDDLE_INFIELD",
    "1B": "CORNER",
    "3B": "CORNER",
    "LF": "OUTFIELD",
    "CF": "OUTFIELD",
    "RF": "OUTFIELD",
    "OF": "OUTFIELD",
    "DH": "OTHER",
}


def position_group(position: object) -> str | None:
    """Collapse an official batting position to the frozen five-group outcome."""

    return POSITION_TO_GROUP.get(str(position or "").upper())


def fit_transition_probabilities(
    origins: list[str], destinations: list[str], *, prior_weight: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fit marginal and origin-conditional probabilities with fixed shrinkage."""

    if len(origins) != len(destinations) or not origins:
        raise ValueError("origins and destinations must be equal nonempty lists")
    if prior_weight <= 0:
        raise ValueError("prior_weight must be positive")
    index = {value: offset for offset, value in enumerate(POSITION_GROUPS)}
    if set(origins) - set(index) or set(destinations) - set(index):
        raise ValueError("unsupported position group")
    counts = np.zeros((len(index), len(index)), dtype=float)
    for origin, destination in zip(origins, destinations, strict=True):
        counts[index[origin], index[destination]] += 1.0
    destination_counts = counts.sum(axis=0)
    marginal = (destination_counts + 0.5) / (
        destination_counts.sum() + 0.5 * len(index)
    )
    transition = (
        counts + prior_weight * marginal.reshape(1, -1)
    ) / (counts.sum(axis=1, keepdims=True) + prior_weight)
    return marginal, transition, counts


def predict_transition(
    origins: list[str], *, marginal: np.ndarray, transition: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Return marginal-baseline and origin-conditional probabilities."""

    index = {value: offset for offset, value in enumerate(POSITION_GROUPS)}
    if set(origins) - set(index):
        raise ValueError("unsupported position group")
    marginal = np.asarray(marginal, dtype=float)
    transition = np.asarray(transition, dtype=float)
    expected = (len(index),)
    if marginal.shape != expected or transition.shape != (len(index), len(index)):
        raise ValueError("position probability shape mismatch")
    baseline = np.tile(marginal, (len(origins), 1))
    candidate = np.vstack([transition[index[origin]] for origin in origins])
    return baseline, candidate


def multiclass_scores(
    destinations: list[str], probabilities: np.ndarray
) -> dict[str, float | int]:
    """Return multiclass proper scores and exact destination accuracy."""

    index = {value: offset for offset, value in enumerate(POSITION_GROUPS)}
    probability = np.asarray(probabilities, dtype=float)
    if probability.shape != (len(destinations), len(index)):
        raise ValueError("probabilities do not match destinations")
    if not np.isfinite(probability).all() or (probability < 0).any():
        raise ValueError("probabilities must be finite and nonnegative")
    if not np.allclose(probability.sum(axis=1), 1.0):
        raise ValueError("each probability row must sum to one")
    observed = np.asarray([index[value] for value in destinations], dtype=int)
    one_hot = np.eye(len(index))[observed]
    chosen = np.clip(probability[np.arange(len(observed)), observed], 1e-12, 1.0)
    return {
        "players": len(destinations),
        "log_loss": float(-np.log(chosen).mean()),
        "brier": float(np.square(probability - one_hot).sum(axis=1).mean()),
        "accuracy": float((probability.argmax(axis=1) == observed).mean()),
    }
