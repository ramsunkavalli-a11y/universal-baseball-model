#!/usr/bin/env python3
"""Select hitter affiliated-profile shrinkage on 2024 and confirm on 2025."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_hitter_age_level_batting_side import (
    COMPONENTS,
    SOURCE,
    _bootstrap,
    _components,
    _score_rows,
)
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)


CANDIDATES = (400.0, 800.0, 1200.0, 1600.0, 2400.0, 3600.0)
INCUMBENT = 1200.0
OUTPUT = Path("docs/hitter-affiliated-regression-audit-result.json")


def _fold(source: pl.DataFrame, target_season: int) -> dict[str, object]:
    cutoff = target_season - 1
    evidence = source.filter(pl.col("season") <= cutoff)
    seasons = tuple(
        int(value) for value in evidence["season"].unique().sort().to_list()
    )
    offsets = fit_same_season_component_translation(
        source,
        exposure_column="plate_appearances",
        component_columns=COMPONENTS,
        completed_seasons=seasons,
        minimum_level_exposure=30,
    ).offsets
    exposure = evidence.group_by("player_id").agg(
        pl.col("plate_appearances").sum().alias("all_pa"),
        pl.col("plate_appearances")
        .filter(pl.col("level_group") == "MLB")
        .sum()
        .alias("mlb_pa"),
    )
    players = exposure.filter(
        (pl.col("all_pa") > 0) & (pl.col("mlb_pa") == 0)
    ).select("player_id")
    target = source.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    predictions = {
        int(regression): build_translated_affiliated_profiles(
            players,
            evidence,
            offsets,
            exposure_column="plate_appearances",
            component_columns=COMPONENTS,
            current_season=cutoff,
            reference_season=cutoff,
            regression_exposure=regression,
        )
        for regression in CANDIDATES
    }
    scores = {
        str(int(regression)): score_component_profiles(
            predictions[int(regression)],
            target,
            exposure_column="plate_appearances",
            component_columns=COMPONENTS,
        )
        for regression in CANDIDATES
    }
    return {"target": target, "predictions": predictions, "scores": scores}


def main() -> int:
    source = _components(pl.read_parquet(SOURCE))
    development = _fold(source, 2024)
    incumbent_key = str(int(INCUMBENT))
    incumbent_dev = development["scores"][incumbent_key]
    eligible = [
        regression for regression in CANDIDATES
        if development["scores"][str(int(regression))]["component_log_loss"]
        < incumbent_dev["component_log_loss"]
        and development["scores"][str(int(regression))]["component_brier_score"]
        < incumbent_dev["component_brier_score"]
    ]
    selected = min(
        eligible,
        key=lambda regression: (
            development["scores"][str(int(regression))]["component_log_loss"],
            abs(regression - INCUMBENT),
        ),
    ) if eligible else INCUMBENT

    confirmation = _fold(source, 2025)
    selected_key = str(int(selected))
    selected_score = confirmation["scores"][selected_key]
    incumbent_score = confirmation["scores"][incumbent_key]
    selected_rows = _score_rows(
        confirmation["predictions"][int(selected)], confirmation["target"]
    )
    incumbent_rows = _score_rows(
        confirmation["predictions"][int(INCUMBENT)], confirmation["target"]
    )
    bootstrap = _bootstrap(selected_rows, incumbent_rows)
    ll_delta = selected_score["component_log_loss"] - incumbent_score["component_log_loss"]
    brier_delta = selected_score["component_brier_score"] - incumbent_score["component_brier_score"]
    promoted = bool(
        selected != INCUMBENT and ll_delta < 0 and brier_delta < 0
        and bootstrap["component_log_loss"]["upper_95"] <= 0
        and bootstrap["component_brier"]["upper_95"] <= 0
    )
    report = {
        "report_schema_version": "0.1",
        "status": "hitter_affiliated_regression_audit_complete",
        "contract": "docs/hitter-affiliated-regression-audit-plan.md",
        "development_2024": {"scores": development["scores"]},
        "selection": {
            "selected_regression_pa": int(selected),
            "incumbent_regression_pa": int(INCUMBENT),
            "rule_applied_before_confirmation": True,
        },
        "confirmation_2025": {
            "selected_score": selected_score,
            "incumbent_score": incumbent_score,
            "selected_minus_incumbent_log_loss": ll_delta,
            "selected_minus_incumbent_brier": brier_delta,
            "player_bootstrap": bootstrap,
        },
        "decision": {
            "promoted": promoted,
            "regression_pa": int(selected if promoted else INCUMBENT),
        },
        "boundaries": {
            "current_2026_outcomes_used": False,
            "demographics_used": False,
            "outside_fv_used": False,
            "current_values_changed": False,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "selected_regression_pa": int(selected),
        "confirmation_log_loss_delta": ll_delta,
        "confirmation_brier_delta": brier_delta,
        "bootstrap": bootstrap,
        "promoted": promoted,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
