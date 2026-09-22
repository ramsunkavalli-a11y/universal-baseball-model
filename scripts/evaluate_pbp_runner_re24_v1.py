#!/usr/bin/env python3
"""Replace the ordinal MiLB runner pilot with focal-runner RE24 value."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from evaluate_pbp_runner_arm_pilot import (
    _all_folds,
    _load,
    _pooled,
    _select_nested,
)
from universal_baseball.hitter_target_architecture import paired_cluster_rmse_delta
from universal_baseball.historical_runner_arm import (
    add_advancement_re24,
    build_run_expectancy_table,
    fit_crossed_runner_arm_effects,
    score_contextual_advancement_residuals,
)


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
        default=Path("reports/generated/pbp-runner-re24-v1"),
    )
    return parser.parse_args()


def _load_terminal(root: Path) -> pl.DataFrame:
    paths = sorted(root.glob("season=*/level=*/terminal/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no terminal partitions under {root}")
    columns = [
        "season",
        "level",
        "game_pk",
        "inning",
        "inning_top_bot",
        "at_bat_index",
        "outs_when_up",
        "start_runner_1b",
        "start_runner_2b",
        "start_runner_3b",
        "bat_score",
        "post_bat_score",
    ]
    return pl.concat(
        [pl.read_parquet(path, columns=columns) for path in paths],
        how="vertical_relaxed",
    )


def main() -> int:
    args = _args()
    print("loading terminal and runner opportunities", flush=True)
    terminal = _load_terminal(args.input_root)
    opportunities = _load(args.input_root)
    print("building RE24 and focal-runner values", flush=True)
    re24 = build_run_expectancy_table(terminal)
    valued = add_advancement_re24(opportunities, re24).filter(
        pl.col("advancement_re24").is_not_null()
    )
    scored = score_contextual_advancement_residuals(
        valued, value_column="advancement_re24"
    )
    runners, arms = fit_crossed_runner_arm_effects(scored)
    runner_pairs = _all_folds(runners, minimum_target_opportunities=8)
    selected, decisions = _select_nested(runner_pairs, minimum_prior_pairs=25)
    metrics = _pooled(selected)
    pooled = pl.concat(selected, how="diagonal_relaxed") if selected else pl.DataFrame()
    report = {
        "report_schema_version": "0.1",
        "status": "pbp_runner_re24_complete",
        "data_scope": "all nonempty materialized public 2016-2024 MiLB PBP partitions",
        "terminal_plays": terminal.height,
        "runner_opportunities": opportunities.height,
        "re24_valued_opportunities": valued.height,
        "run_expectancy_cells": re24.height,
        "years": sorted(scored["season"].unique().to_list()),
        "runner_nested_selection": decisions,
        "runner_pooled_metrics": metrics,
        "runner_projected_minus_neutral": (
            paired_cluster_rmse_delta(
                pooled["actual_effect"].to_numpy(),
                pooled["projected_effect"].to_numpy(),
                pl.Series("neutral", [0.0] * pooled.height).to_numpy(),
                pooled["player_id"].to_numpy(),
                bootstrap_samples=5_000,
            )
            if not pooled.is_empty()
            else None
        ),
        "mean_re24_value": float(valued["advancement_re24"].mean()),
        "mean_absolute_re24_value": float(valued["advancement_re24"].abs().mean()),
        "protected_2026_accessed": False,
        "decision_rule": (
            "advance only if chronology-selected prior player effects beat neutral "
            "on later RE24 runner value"
        ),
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    re24.write_parquet(args.output_root / "run-expectancy.parquet")
    runners.write_parquet(args.output_root / "runner-season-effects.parquet")
    if not pooled.is_empty():
        pooled.write_parquet(args.output_root / "runner-re24-predictions.parquet")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
