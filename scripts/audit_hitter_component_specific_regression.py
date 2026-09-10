#!/usr/bin/env python3
"""Test component-specific affiliated hitter shrinkage without changing production."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

import audit_hitter_affiliated_regression as prior_audit
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
)


COMPONENTS = prior_audit.COMPONENTS
GRID = prior_audit.CANDIDATES
INCUMBENT = prior_audit.INCUMBENT
OUTPUT = Path("docs/hitter-component-specific-regression-result.json")


def _inputs(source: pl.DataFrame, target_season: int):
    cutoff = target_season - 1
    evidence = source.filter(pl.col("season") <= cutoff)
    seasons = tuple(int(v) for v in evidence["season"].unique().sort().to_list())
    offsets = fit_same_season_component_translation(
        source, exposure_column="plate_appearances", component_columns=COMPONENTS,
        completed_seasons=seasons, minimum_level_exposure=30,
    ).offsets
    exposure = evidence.group_by("player_id").agg(
        pl.col("plate_appearances").sum().alias("all_pa"),
        pl.col("plate_appearances").filter(pl.col("level_group") == "MLB").sum().alias("mlb_pa"),
    )
    players = exposure.filter((pl.col("all_pa") > 0) & (pl.col("mlb_pa") == 0)).select("player_id")
    target = source.filter(
        (pl.col("season") == target_season) & (pl.col("level_group") == "MLB")
    )
    return players, evidence, target, offsets


def _predict(players, evidence, offsets, target_season, strengths):
    return build_translated_affiliated_profiles(
        players, evidence, offsets,
        exposure_column="plate_appearances", component_columns=COMPONENTS,
        current_season=target_season - 1, reference_season=target_season - 1,
        regression_exposure=strengths,
    )


def _score(predictions, target):
    return score_component_profiles(
        predictions, target,
        exposure_column="plate_appearances", component_columns=COMPONENTS,
    )


def _better(candidate, incumbent):
    return (
        candidate["component_log_loss"] < incumbent["component_log_loss"]
        and candidate["component_brier_score"] < incumbent["component_brier_score"]
    )


def main() -> int:
    source = prior_audit._components(pl.read_parquet(prior_audit.SOURCE))
    incumbent_strengths = {component: INCUMBENT for component in COMPONENTS}
    dev_players, dev_evidence, dev_target, dev_offsets = _inputs(source, 2024)
    dev_incumbent = _score(
        _predict(dev_players, dev_evidence, dev_offsets, 2024, incumbent_strengths), dev_target
    )
    selected = dict(incumbent_strengths)
    ablations = {}
    for component in COMPONENTS:
        scores = {}
        for strength in GRID:
            candidate = dict(incumbent_strengths)
            candidate[component] = strength
            scores[str(int(strength))] = _score(
                _predict(dev_players, dev_evidence, dev_offsets, 2024, candidate), dev_target
            )
        eligible = [s for s in GRID if _better(scores[str(int(s))], dev_incumbent)]
        if eligible:
            selected[component] = min(
                eligible,
                key=lambda s: (scores[str(int(s))]["component_log_loss"], -s),
            )
        ablations[component] = scores
    dev_selected = _score(
        _predict(dev_players, dev_evidence, dev_offsets, 2024, selected), dev_target
    )
    val_players, val_evidence, val_target, val_offsets = _inputs(source, 2025)
    val_incumbent_predictions = _predict(
        val_players, val_evidence, val_offsets, 2025, incumbent_strengths
    )
    val_selected_predictions = _predict(
        val_players, val_evidence, val_offsets, 2025, selected
    )
    val_incumbent = _score(val_incumbent_predictions, val_target)
    val_selected = _score(val_selected_predictions, val_target)
    bootstrap = prior_audit._bootstrap(
        prior_audit._score_rows(val_selected_predictions, val_target),
        prior_audit._score_rows(val_incumbent_predictions, val_target),
    )
    report = {
        "report_schema_version": "0.1",
        "status": "diagnostic_complete_not_eligible_for_promotion",
        "population": "affiliated hitters with no prior MLB PA who appear in MLB in target year",
        "incumbent_regression_pa": incumbent_strengths,
        "candidate_grid_pa": list(GRID),
        "selection_year": 2024,
        "selected_regression_pa": selected,
        "development": {
            "incumbent": dev_incumbent, "selected": dev_selected,
            "one_component_at_a_time": ablations,
        },
        "stability_year": 2025,
        "stability": {
            "incumbent": val_incumbent,
            "selected": val_selected,
            "selected_minus_incumbent_log_loss": val_selected["component_log_loss"] - val_incumbent["component_log_loss"],
            "selected_minus_incumbent_brier": val_selected["component_brier_score"] - val_incumbent["component_brier_score"],
            "player_bootstrap_selected_minus_incumbent": bootstrap,
        },
        "promotion_eligible": False,
        "promotion_blocker": "2025 was previously disclosed; this is stability evidence, not untouched confirmation",
        "outside_fv_used": False,
        "production_changed": False,
    }
    OUTPUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "selected_regression_pa": selected,
        "development_delta_log_loss": dev_selected["component_log_loss"] - dev_incumbent["component_log_loss"],
        "stability_delta_log_loss": report["stability"]["selected_minus_incumbent_log_loss"],
        "stability_delta_brier": report["stability"]["selected_minus_incumbent_brier"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
