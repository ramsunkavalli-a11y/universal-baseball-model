#!/usr/bin/env python3
"""Convert MiLB infield range residuals to RE24 runs and validate persistence."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.historical_fielding_range import (
    score_visitor_anchored_park_fielding_residuals,
)
from universal_baseball.historical_fielding_value import (
    add_contextual_fielding_runs,
    add_terminal_re24_change,
    aggregate_player_fielding_run_seasons,
    evaluate_fielding_run_projection,
)
from universal_baseball.historical_runner_arm import build_run_expectancy_table
from universal_baseball.hitter_target_architecture import paired_cluster_rmse_delta
from universal_baseball.storage import write_canonical_parquet


REGRESSION_GRID = (400.0, 800.0, 1200.0, 2000.0, 3000.0)
DEFAULT_REGRESSION = 1200.0


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
        default=Path("reports/generated/pbp-infield-range-re24-v1"),
    )
    return parser.parse_args()


def _load_parts(root: Path, kind: str, columns: list[str]) -> pl.DataFrame:
    paths = sorted(root.glob(f"season=*/level=*/{kind}/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no {kind} partitions under {root}")
    return pl.concat(
        [pl.read_parquet(path, columns=columns) for path in paths],
        how="diagonal_relaxed",
    )


def _load_terminal(root: Path) -> pl.DataFrame:
    columns = [
        "season",
        "level",
        "source_asset",
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
    return (
        _load_parts(root, "terminal", columns)
        .sort("game_pk", "at_bat_index", "source_asset")
        .unique(subset=["game_pk", "at_bat_index"], keep="first", maintain_order=True)
    )


def _load_fielding(root: Path, game_context: Path) -> pl.DataFrame:
    columns = [
        "season",
        "level",
        "source_asset",
        "game_pk",
        "at_bat_index",
        "responsible_position",
        "responsible_fielder_id",
        "conversion_out",
        "bb_type",
        "stand",
        "p_throws",
        "park_key",
        "defense_team",
        "home_team",
        "batter",
        "hc_x",
        "hc_y",
        "outs_when_up",
        "start_runner_1b",
        "start_runner_2b",
        "start_runner_3b",
    ]
    frame = (
        _load_parts(root, "fielding", columns)
        .sort("game_pk", "at_bat_index", "source_asset")
        .unique(subset=["game_pk", "at_bat_index"], keep="first", maintain_order=True)
    )
    if game_context.exists():
        context = pl.read_parquet(
            game_context, columns=["game_pk", "venue_id"]
        ).unique(subset=["game_pk"], keep="none")
        frame = frame.join(context, on="game_pk", how="left", validate="m:1").with_columns(
            pl.when(pl.col("venue_id").is_not_null())
            .then(
                pl.concat_str(
                    [pl.col("season"), pl.lit("venue"), pl.col("venue_id")],
                    separator=":",
                )
            )
            .otherwise(pl.col("park_key"))
            .alias("park_key")
        )
    return frame


def _all_pairs(
    seasons: pl.DataFrame,
) -> dict[tuple[int, float], tuple[pl.DataFrame, dict[str, Any]]]:
    pairs = {}
    years = sorted(seasons["season"].unique().to_list())
    for year in years:
        if not any(old < year for old in years):
            continue
        for regression in REGRESSION_GRID:
            paired, metrics = evaluate_fielding_run_projection(
                seasons,
                target_season=int(year),
                regression_opportunities=regression,
                minimum_target_opportunities=25,
            )
            if not paired.is_empty():
                pairs[(int(year), regression)] = (paired, metrics)
    return pairs


def _nested_select(
    pairs: dict[tuple[int, float], tuple[pl.DataFrame, dict[str, Any]]],
) -> tuple[list[pl.DataFrame], list[dict[str, Any]]]:
    target_years = sorted({year for year, _ in pairs})
    selected = []
    decisions = []
    for target_year in target_years:
        choices = []
        for regression in REGRESSION_GRID:
            prior = [
                frame
                for (year, candidate), (frame, _) in pairs.items()
                if year < target_year and candidate == regression
            ]
            if prior:
                pooled = pl.concat(prior)
                choices.append(
                    (
                        float(pooled["candidate_error"].pow(2).sum()),
                        regression,
                        pooled.height,
                    )
                )
        if choices:
            prior_sse, regression, prior_rows = min(choices)
        else:
            regression = DEFAULT_REGRESSION
            prior_sse = None
            prior_rows = 0
        paired, metrics = pairs[(target_year, regression)]
        selected.append(paired.with_columns(pl.lit(target_year).alias("target_season")))
        decisions.append(
            {
                **metrics,
                "selected_regression_opportunities": regression,
                "prior_player_position_rows": prior_rows,
                "prior_candidate_sse": prior_sse,
            }
        )
    return selected, decisions


def main() -> int:
    args = _args()
    print("loading fielding and terminal plays", flush=True)
    fielding = _load_fielding(args.input_root, args.game_context)
    terminal = _load_terminal(args.input_root)
    print("building play-level RE24 range values", flush=True)
    re24 = build_run_expectancy_table(terminal)
    terminal_values = add_terminal_re24_change(terminal, re24)
    scored = score_visitor_anchored_park_fielding_residuals(
        fielding,
        positions=(4, 5, 6),
        batted_ball_types=("ground_ball",),
    )
    valued = add_contextual_fielding_runs(scored, terminal_values)
    seasons = aggregate_player_fielding_run_seasons(valued)
    print("running nested chronological projection", flush=True)
    selected, decisions = _nested_select(_all_pairs(seasons))
    pooled = pl.concat(selected) if selected else pl.DataFrame()
    if pooled.is_empty():
        raise RuntimeError("no infield run-value projection folds")
    candidate_rmse = float(pooled["candidate_error"].pow(2).mean()) ** 0.5
    neutral_rmse = float(pooled["neutral_error"].pow(2).mean()) ** 0.5
    report = {
        "schema_version": "0.1",
        "status": "pbp_infield_range_re24_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "measurement_model": (
            "visitor-anchored park-adjusted expected outs multiplied by the local "
            "RE24 difference between an out and a non-out"
        ),
        "terminal_plays": terminal.height,
        "infield_ground_ball_opportunities": valued.height,
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
            table_name="pbp_infield_range_re24_player_position_seasons",
        ).as_record(),
        "predictions": write_canonical_parquet(
            pooled,
            args.output_root / "nested-predictions.parquet",
            table_name="pbp_infield_range_re24_nested_predictions",
        ).as_record(),
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
