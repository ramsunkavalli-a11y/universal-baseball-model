#!/usr/bin/env python3
"""Test the strength of only the pitcher HR level translation."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_pitcher_affiliated_regression import (
    COMPONENTS,
    _components,
    _fold_inputs,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    score_component_profiles,
)


SOURCE = Path(
    "reports/generated/affiliated-skill-source/tables/"
    "affiliated_pitching_components.parquet"
)
OUTPUT = Path("docs/pitcher-hr-translation-strength-audit-result.json")
STRENGTHS = (0.0, 0.25, 0.50, 0.75, 1.0)
INCUMBENT = 1.0


def _fold(source: pl.DataFrame, target_season: int) -> dict[str, object]:
    players, evidence, target, support = _fold_inputs(source, target_season)
    offsets = support["offsets"]
    predictions = {}
    scores = {}
    for strength in STRENGTHS:
        candidate_offsets = offsets.with_columns(
            pl.when(pl.col("component") == "hr")
            .then(pl.col("clr_environment_effect") * strength)
            .otherwise(pl.col("clr_environment_effect"))
            .alias("clr_environment_effect")
        )
        prediction = build_translated_affiliated_profiles(
            players,
            evidence,
            candidate_offsets,
            exposure_column="batters_faced",
            component_columns=COMPONENTS,
            current_season=target_season - 1,
            reference_season=target_season - 1,
            regression_exposure=800.0,
        )
        predictions[strength] = prediction
        scores[str(strength)] = score_component_profiles(
            prediction,
            target,
            exposure_column="batters_faced",
            component_columns=COMPONENTS,
        )
    return {"scores": scores, "predictions": predictions, "target": target}


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    development = _fold(source, 2024)
    incumbent_dev = development["scores"][str(INCUMBENT)]
    eligible = [
        strength
        for strength in STRENGTHS
        if development["scores"][str(strength)]["component_log_loss"]
        < incumbent_dev["component_log_loss"]
        and development["scores"][str(strength)]["component_brier_score"]
        < incumbent_dev["component_brier_score"]
    ]
    selected = min(
        eligible,
        key=lambda strength: development["scores"][str(strength)][
            "component_log_loss"
        ],
    ) if eligible else INCUMBENT
    confirmation = _fold(source, 2025)
    candidate = confirmation["scores"][str(selected)]
    incumbent = confirmation["scores"][str(INCUMBENT)]
    log_loss_delta = float(candidate["component_log_loss"] - incumbent["component_log_loss"])
    brier_delta = float(candidate["component_brier_score"] - incumbent["component_brier_score"])
    promoted = selected != INCUMBENT and log_loss_delta < 0 and brier_delta < 0
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_hr_translation_strength_audit_complete",
        "candidate": (
            "Multiply only the fitted HR level-environment offset by a fixed strength; "
            "all other component offsets and the 800-BF prior stay unchanged."
        ),
        "development_2024": {
            "scores": development["scores"],
            "selected_hr_translation_strength": selected,
        },
        "confirmation_2025": {
            "candidate": candidate,
            "incumbent": incumbent,
            "candidate_minus_incumbent_log_loss": log_loss_delta,
            "candidate_minus_incumbent_brier": brier_delta,
        },
        "decision": {
            "promoted": promoted,
            "production_hr_translation_strength": selected if promoted else INCUMBENT,
        },
        "boundaries": {
            "2026_outcomes_used": False,
            "outside_rank_or_fv_used": False,
            "only_hr_level_translation_varied": True,
            "regression_bf_changed": False,
            "arrival_or_workload_changed": False,
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
