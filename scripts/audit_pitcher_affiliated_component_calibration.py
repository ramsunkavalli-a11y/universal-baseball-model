#!/usr/bin/env python3
"""Fit one 2024 pitcher component intercept and confirm it once on 2025."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_pitcher_affiliated_regression import (
    COMPONENTS,
    INCUMBENT,
    SOURCE,
    _bootstrap_delta,
    _components,
    _fold_inputs,
    _run_rate_diagnostic,
    _score_rows,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    score_component_profiles,
)


OUTPUT = Path("docs/pitcher-affiliated-component-calibration-result.json")


def _incumbent_fold(
    source: pl.DataFrame, target_season: int
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, float]]:
    players, evidence, target, support = _fold_inputs(source, target_season)
    offsets = support.pop("offsets")
    predictions = build_translated_affiliated_profiles(
        players,
        evidence,
        offsets,
        exposure_column="batters_faced",
        component_columns=COMPONENTS,
        current_season=target_season - 1,
        reference_season=target_season - 1,
        regression_exposure=INCUMBENT,
    )
    return predictions, target, support


def _fit_clr_offset(
    predictions: pl.DataFrame, target: pl.DataFrame
) -> dict[str, float]:
    rows = _score_rows(predictions, target)
    total_bf = float(rows.get_column("batters_faced").sum())
    predicted = np.asarray(
        [
            float(
                rows.select(
                    (pl.col(f"p_{component}") * pl.col("batters_faced")).sum()
                ).item()
            )
            / total_bf
            for component in COMPONENTS
        ]
    )
    observed = np.asarray(
        [float(rows.get_column(component).sum()) / total_bf for component in COMPONENTS]
    )
    raw = np.log(observed) - np.log(predicted)
    centered = raw - raw.mean()
    return {
        component: float(centered[index])
        for index, component in enumerate(COMPONENTS)
    }


def _apply_clr_offset(
    predictions: pl.DataFrame, offset: dict[str, float]
) -> pl.DataFrame:
    rows = []
    for row in predictions.sort("player_id").iter_rows(named=True):
        logits = np.asarray(
            [
                np.log(float(row[f"p_{component}"])) + offset[component]
                for component in COMPONENTS
            ]
        )
        probabilities = np.exp(logits - logits.max())
        probabilities /= probabilities.sum()
        rows.append(
            {
                **row,
                **{
                    f"p_{component}": float(probabilities[index])
                    for index, component in enumerate(COMPONENTS)
                },
            }
        )
    return pl.DataFrame(rows).sort("player_id")


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    development_prediction, development_target, _ = _incumbent_fold(source, 2024)
    offset = _fit_clr_offset(development_prediction, development_target)
    development_candidate = _apply_clr_offset(development_prediction, offset)

    confirmation_prediction, confirmation_target, prior = _incumbent_fold(source, 2025)
    confirmation_candidate = _apply_clr_offset(confirmation_prediction, offset)
    incumbent_score = score_component_profiles(
        confirmation_prediction,
        confirmation_target,
        exposure_column="batters_faced",
        component_columns=COMPONENTS,
    )
    candidate_score = score_component_profiles(
        confirmation_candidate,
        confirmation_target,
        exposure_column="batters_faced",
        component_columns=COMPONENTS,
    )
    log_loss_delta = float(candidate_score["component_log_loss"]) - float(
        incumbent_score["component_log_loss"]
    )
    brier_delta = float(candidate_score["component_brier_score"]) - float(
        incumbent_score["component_brier_score"]
    )
    promoted = log_loss_delta < 0 and brier_delta < 0
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_affiliated_component_calibration_complete",
        "contract": "docs/pitcher-affiliated-component-calibration-plan.md",
        "development_2024": {
            "clr_offset": offset,
            "incumbent_score": score_component_profiles(
                development_prediction,
                development_target,
                exposure_column="batters_faced",
                component_columns=COMPONENTS,
            ),
            "candidate_score": score_component_profiles(
                development_candidate,
                development_target,
                exposure_column="batters_faced",
                component_columns=COMPONENTS,
            ),
        },
        "confirmation_2025": {
            "incumbent_score": incumbent_score,
            "candidate_score": candidate_score,
            "candidate_minus_incumbent_component_log_loss": log_loss_delta,
            "candidate_minus_incumbent_component_brier": brier_delta,
            "bootstrap_candidate_minus_incumbent": _bootstrap_delta(
                _score_rows(confirmation_candidate, confirmation_target),
                _score_rows(confirmation_prediction, confirmation_target),
                seed=20250910,
            ),
            "candidate_run_rate_diagnostic": _run_rate_diagnostic(
                confirmation_candidate, confirmation_target, prior
            ),
            "incumbent_run_rate_diagnostic": _run_rate_diagnostic(
                confirmation_prediction, confirmation_target, prior
            ),
        },
        "decision": {"promoted": promoted},
        "boundaries": {
            "current_2026_outcomes_used": False,
            "outside_fv_used": False,
            "calibration_strength_tuned_on_confirmation": False,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "component_log_loss_delta": log_loss_delta,
                "component_brier_delta": brier_delta,
                "promoted": promoted,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
