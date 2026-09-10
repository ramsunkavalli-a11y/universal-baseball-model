"""Chronology-safe validation for conditional prospect workload distributions."""

from __future__ import annotations

import math

import numpy as np
import polars as pl


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return a Wilson score interval for a binomial proportion."""

    if total < 1 or not 0 <= successes <= total or not math.isfinite(z) or z <= 0:
        raise ValueError("invalid Wilson interval inputs")
    rate = successes / total
    denominator = 1.0 + z * z / total
    center = (rate + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(rate * (1.0 - rate) / total + z * z / (4.0 * total * total)) / denominator
    return center - half, center + half


def build_workload_holdout_predictions(
    paths: pl.DataFrame,
    *,
    training_end_year: int = 2017,
    evaluation_start_year: int = 2018,
    minimum_role_players: int = 30,
) -> pl.DataFrame:
    """Score later debut cohorts from earlier conditional workload distributions."""

    required = {
        "player_id", "player_type", "debut_year", "outcome_tier_v2",
        "career_role", "adjusted_total_workload",
    }
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"workload paths missing fields: {missing}")
    if evaluation_start_year <= training_end_year or minimum_role_players < 1:
        raise ValueError("invalid chronology or minimum role count")
    training = paths.filter(pl.col("debut_year") <= training_end_year)
    evaluation = paths.filter(pl.col("debut_year") >= evaluation_start_year)
    if training.is_empty() or evaluation.is_empty():
        raise ValueError("training and evaluation cohorts must be nonempty")

    rows = []
    for row in evaluation.iter_rows(named=True):
        pooled = training.filter(
            (pl.col("player_type") == row["player_type"])
            & (pl.col("outcome_tier_v2") == row["outcome_tier_v2"])
        )
        role = pooled.filter(pl.col("career_role") == row["career_role"])
        selected = role if role.height >= minimum_role_players else pooled
        source = "role" if role.height >= minimum_role_players else "pooled"
        if selected.is_empty():
            raise ValueError(
                "missing training cell for "
                f"{row['player_type']}/{row['outcome_tier_v2']}/{row['career_role']}"
            )
        samples = selected.get_column("adjusted_total_workload").to_numpy()
        actual = float(row["adjusted_total_workload"])
        p10, p25, p50, p75, p90 = np.quantile(
            samples, [0.10, 0.25, 0.50, 0.75, 0.90], method="linear"
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "player_type": str(row["player_type"]),
                "debut_year": int(row["debut_year"]),
                "outcome_tier_v2": str(row["outcome_tier_v2"]),
                "career_role": str(row["career_role"]),
                "sample_source": source,
                "training_players": selected.height,
                "actual_workload": actual,
                "predicted_p10": float(p10),
                "predicted_p25": float(p25),
                "predicted_p50": float(p50),
                "predicted_p75": float(p75),
                "predicted_p90": float(p90),
                "covered_80": bool(p10 <= actual <= p90),
                "covered_50": bool(p25 <= actual <= p75),
                "absolute_median_error": abs(actual - float(p50)),
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def summarize_workload_coverage(
    predictions: pl.DataFrame,
    group_columns: list[str],
) -> pl.DataFrame:
    """Summarize empirical coverage and Wilson uncertainty by declared groups."""

    required = {
        *group_columns, "covered_80", "covered_50", "absolute_median_error"
    }
    if missing := sorted(required - set(predictions.columns)):
        raise ValueError(f"predictions missing fields: {missing}")
    rows = []
    for key, group in predictions.partition_by(group_columns, as_dict=True).items():
        keys = key if isinstance(key, tuple) else (key,)
        total = group.height
        hits80 = int(group["covered_80"].sum())
        hits50 = int(group["covered_50"].sum())
        low80, high80 = wilson_interval(hits80, total)
        low50, high50 = wilson_interval(hits50, total)
        row = dict(zip(group_columns, keys, strict=True))
        row.update(
            {
                "players": total,
                "coverage_80": hits80 / total,
                "coverage_80_wilson_low": low80,
                "coverage_80_wilson_high": high80,
                "target_80_inside_wilson": low80 <= 0.8 <= high80,
                "coverage_50": hits50 / total,
                "coverage_50_wilson_low": low50,
                "coverage_50_wilson_high": high50,
                "target_50_inside_wilson": low50 <= 0.5 <= high50,
                "median_absolute_error": float(
                    group["absolute_median_error"].median()
                ),
            }
        )
        rows.append(row)
    return pl.DataFrame(rows, infer_schema_length=None).sort(group_columns)
