#!/usr/bin/env python3
"""Test PA-level catcher blocking with all runner-on dirt-ball sequences."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from evaluate_pbp_catcher_pilot import _evaluate_nested, _read_partitions
from universal_baseball.historical_catcher_pbp import (
    extract_broad_catcher_blocking_opportunities,
    fit_crossed_catcher_pitcher_effects,
    score_binary_context_residuals,
)
from universal_baseball.hitter_target_architecture import paired_cluster_rmse_delta


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pbp-catcher-blocking-broad-v1"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    pitches = _read_partitions(args.input_root, "catcher_pitches")
    opportunities = extract_broad_catcher_blocking_opportunities(pitches)
    scored = score_binary_context_residuals(
        opportunities,
        outcome_column="block_failure",
        context_columns=[
            "start_runner_count",
            "dirt_pitch_count_band",
            "dirt_severity_band",
            "pitcher_hand",
            "batter_side",
        ],
        context_prior=120.0,
        park_prior=200.0,
    )
    catchers, pitchers = fit_crossed_catcher_pitcher_effects(
        scored, catcher_prior=250.0, pitcher_prior=250.0
    )
    selected, decisions, metrics = _evaluate_nested(
        catchers,
        minimum_target_opportunities=30,
        minimum_prior_pairs=25,
        regression_grid=(400.0, 800.0, 1200.0, 2000.0, 5000.0, 10000.0),
    )
    pooled = pl.concat(selected) if selected else pl.DataFrame()
    clustered = None
    if not pooled.is_empty():
        clustered = paired_cluster_rmse_delta(
            pooled["actual_effect"].to_numpy(),
            pooled["projected_effect"].to_numpy(),
            pl.Series("neutral", [0.0] * pooled.height).to_numpy(),
            pooled["player_id"].to_numpy(),
            bootstrap_samples=5_000,
        )
    report = {
        "schema_version": "0.1",
        "status": "pbp_catcher_blocking_broad_complete",
        "protected_2026_outcomes_used": False,
        "runner_on_dirt_ball_pas": opportunities.height,
        "failures": int(opportunities["block_failure"].sum()),
        "failure_rate": float(opportunities["block_failure"].mean()),
        "catcher_seasons": catchers.height,
        "pitcher_seasons": pitchers.height,
        "nested_selection": decisions,
        "pooled_metrics": metrics,
        "player_clustered_rmse_change": clustered,
        "effect_direction": "positive catcher effect means more failures than expected",
        "decision_rule": (
            "advance only if prior catcher effect beats neutral on later PA-level "
            "blocking failure residuals with favorable clustered uncertainty"
        ),
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    catchers.write_parquet(args.output_root / "catcher-season-effects.parquet")
    if not pooled.is_empty():
        pooled.write_parquet(args.output_root / "nested-predictions.parquet")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
