"""Transparent historical comparable outcomes for pre-MLB hitters."""

from __future__ import annotations

import numpy as np
import polars as pl


RATE_COLUMNS = tuple(f"production_rate_{index}" for index in range(1, 5))
FEATURE_COLUMNS = ("age_years", "log_workload", *RATE_COLUMNS)
RATE_REGRESSION_PA = 200.0
DEFAULT_COMPARABLES = 150


def _prepared(reference: pl.DataFrame, frame: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    workload = reference["current_milb_workload"].to_numpy().astype(float)
    total = max(float(workload.sum()), 1.0)
    priors = np.asarray([
        float((reference[column] * reference["current_milb_workload"]).sum()) / total
        for column in RATE_COLUMNS
    ])

    def matrix(source: pl.DataFrame) -> np.ndarray:
        exposure = source["current_milb_workload"].to_numpy().astype(float)
        rates = source.select(RATE_COLUMNS).to_numpy().astype(float)
        regressed = (
            rates * exposure[:, None] + priors * RATE_REGRESSION_PA
        ) / (exposure[:, None] + RATE_REGRESSION_PA)
        return np.column_stack((
            source["age_years"].to_numpy().astype(float),
            np.log1p(exposure),
            regressed,
        ))

    reference_matrix = matrix(reference)
    target_matrix = matrix(frame)
    center = np.nanmedian(reference_matrix, axis=0)
    scale = np.nanstd(reference_matrix, axis=0)
    scale[scale < 1e-9] = 1.0
    reference_matrix = np.nan_to_num((reference_matrix - center) / scale)
    target_matrix = np.nan_to_num((target_matrix - center) / scale)
    return reference_matrix, target_matrix


def score_hitter_comparables(
    reference: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    comparable_count: int = DEFAULT_COMPARABLES,
) -> pl.DataFrame:
    """Score every target from the same procedure and all-player outcomes.

    Comparisons stay within primary level. Rates are regressed before distance is
    measured. Every reference player remains in the outcome distribution, including
    players with zero later MLB opportunities.
    """

    required = {
        "player_id", "age_years", "primary_level_tier", "current_milb_workload",
        *RATE_COLUMNS,
    }
    outcome_columns = {"later_component_war", "later_mlb_workload"}
    if missing := sorted((required | outcome_columns) - set(reference.columns)):
        raise ValueError(f"reference missing comparable fields: {missing}")
    if missing := sorted(required - set(targets.columns)):
        raise ValueError(f"targets missing comparable fields: {missing}")
    if comparable_count < 25:
        raise ValueError("comparable_count must be at least 25")

    rows: list[dict[str, float | int | str]] = []
    for level in targets["primary_level_tier"].unique().to_list():
        target_group = targets.filter(pl.col("primary_level_tier") == level)
        reference_group = reference.filter(pl.col("primary_level_tier") == level)
        if reference_group.height < 25:
            reference_group = reference
        reference_matrix, target_matrix = _prepared(reference_group, target_group)
        outcome = reference_group["later_component_war"].to_numpy().astype(float)
        workload = reference_group["later_mlb_workload"].to_numpy().astype(float)
        k = min(comparable_count, reference_group.height)
        for index, target in enumerate(target_group.iter_rows(named=True)):
            distance = np.sum((reference_matrix - target_matrix[index]) ** 2, axis=1)
            neighbor_index = np.argpartition(distance, k - 1)[:k]
            neighbor_outcome = outcome[neighbor_index]
            neighbor_workload = workload[neighbor_index]
            rows.append({
                "player_id": int(target["player_id"]),
                "historical_comparable_level": str(level),
                "historical_comparable_players": int(k),
                "historical_arrival_rate_4y": float((neighbor_workload > 0).mean()),
                "historical_component_war_4y": float(neighbor_outcome.mean()),
                "historical_positive_component_war_4y": float(
                    np.maximum(neighbor_outcome, 0.0).mean()
                ),
                "historical_impact_rate_4y": float((neighbor_outcome >= 1.0).mean()),
            })
    return pl.DataFrame(rows).sort("player_id")
