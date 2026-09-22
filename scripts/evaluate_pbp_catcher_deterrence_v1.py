#!/usr/bin/env python3
"""Chronologically test all-level catcher steal-attempt deterrence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from evaluate_pbp_catcher_pilot import _evaluate_nested
from universal_baseball.historical_catcher_pbp import (
    extract_catcher_deterrence_opportunities,
    fit_crossed_deterrence_effects,
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
        default=Path("reports/generated/pbp-catcher-deterrence-v1"),
    )
    return parser.parse_args()


def _load_terminal(root: Path) -> pl.DataFrame:
    paths = sorted(root.glob("season=*/level=*/terminal/*.parquet"))
    columns = [
        "season",
        "level",
        "source_asset",
        "game_pk",
        "at_bat_index",
        "terminal_pitch_number",
        "pa_description",
        "fielder_2",
        "pitcher",
        "p_throws",
        "stand",
        "outs_when_up",
        "inning",
        "bat_score",
        "fld_score",
        "park_key",
        "start_runner_1b",
        "start_runner_2b",
        "start_runner_3b",
    ]
    return (
        pl.concat(
            [pl.read_parquet(path, columns=columns) for path in paths],
            how="diagonal_relaxed",
        )
        .sort("game_pk", "at_bat_index", "source_asset")
        .unique(subset=["game_pk", "at_bat_index"], keep="first", maintain_order=True)
    )


def main() -> int:
    args = _args()
    terminal = _load_terminal(args.input_root)
    opportunities = extract_catcher_deterrence_opportunities(terminal)
    scored = score_binary_context_residuals(
        opportunities,
        outcome_column="steal_attempted",
        context_columns=[
            "attempt_base",
            "pitcher_hand",
            "batter_side",
            "outs_when_up",
            "inning_band",
            "score_band",
            "pitch_window",
        ],
        context_prior=100.0,
        park_prior=200.0,
    )
    catchers, pitchers, runners = fit_crossed_deterrence_effects(scored)
    selected, decisions, metrics = _evaluate_nested(
        catchers,
        minimum_target_opportunities=100,
        minimum_prior_pairs=25,
        regression_grid=(1200.0, 2000.0, 5000.0, 10000.0, 20000.0),
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
        "status": "pbp_catcher_deterrence_complete",
        "protected_2026_outcomes_used": False,
        "terminal_plays": terminal.height,
        "steal_eligible_pa_starts": opportunities.height,
        "observed_attempts": int(opportunities["steal_attempted"].sum()),
        "observed_attempt_rate": float(opportunities["steal_attempted"].mean()),
        "catcher_seasons": catchers.height,
        "pitcher_seasons": pitchers.height,
        "runner_seasons": runners.height,
        "nested_selection": decisions,
        "pooled_metrics": metrics,
        "player_clustered_rmse_change": clustered,
        "effect_direction": "negative catcher effect means fewer attempts than expected",
        "decision_rule": (
            "advance only if prior catcher deterrence beats neutral on later-season "
            "attempt-rate residuals with favorable clustered uncertainty"
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
