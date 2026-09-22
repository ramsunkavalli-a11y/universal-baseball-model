"""Comparable indexes and diagnostics for external park-factor audits.

External systems do not need to agree with UBM.  These helpers put factors on
roughly comparable scales, then measure direction and rank separately from
absolute magnitude so shrinkage is not mistaken for a scientific failure.
"""

from __future__ import annotations

import math

import numpy as np
import polars as pl


def unhalve_full_park_index(value: float) -> float:
    """Undo a published half-season adjustment around the neutral index 100."""

    if not math.isfinite(value):
        raise ValueError("park index must be finite")
    return 100.0 + 2.0 * (float(value) - 100.0)


def component_probability_indexes(
    factors: pl.DataFrame,
    *,
    reference_probabilities: dict[str, float],
    outcome_weights: dict[str, float] | None = None,
) -> pl.DataFrame:
    """Convert CLR effects to full in-park probability indexes.

    A CLR coefficient is not itself a home/road rate ratio.  The conversion
    composes every outcome effect with one common reference distribution and
    renormalizes the probability vector.  This produces indexes comparable to
    published component rates while preserving UBM's exhaustive accounting.
    """

    required = {"venue_id", "component", "park_clr_effect"}
    missing = sorted(required - set(factors.columns))
    if missing:
        raise ValueError(f"UBM factors missing fields: {missing}")
    components = tuple(reference_probabilities)
    if set(factors["component"].unique().to_list()) != set(components):
        raise ValueError("factor components do not match reference probabilities")
    probability = np.asarray([reference_probabilities[value] for value in components])
    if np.any(~np.isfinite(probability)) or np.any(probability <= 0):
        raise ValueError("reference probabilities must be positive and finite")
    probability = probability / probability.sum()
    weights = None
    baseline_score = None
    if outcome_weights is not None:
        if set(outcome_weights) != set(components):
            raise ValueError("outcome weights do not match reference probabilities")
        weights = np.asarray([outcome_weights[value] for value in components])
        baseline_score = float(np.dot(probability, weights))
        if not math.isfinite(baseline_score) or baseline_score <= 0:
            raise ValueError("weighted reference score must be positive")

    lookup = {
        (int(row["venue_id"]), str(row["component"])): float(
            row["park_clr_effect"]
        )
        for row in factors.iter_rows(named=True)
    }
    rows: list[dict[str, float | int]] = []
    for venue_id in sorted(factors["venue_id"].unique().to_list()):
        effect = np.asarray(
            [lookup[(int(venue_id), component)] for component in components]
        )
        adjusted = probability * np.exp(effect - np.max(effect))
        adjusted = adjusted / adjusted.sum()
        row: dict[str, float | int] = {"venue_id": int(venue_id)}
        for index, component in enumerate(components):
            row[f"ubm_{component}_index"] = float(
                100.0 * adjusted[index] / probability[index]
            )
        if weights is not None and baseline_score is not None:
            row["ubm_weighted_index"] = float(
                100.0 * np.dot(adjusted, weights) / baseline_score
            )
        rows.append(row)
    return pl.DataFrame(rows).sort("venue_id")


def compare_park_indexes(
    overlap: pl.DataFrame,
    *,
    ubm_column: str,
    external_column: str,
) -> dict[str, float | int | None]:
    """Measure overlap, direction, scale, and rank agreement."""

    required = {ubm_column, external_column}
    missing = sorted(required - set(overlap.columns))
    if missing:
        raise ValueError(f"park comparison missing fields: {missing}")
    paired = overlap.select(ubm_column, external_column).drop_nulls()
    if paired.is_empty():
        return {
            "parks": 0,
            "pearson": None,
            "spearman": None,
            "sign_agreement": None,
            "mean_absolute_index_gap": None,
        }
    ubm = paired[ubm_column].to_numpy().astype(float)
    external = paired[external_column].to_numpy().astype(float)
    if not np.all(np.isfinite(ubm)) or not np.all(np.isfinite(external)):
        raise ValueError("park comparison indexes must be finite")

    def correlation(left: np.ndarray, right: np.ndarray) -> float | None:
        if len(left) < 2 or np.std(left) == 0 or np.std(right) == 0:
            return None
        return float(np.corrcoef(left, right)[0, 1])

    ubm_rank = pl.Series(ubm).rank(method="average").to_numpy()
    external_rank = pl.Series(external).rank(method="average").to_numpy()
    directional = (ubm != 100.0) & (external != 100.0)
    sign_agreement = (
        float(np.mean(np.sign(ubm[directional] - 100.0) == np.sign(
            external[directional] - 100.0
        )))
        if np.any(directional)
        else None
    )
    return {
        "parks": int(len(ubm)),
        "pearson": correlation(ubm, external),
        "spearman": correlation(ubm_rank, external_rank),
        "sign_agreement": sign_agreement,
        "mean_absolute_index_gap": float(np.mean(np.abs(ubm - external))),
        "ubm_standard_deviation": float(np.std(ubm)),
        "external_standard_deviation": float(np.std(external)),
    }
