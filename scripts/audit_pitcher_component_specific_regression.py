#!/usr/bin/env python3
"""Test component-specific affiliated pitcher shrinkage without changing production."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

import audit_pitcher_affiliated_regression as prior_audit
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    score_component_profiles,
)


COMPONENTS = prior_audit.COMPONENTS
GRID = (200.0, 400.0, 600.0, 800.0, 1200.0, 1600.0)
INCUMBENT = 800.0
OUTPUT = Path("docs/pitcher-component-specific-regression-result.json")


def _inputs(source: pl.DataFrame, target_season: int):
    players, evidence, target, support = prior_audit._fold_inputs(source, target_season)
    offsets = support.pop("offsets")
    return players, evidence, target, support, offsets


def _predict(
    players: pl.DataFrame,
    evidence: pl.DataFrame,
    offsets: pl.DataFrame,
    target_season: int,
    strengths: dict[str, float],
) -> pl.DataFrame:
    return build_translated_affiliated_profiles(
        players, evidence, offsets,
        exposure_column="batters_faced", component_columns=COMPONENTS,
        current_season=target_season - 1, reference_season=target_season - 1,
        regression_exposure=strengths,
    )


def _score(predictions: pl.DataFrame, target: pl.DataFrame) -> dict[str, object]:
    return score_component_profiles(
        predictions, target,
        exposure_column="batters_faced", component_columns=COMPONENTS,
    )


def _better(candidate: dict[str, object], incumbent: dict[str, object]) -> bool:
    return (
        float(candidate["component_log_loss"])
        < float(incumbent["component_log_loss"])
        and float(candidate["component_brier_score"])
        < float(incumbent["component_brier_score"])
    )


def main() -> int:
    source = prior_audit._components(pl.read_parquet(prior_audit.SOURCE))
    dev_players, dev_evidence, dev_target, _, dev_offsets = _inputs(source, 2024)
    incumbent_strengths = {component: INCUMBENT for component in COMPONENTS}
    dev_incumbent = _score(
        _predict(dev_players, dev_evidence, dev_offsets, 2024, incumbent_strengths),
        dev_target,
    )
    ablations: dict[str, dict[str, dict[str, object]]] = {}
    selected = dict(incumbent_strengths)
    for component in COMPONENTS:
        component_scores = {}
        for strength in GRID:
            candidate_strengths = dict(incumbent_strengths)
            candidate_strengths[component] = strength
            component_scores[str(int(strength))] = _score(
                _predict(
                    dev_players, dev_evidence, dev_offsets, 2024,
                    candidate_strengths,
                ),
                dev_target,
            )
        eligible = [
            strength for strength in GRID
            if _better(component_scores[str(int(strength))], dev_incumbent)
        ]
        if eligible:
            selected[component] = min(
                eligible,
                key=lambda strength: (
                    float(component_scores[str(int(strength))]["component_log_loss"]),
                    -strength,
                ),
            )
        ablations[component] = component_scores

    dev_selected = _score(
        _predict(dev_players, dev_evidence, dev_offsets, 2024, selected), dev_target
    )
    val_players, val_evidence, val_target, _, val_offsets = _inputs(source, 2025)
    val_incumbent_predictions = _predict(
        val_players, val_evidence, val_offsets, 2025, incumbent_strengths
    )
    val_selected_predictions = _predict(
        val_players, val_evidence, val_offsets, 2025, selected
    )
    val_incumbent = _score(val_incumbent_predictions, val_target)
    val_selected = _score(val_selected_predictions, val_target)
    report = {
        "report_schema_version": "0.1",
        "status": "diagnostic_complete_not_eligible_for_promotion",
        "population": "affiliated pitchers with no prior MLB BF who appear in MLB in target year",
        "incumbent_regression_bf": incumbent_strengths,
        "candidate_grid_bf": list(GRID),
        "selection_year": 2024,
        "selected_regression_bf": selected,
        "development": {
            "incumbent": dev_incumbent,
            "selected": dev_selected,
            "one_component_at_a_time": ablations,
        },
        "stability_year": 2025,
        "stability": {
            "incumbent": val_incumbent,
            "selected": val_selected,
            "selected_minus_incumbent_log_loss": (
                float(val_selected["component_log_loss"])
                - float(val_incumbent["component_log_loss"])
            ),
            "selected_minus_incumbent_brier": (
                float(val_selected["component_brier_score"])
                - float(val_incumbent["component_brier_score"])
            ),
        },
        "selection_rules": {
            "candidate_family": "change one component from 800 BF at a time",
            "eligibility": "must improve both component log loss and Brier in 2024",
            "tie": "prefer stronger shrinkage",
            "joint_candidate": "combine only the independently eligible strengths",
        },
        "promotion_eligible": False,
        "promotion_blocker": "2025 was previously disclosed; this is stability evidence, not untouched confirmation",
        "outside_fv_used": False,
        "production_changed": False,
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_regression_bf": selected,
        "development_delta_log_loss": (
            float(dev_selected["component_log_loss"])
            - float(dev_incumbent["component_log_loss"])
        ),
        "stability_delta_log_loss": report["stability"]["selected_minus_incumbent_log_loss"],
        "stability_delta_brier": report["stability"]["selected_minus_incumbent_brier"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
