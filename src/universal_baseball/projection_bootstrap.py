"""Paired player-cluster bootstrap for probability projection comparisons."""

from __future__ import annotations

import numpy as np


def paired_player_cluster_bootstrap(
    *,
    player_ids: np.ndarray,
    actual: np.ndarray,
    baseline: np.ndarray,
    candidate: np.ndarray,
    weights: np.ndarray,
    repetitions: int = 5000,
    seed: int = 1729,
) -> dict[str, dict[str, float]]:
    """Bootstrap entire player histories and return candidate-minus-base intervals."""

    if repetitions < 100:
        raise ValueError("bootstrap requires at least 100 repetitions")
    if actual.shape != baseline.shape or actual.shape != candidate.shape:
        raise ValueError("actual and prediction matrices must have the same shape")
    if actual.ndim != 2 or len(player_ids) != actual.shape[0]:
        raise ValueError("player IDs must align with two-dimensional predictions")
    if len(weights) != actual.shape[0] or np.any(weights <= 0):
        raise ValueError("positive weights must align with predictions")

    baseline = np.clip(baseline, 1e-12, 1.0)
    candidate = np.clip(candidate, 1e-12, 1.0)
    _, cluster = np.unique(player_ids, return_inverse=True)
    cluster_count = int(cluster.max()) + 1
    cell_count = np.bincount(
        cluster, weights=np.full(len(cluster), actual.shape[1], dtype=float)
    )
    weight_sum = np.bincount(cluster, weights=weights)
    aggregates = {
        "rate_rmse": (
            np.bincount(cluster, weights=np.sum((baseline - actual) ** 2, axis=1)),
            np.bincount(cluster, weights=np.sum((candidate - actual) ** 2, axis=1)),
            cell_count,
        ),
        "multinomial_log_loss": (
            np.bincount(
                cluster,
                weights=-weights * np.sum(actual * np.log(baseline), axis=1),
            ),
            np.bincount(
                cluster,
                weights=-weights * np.sum(actual * np.log(candidate), axis=1),
            ),
            weight_sum,
        ),
        "multinomial_brier": (
            np.bincount(
                cluster,
                weights=weights * np.sum((baseline - actual) ** 2, axis=1),
            ),
            np.bincount(
                cluster,
                weights=weights * np.sum((candidate - actual) ** 2, axis=1),
            ),
            weight_sum,
        ),
    }
    samples = {name: [] for name in aggregates}
    rng = np.random.default_rng(seed)
    remaining = repetitions
    while remaining:
        batch = min(250, remaining)
        selected = rng.integers(0, cluster_count, size=(batch, cluster_count))
        for name, (base_sum, candidate_sum, denominator) in aggregates.items():
            den = denominator[selected].sum(axis=1)
            base_value = base_sum[selected].sum(axis=1) / den
            candidate_value = candidate_sum[selected].sum(axis=1) / den
            if name == "rate_rmse":
                base_value = np.sqrt(base_value)
                candidate_value = np.sqrt(candidate_value)
            samples[name].append(candidate_value - base_value)
        remaining -= batch

    result = {}
    for name, chunks in samples.items():
        values = np.concatenate(chunks)
        result[name] = {
            "lower_95": float(np.quantile(values, 0.025)),
            "median": float(np.quantile(values, 0.5)),
            "upper_95": float(np.quantile(values, 0.975)),
            "probability_candidate_better": float(np.mean(values < 0)),
        }
    return result
