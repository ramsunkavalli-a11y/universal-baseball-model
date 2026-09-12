#!/usr/bin/env python3
"""Test whether the pitcher peak model orders future talent, not only probabilities."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import polars as pl

from audit_age_to_peak_talent import _fit_peak
from audit_one_year_talent_development import (
    PITCHER_COMPONENTS,
    _predict,
)
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA,
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.projection_composition import sequential_helmert_ilr_basis


EXAMPLES = Path(
    "reports/generated/age-to-peak-talent/tables/batters_faced_examples.parquet"
)
OUTPUT = Path("reports/generated/peak-talent-ranking-audit/report.json")
REPLAY_END_YEARS = (2018, 2019, 2023, 2024, 2025)
ALPHA = 100.0


def _rates(rows: list[dict[str, object]], prefix: str) -> np.ndarray:
    values = np.asarray([
        [float(row[f"{prefix}{component}"]) for component in PITCHER_COMPONENTS]
        for row in rows
    ])
    if prefix == "target_":
        values = values / values.sum(axis=1, keepdims=True)
    return values


def _run_weights(training_rows: list[dict[str, object]]) -> np.ndarray:
    counts = np.asarray([
        [float(row[f"target_{component}"]) for component in PITCHER_COMPONENTS]
        for row in training_rows
    ]).sum(axis=0)
    reference = counts / counts.sum()
    known = (
        reference[1] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + reference[2] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + reference[3] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    other_weight = (NEUTRAL_WOBA - known) / reference[4]
    return np.asarray([
        0.0,
        NEUTRAL_WOBA_WEIGHTS["UBB"],
        NEUTRAL_WOBA_WEIGHTS["HBP"],
        NEUTRAL_WOBA_WEIGHTS["HR"],
        other_weight,
    ])


def _run_scores(probabilities: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return -(probabilities @ weights - NEUTRAL_WOBA) * 800.0 / NEUTRAL_WOBA_SCALE


def _ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=float)
    ranks[order] = np.arange(len(values), dtype=float)
    return ranks


def _ranking_score(predicted: np.ndarray, actual: np.ndarray) -> dict[str, float | int]:
    predicted_rank = _ranks(predicted)
    actual_rank = _ranks(actual)
    spearman = float(np.corrcoef(predicted_rank, actual_rank)[0, 1])
    result: dict[str, float | int] = {
        "players": len(actual),
        "spearman": spearman,
    }
    for fraction, label in ((0.10, "top_decile"), (0.25, "top_quartile")):
        count = max(1, math.ceil(len(actual) * fraction))
        predicted_top = set(np.argsort(predicted)[-count:])
        actual_top = set(np.argsort(actual)[-count:])
        result[f"{label}_count"] = count
        result[f"{label}_precision"] = len(predicted_top & actual_top) / count
        result[f"{label}_actual_runs"] = float(
            np.mean(actual[list(predicted_top)])
        )
    return result


def main() -> int:
    examples = pl.read_parquet(EXAMPLES)
    basis = sequential_helmert_ilr_basis(len(PITCHER_COMPONENTS))
    replay = []
    for end_year in REPLAY_END_YEARS:
        training = examples.filter(pl.col("peak_window_end_year") < end_year).to_dicts()
        target = examples.filter(pl.col("peak_window_end_year") == end_year).to_dicts()
        weights = _run_weights(training)
        actual = _run_scores(_rates(target, "target_"), weights)
        age_level = _predict(
            _fit_peak(training, PITCHER_COMPONENTS, "age_level", ALPHA, basis),
            target,
            PITCHER_COMPONENTS,
            "age_level",
            basis,
        )
        component = _predict(
            _fit_peak(
                training,
                PITCHER_COMPONENTS,
                "component_development",
                ALPHA,
                basis,
            ),
            target,
            PITCHER_COMPONENTS,
            "component_development",
            basis,
        )
        predictions = {
            "carry_forward": _rates(target, "p_"),
            "age_level": age_level,
            "blend_25_component": 0.75 * age_level + 0.25 * component,
            "blend_50_component": 0.50 * age_level + 0.50 * component,
            "blend_75_component": 0.25 * age_level + 0.75 * component,
            "component_development": component,
        }
        scores = {
            name: _ranking_score(_run_scores(probability, weights), actual)
            for name, probability in predictions.items()
        }
        replay.append({
            "peak_window_end_year": end_year,
            "actual_population_runs": float(np.mean(actual)),
            "models": scores,
        })
    comparison = {}
    for metric in ("spearman", "top_decile_precision", "top_decile_actual_runs"):
        deltas = [
            row["models"]["component_development"][metric]
            - row["models"]["age_level"][metric]
            for row in replay
        ]
        comparison[metric] = {
            "component_wins": sum(delta > 0 for delta in deltas),
            "ties": sum(delta == 0 for delta in deltas),
            "replays": len(deltas),
            "mean_delta": float(np.mean(deltas)),
        }
    candidate_names = (
        "age_level",
        "blend_25_component",
        "blend_50_component",
        "blend_75_component",
        "component_development",
    )
    selection_rows = [row for row in replay if row["peak_window_end_year"] <= 2019]
    selected = max(
        candidate_names,
        key=lambda name: np.mean([
            row["models"][name]["top_decile_actual_runs"] for row in selection_rows
        ]),
    )
    confirmation = []
    for row in replay:
        if row["peak_window_end_year"] < 2023:
            continue
        candidate = row["models"][selected]
        baseline = row["models"]["age_level"]
        confirmation.append({
            "peak_window_end_year": row["peak_window_end_year"],
            "spearman_delta": candidate["spearman"] - baseline["spearman"],
            "top_decile_precision_delta": (
                candidate["top_decile_precision"] - baseline["top_decile_precision"]
            ),
            "top_decile_actual_runs_delta": (
                candidate["top_decile_actual_runs"]
                - baseline["top_decile_actual_runs"]
            ),
        })
    passed = (
        selected == "blend_50_component"
        and all(row["spearman_delta"] >= -0.005 for row in confirmation)
        and all(row["top_decile_precision_delta"] >= 0 for row in confirmation)
        and all(row["top_decile_actual_runs_delta"] >= -0.5 for row in confirmation)
    )
    report = {
        "status": "promote_blended_ordering" if passed else "reject_precise_ordering",
        "question": "Does current component shape improve future peak pitcher ordering beyond age and level?",
        "public_rank_or_fv_used": False,
        "future_workload_used_as_weight": False,
        "run_weights_fit_from_prior_rows_only": True,
        "replay": replay,
        "component_vs_age_level": comparison,
        "selection": {
            "years": [2018, 2019],
            "criterion": "highest mean realized future runs among the predicted top decile",
            "selected": selected,
        },
        "confirmation": confirmation,
        "decision_rule": (
            "On 2023-2025, require no Spearman loss worse than 0.005, no top-decile "
            "precision loss, and no realized top-decile run loss worse than 0.5 runs."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
