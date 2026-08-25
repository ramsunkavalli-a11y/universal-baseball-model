"""Frozen disclosed-comparison helpers for Stage 2f H0."""

from __future__ import annotations

from collections.abc import Mapping

import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2f import (
    normalize_level,
    probabilities_from_links,
    probability_links,
)


PRIMARY_METRICS = (
    "terminal_log_loss",
    "terminal_brier_score",
    "woba_rmse",
    "runs_per_600_rmse",
)
CORRELATION_METRICS = (
    "woba_pearson",
    "woba_spearman",
    "runs_per_600_pearson",
    "runs_per_600_spearman",
)
STRICT_TOLERANCE = 1e-8


def translate_target_to_reference(
    target: pl.DataFrame,
    translation_offsets: pl.DataFrame | None,
) -> pl.DataFrame:
    """Translate disclosed outcomes with the fold's already-frozen ALL surface."""

    required = {"player_id", "hitter_talent_pa", *HITTER_TALENT_OUTCOMES}
    if missing := sorted(required - set(target.columns)):
        raise ValueError(f"reference target is missing columns: {missing}")
    level_column = (
        "primary_target_level_group"
        if "primary_target_level_group" in target.columns
        else "level_group"
    )
    if level_column not in target.columns:
        raise ValueError("reference target is missing its observed level")
    if translation_offsets is None or translation_offsets.is_empty():
        return target.clone()
    offsets = {
        (str(row["component"]), str(row["level"])): float(
            row["link_offset_to_MLB"]
        )
        for row in translation_offsets.filter(pl.col("age_band") == "ALL").iter_rows(
            named=True
        )
    }
    rows: list[dict[str, object]] = []
    for row in target.iter_rows(named=True):
        evidence = float(row["hitter_talent_pa"])
        if evidence <= 0.0:
            raise ValueError("reference target evidence must be positive")
        probabilities = {
            outcome: float(row[outcome]) / evidence
            for outcome in HITTER_TALENT_OUTCOMES
        }
        level = normalize_level(row[level_column])
        links = {
            component: value + offsets.get((component, level), 0.0)
            for component, value in probability_links(probabilities).items()
        }
        translated = probabilities_from_links(links)
        translated_counts = {
            outcome: translated[outcome] * evidence
            for outcome in HITTER_TALENT_OUTCOMES
        }
        translated_counts["OTHER_OUT"] = evidence - sum(
            translated_counts[outcome]
            for outcome in HITTER_TALENT_OUTCOMES
            if outcome != "OTHER_OUT"
        )
        rows.append(
            {
                **row,
                **translated_counts,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None).sort("player_id")


def strongest_baseline(
    metrics: Mapping[str, Mapping[str, float | int | None]], metric: str
) -> tuple[str, float]:
    """Return the lowest-loss comparator with deterministic ID tie-breaking."""

    candidates = []
    for model_id, values in metrics.items():
        value = values.get(metric)
        if value is None:
            raise ValueError(f"baseline metric is unavailable: {model_id} {metric}")
        candidates.append((model_id, float(value)))
    return min(candidates, key=lambda item: (item[1], item[0]))


def primary_gate(
    candidate: Mapping[str, float | int | None],
    baselines: Mapping[str, Mapping[str, float | int | None]],
) -> dict[str, object]:
    """Require strict improvement on all four predeclared primary metrics."""

    comparisons: dict[str, object] = {}
    for metric in PRIMARY_METRICS:
        baseline_id, baseline = strongest_baseline(baselines, metric)
        value = float(candidate[metric])
        comparisons[metric] = {
            "candidate": value,
            "baseline_id": baseline_id,
            "baseline": baseline,
            "candidate_minus_baseline": value - baseline,
            "pass": value - baseline < -STRICT_TOLERANCE,
        }
    return {
        "comparisons": comparisons,
        "pass": all(bool(row["pass"]) for row in comparisons.values()),
    }


def subgroup_reversal_gate(
    candidate: Mapping[str, float | int | None],
    baselines: Mapping[str, Mapping[str, float | int | None]],
) -> dict[str, object]:
    """Apply the frozen material supported-subgroup reversal definition."""

    deltas = {
        metric: float(candidate[metric]) - strongest_baseline(baselines, metric)[1]
        for metric in PRIMARY_METRICS
    }
    rate_reversal = (
        deltas["woba_rmse"] > 0.002
        and deltas["runs_per_600_rmse"] > 0.5
    )
    proper_reversal = (
        deltas["terminal_log_loss"] > 0.0005
        and deltas["terminal_brier_score"] > 0.0005
    )
    return {
        "candidate_minus_metric_wise_comparator": deltas,
        "rate_reversal": rate_reversal,
        "proper_score_reversal": proper_reversal,
        "pass": not rate_reversal and not proper_reversal,
    }
