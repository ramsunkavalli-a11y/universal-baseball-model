#!/usr/bin/env python
"""Chronologically validate historical MiLB catcher throwing and blocking."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.historical_catcher_pbp import (
    extract_catcher_blocking_opportunities,
    extract_catcher_throwing_attempts,
    fit_crossed_catcher_pitcher_effects,
    score_binary_context_residuals,
)
from universal_baseball.historical_runner_arm import evaluate_effect_projection


REGRESSION_GRID = (0.0, 25.0, 50.0, 100.0, 200.0, 400.0, 800.0, 1200.0)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pbp-catcher-pilot-v1"),
    )
    return parser


def _read_partitions(root: Path, family: str) -> pl.DataFrame:
    paths = sorted(root.glob(f"season=*/level=*/{family}/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no {family} partitions under {root}")
    if family == "terminal":
        columns = [
            "season",
            "level",
            "game_pk",
            "at_bat_index",
            "source_asset",
            "pa_description",
            "fielder_2",
            "pitcher",
            "p_throws",
            "outs_when_up",
            "park_key",
        ]
    else:
        columns = [
            "season",
            "level",
            "game_pk",
            "at_bat_index",
            "pitch_number",
            "source_asset",
            "fielder_2",
            "pitcher",
            "p_throws",
            "stand",
            "balls",
            "strikes",
            "plate_x",
            "plate_z",
            "sz_top",
            "sz_bot",
            "home_team",
            "start_runner_count",
            "outs_continuity_ok",
            "block_candidate",
            "pa_has_passed_ball",
            "pa_has_wild_pitch",
            "clean_block_opportunity",
            "block_result",
        ]
    frame = pl.concat(
        [pl.read_parquet(path, columns=columns) for path in paths],
        how="diagonal_relaxed",
    )
    key = ["game_pk", "at_bat_index"]
    if family == "catcher_pitches":
        key.append("pitch_number")
    return frame.sort([*key, "source_asset"]).unique(
        subset=key, keep="first", maintain_order=True
    )


def _evaluate_nested(
    effects: pl.DataFrame,
    *,
    minimum_target_opportunities: int,
    minimum_prior_pairs: int,
    regression_grid: tuple[float, ...] = REGRESSION_GRID,
) -> tuple[list[pl.DataFrame], list[dict[str, Any]], dict[str, Any]]:
    years = sorted(effects.get_column("season").unique().to_list())
    pairs: dict[tuple[int, float], pl.DataFrame] = {}
    for year in years:
        for regression in regression_grid:
            paired, _ = evaluate_effect_projection(
                effects,
                target_season=int(year),
                regression_opportunities=regression,
                minimum_target_opportunities=minimum_target_opportunities,
            )
            pairs[(int(year), regression)] = paired
    selected: list[pl.DataFrame] = []
    decisions: list[dict[str, Any]] = []
    for year in years:
        choices = []
        for regression in regression_grid:
            older = [
                frame
                for (old, candidate), frame in pairs.items()
                if old < year and candidate == regression and not frame.is_empty()
            ]
            if not older:
                continue
            pooled = pl.concat(older, how="diagonal_relaxed")
            if pooled.height < minimum_prior_pairs:
                continue
            choices.append(
                (
                    float(pooled.get_column("candidate_error").pow(2).sum()),
                    regression,
                    int(pooled.height),
                )
            )
        if not choices:
            continue
        prior_sse, regression, prior_count = min(choices)
        frame = pairs[(year, regression)]
        if frame.is_empty():
            continue
        selected.append(
            frame.with_columns(
                pl.lit(year).alias("target_season"),
                pl.lit(regression).alias("selected_regression_opportunities"),
            )
        )
        decisions.append(
            {
                "target_season": year,
                "selected_regression_opportunities": regression,
                "prior_selection_player_count": prior_count,
                "evaluation_player_count": int(frame.height),
            }
        )
    if not selected:
        return selected, decisions, {"player_test_count": 0}
    pooled = pl.concat(selected, how="diagonal_relaxed")
    row = pooled.select(
        pl.len().alias("player_test_count"),
        pl.col("candidate_error").pow(2).mean().sqrt().alias("candidate_rmse"),
        pl.col("neutral_error").pow(2).mean().sqrt().alias("neutral_rmse"),
        pl.corr("projected_effect", "actual_effect").alias("correlation"),
    ).row(0, named=True)
    metrics = {
        "player_test_count": int(row["player_test_count"]),
        "candidate_rmse": float(row["candidate_rmse"]),
        "neutral_rmse": float(row["neutral_rmse"]),
        "rmse_change": float(row["candidate_rmse"] - row["neutral_rmse"]),
        "correlation": float(row["correlation"]),
    }
    return selected, decisions, metrics


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Historical MiLB catcher PBP pilot",
        "",
        f"- Throwing attempts found: {report['throwing_attempt_count']:,}",
        f"- Caught-stealing share: {report['caught_stealing_share']:.1%}",
        f"- Clean dirt-ball opportunities: {report['blocking_opportunity_count']:,}",
        f"- Recorded WP/PB failures: {report['blocking_failure_count']:,}",
        f"- Years: {report['years']}",
        "- 2026 accessed: **false**",
        "",
    ]
    for label, direction in (
        ("throwing", "positive is better"),
        ("blocking", "negative is better"),
    ):
        metrics = report[f"{label}_pooled_metrics"]
        lines.extend([f"## {label.title()} ({direction})", ""])
        if metrics.get("player_test_count"):
            lines.extend(
                [
                    f"- Later-season catcher tests: {metrics['player_test_count']:,}",
                    f"- Candidate RMSE: {metrics['candidate_rmse']:.6f}",
                    f"- Neutral RMSE: {metrics['neutral_rmse']:.6f}",
                    f"- RMSE change: {metrics['rmse_change']:+.6f}",
                    f"- Correlation: {metrics['correlation']:.4f}",
                ]
            )
        else:
            lines.append("- Not enough repeat catcher samples for nested validation.")
        lines.append("")
    lines.extend(
        [
            "## Boundary",
            "",
            "Throwing currently models success after an attempt. Deterrence still needs an",
            "attempt-rate denominator, and blocking labels are conservative one-dirt-ball",
            "plays. Neither component is ready for WAR promotion from this pilot alone.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = _parser().parse_args()
    terminal = _read_partitions(args.input_root, "terminal")
    pitches = _read_partitions(args.input_root, "catcher_pitches")

    throwing = extract_catcher_throwing_attempts(terminal)
    throwing_scored = score_binary_context_residuals(
        throwing,
        outcome_column="caught_stealing",
        context_columns=["attempt_base", "pitcher_hand", "outs_before"],
        context_prior=40,
        park_prior=80,
    )
    throwing_catchers, _ = fit_crossed_catcher_pitcher_effects(
        throwing_scored, catcher_prior=20, pitcher_prior=30
    )

    blocking = extract_catcher_blocking_opportunities(pitches)
    blocking_scored = score_binary_context_residuals(
        blocking,
        outcome_column="block_failure",
        context_columns=[
            "start_runner_count",
            "balls",
            "strikes",
            "pitcher_hand",
            "batter_side",
        ],
        context_prior=80,
        park_prior=120,
    )
    blocking_catchers, _ = fit_crossed_catcher_pitcher_effects(
        blocking_scored, catcher_prior=100, pitcher_prior=100
    )

    throwing_selected, throwing_decisions, throwing_metrics = _evaluate_nested(
        throwing_catchers,
        minimum_target_opportunities=4,
        minimum_prior_pairs=15,
    )
    blocking_selected, blocking_decisions, blocking_metrics = _evaluate_nested(
        blocking_catchers,
        minimum_target_opportunities=20,
        minimum_prior_pairs=15,
    )
    report = {
        "report_schema_version": "0.1",
        "component": "historical_milb_catcher_pbp_pilot",
        "data_scope": "all nonempty materialized public 2016-2024 MiLB PBP partitions",
        "years": sorted(terminal.get_column("season").unique().to_list()),
        "throwing_attempt_count": int(throwing.height),
        "caught_stealing_share": float(throwing.get_column("caught_stealing").mean()),
        "blocking_opportunity_count": int(blocking.height),
        "blocking_failure_count": int(blocking.get_column("block_failure").sum()),
        "throwing_nested_selection": throwing_decisions,
        "blocking_nested_selection": blocking_decisions,
        "throwing_pooled_metrics": throwing_metrics,
        "blocking_pooled_metrics": blocking_metrics,
        "protected_2026_accessed": False,
        "promotion_decision": "pilot_only_pending_deterrence_full_history_and_WAR_validation",
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    (args.output_root / "report.md").write_text(_markdown(report), encoding="utf-8")
    if throwing_selected:
        pl.concat(throwing_selected, how="diagonal_relaxed").write_parquet(
            args.output_root / "throwing_nested_predictions.parquet"
        )
    if blocking_selected:
        pl.concat(blocking_selected, how="diagonal_relaxed").write_parquet(
            args.output_root / "blocking_nested_predictions.parquet"
        )
    print(_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
