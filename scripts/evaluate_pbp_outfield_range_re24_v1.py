#!/usr/bin/env python3
"""Convert MiLB outfield range residuals to RE24 runs and validate persistence."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from evaluate_pbp_infield_range_re24_v1 import (
    _all_pairs,
    _load_fielding,
    _load_terminal,
    _nested_select,
)
from universal_baseball.historical_fielding_range import (
    score_visitor_anchored_park_fielding_residuals,
)
from universal_baseball.historical_fielding_value import (
    add_contextual_fielding_runs,
    add_terminal_re24_change,
    aggregate_player_fielding_run_seasons,
)
from universal_baseball.historical_runner_arm import build_run_expectancy_table
from universal_baseball.hitter_target_architecture import paired_cluster_rmse_delta
from universal_baseball.storage import write_canonical_parquet


OUTFIELD_POSITIONS = (7, 8, 9)
OUTFIELD_CONTACTS = ("fly_ball", "line_drive")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--game-context",
        type=Path,
        default=Path(
            "reports/generated/defensive-venue-context-v1/"
            "affiliated-game-context.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pbp-outfield-range-re24-v1"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    print("loading outfield and terminal plays", flush=True)
    fielding = _load_fielding(args.input_root, args.game_context)
    terminal = _load_terminal(args.input_root)
    print("building play-level RE24 outfield values", flush=True)
    re24 = build_run_expectancy_table(terminal)
    terminal_values = add_terminal_re24_change(terminal, re24)
    scored = score_visitor_anchored_park_fielding_residuals(
        fielding,
        positions=OUTFIELD_POSITIONS,
        batted_ball_types=OUTFIELD_CONTACTS,
    )
    valued = add_contextual_fielding_runs(scored, terminal_values)
    seasons = aggregate_player_fielding_run_seasons(valued)
    print("running nested chronological projection", flush=True)
    selected, decisions = _nested_select(_all_pairs(seasons))
    pooled = pl.concat(selected) if selected else pl.DataFrame()
    if pooled.is_empty():
        raise RuntimeError("no outfield run-value projection folds")
    candidate_rmse = float(pooled["candidate_error"].pow(2).mean()) ** 0.5
    neutral_rmse = float(pooled["neutral_error"].pow(2).mean()) ** 0.5
    report = {
        "schema_version": "0.1",
        "status": "pbp_outfield_range_re24_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "measurement_model": (
            "visitor-anchored park-adjusted expected outs on fly balls and line "
            "drives, multiplied by the local RE24 difference between an out and non-out"
        ),
        "terminal_plays": terminal.height,
        "outfield_opportunities": valued.height,
        "player_position_seasons": seasons.height,
        "mean_out_run_swing": float(valued["out_run_swing"].mean()),
        "nested_selection": decisions,
        "pooled": {
            "player_position_tests": pooled.height,
            "candidate_rmse_runs_per_opportunity": candidate_rmse,
            "neutral_rmse_runs_per_opportunity": neutral_rmse,
            "rmse_change": candidate_rmse - neutral_rmse,
            "correlation": float(
                pooled.select(
                    pl.corr(
                        "projected_range_runs_per_opportunity", "actual_run_rate"
                    )
                ).item()
            ),
            "player_clustered_rmse_change": paired_cluster_rmse_delta(
                pooled["actual_run_rate"].to_numpy(),
                pooled["projected_range_runs_per_opportunity"].to_numpy(),
                pl.Series("neutral", [0.0] * pooled.height).to_numpy(),
                pooled["responsible_fielder_id"].to_numpy(),
                bootstrap_samples=5_000,
            ),
        },
        "decision_rule": (
            "advance to hitter-value integration only if the chronology-selected "
            "run-rate projection beats neutral with favorable clustered uncertainty"
        ),
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    report["artifacts"] = {
        "season_effects": write_canonical_parquet(
            seasons,
            args.output_root / "player-position-season-effects.parquet",
            table_name="pbp_outfield_range_re24_player_position_seasons",
        ).as_record(),
        "predictions": write_canonical_parquet(
            pooled,
            args.output_root / "nested-predictions.parquet",
            table_name="pbp_outfield_range_re24_nested_predictions",
        ).as_record(),
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
