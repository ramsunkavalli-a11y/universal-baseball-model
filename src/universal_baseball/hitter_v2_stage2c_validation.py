"""Frozen Stage 2c E1 conditional scores and gate primitives."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2b_validation import (
    STRICT_IMPROVEMENT_TOLERANCE,
    strongest_baseline_value,
)


CONTACT_OUTCOMES = (
    "HR",
    "1B",
    "2B",
    "3B",
    "ROE",
    "FC_REACH",
    "SF",
    "MULTI_OUT",
    "OTHER_OUT",
)


def score_hr_conditional(
    predictions: pl.DataFrame,
    target: pl.DataFrame,
    *,
    weighting: str,
) -> dict[str, float | int]:
    """Score HR versus non-HR contact in equal-player or contact-event view."""

    if weighting not in {"player", "pa"}:
        raise ValueError("weighting must be 'player' or 'pa'")
    probability_columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    joined = target.join(
        predictions.select("player_id", *probability_columns),
        on="player_id",
        how="inner",
        validate="1:1",
    ).sort("player_id")
    rows: list[tuple[float, float, float]] = []
    for row in joined.iter_rows(named=True):
        success = float(row["HR"])
        parent_events = sum(float(row[outcome]) for outcome in CONTACT_OUTCOMES)
        if parent_events <= 0.0:
            continue
        parent_mass = sum(float(row[f"p_{outcome}"]) for outcome in CONTACT_OUTCOMES)
        if parent_mass <= 0.0:
            raise ValueError("predicted contact parent has zero probability mass")
        predicted = float(row["p_HR"]) / parent_mass
        actual = success / parent_events
        predicted = min(max(predicted, 1e-12), 1.0 - 1e-12)
        log_loss = -(
            actual * np.log(predicted) + (1.0 - actual) * np.log(1.0 - predicted)
        )
        brier = (
            1.0
            - 2.0 * (actual * predicted + (1.0 - actual) * (1.0 - predicted))
            + predicted**2
            + (1.0 - predicted) ** 2
        )
        rows.append((float(log_loss), float(brier), parent_events))
    if not rows:
        raise ValueError("HR conditional score has no contact events")
    values = np.asarray(rows, dtype=float)
    weights = np.ones(len(rows), dtype=float) if weighting == "player" else values[:, 2]
    return {
        "players": len(rows),
        "contact_events": int(values[:, 2].sum()),
        "hr_conditional_log_loss": float(np.average(values[:, 0], weights=weights)),
        "hr_conditional_brier": float(np.average(values[:, 1], weights=weights)),
    }


def hr_increment_gate(
    candidate: Mapping[str, float | int],
    e0: Mapping[str, float | int],
) -> dict[str, object]:
    """Require the predeclared strict HR-conditional log-loss improvement."""

    delta = float(candidate["hr_conditional_log_loss"]) - float(
        e0["hr_conditional_log_loss"]
    )
    return {
        "candidate": float(candidate["hr_conditional_log_loss"]),
        "e0": float(e0["hr_conditional_log_loss"]),
        "candidate_minus_e0": delta,
        "pass": delta < -STRICT_IMPROVEMENT_TOLERANCE,
    }


def pooled_rate_gate(
    candidate: Mapping[str, float | int | None],
    b0: Mapping[str, float | int | None],
    b1: Mapping[str, float | int | None],
) -> dict[str, object]:
    """Require pooled wOBA and runs/600 RMSE improvement over simple baselines."""

    comparisons: dict[str, object] = {}
    for metric in ("woba_rmse", "runs_per_600_rmse"):
        baseline_id, baseline = strongest_baseline_value(b0, b1, metric)
        value = float(candidate[metric])
        delta = value - baseline
        comparisons[metric] = {
            "candidate": value,
            "baseline_id": baseline_id,
            "baseline": baseline,
            "candidate_minus_baseline": delta,
            "pass": delta < -STRICT_IMPROVEMENT_TOLERANCE,
        }
    return {
        "comparisons": comparisons,
        "pass": all(bool(value["pass"]) for value in comparisons.values()),
    }
