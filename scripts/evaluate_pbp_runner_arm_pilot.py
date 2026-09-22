#!/usr/bin/env python
"""Chronologically validate joint PBP runner and outfielder-arm effects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.historical_runner_arm import (
    evaluate_effect_projection,
    fit_crossed_runner_arm_effects,
    score_contextual_advancement_residuals,
)


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
        default=Path("reports/generated/pbp-runner-arm-pilot-v1"),
    )
    parser.add_argument("--minimum-runner-target-opportunities", type=int, default=8)
    parser.add_argument("--minimum-arm-target-opportunities", type=int, default=10)
    return parser


def _load(root: Path) -> pl.DataFrame:
    paths = sorted(root.glob("season=*/level=*/runners/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no runner opportunity partitions under {root}")
    columns = [
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "source_asset",
        "runner_id",
        "responsible_fielder_id",
        "responsible_position",
        "opportunity_type",
        "origin_base",
        "destination_base",
        "outfield_arm_context",
        "outs_when_up",
        "bb_type",
        "hit_location",
        "stand",
        "p_throws",
        "park_key",
    ]
    frames = []
    for path in paths:
        available = set(pl.scan_parquet(path).collect_schema().names())
        frame = pl.read_parquet(
            path, columns=[column for column in columns if column in available]
        )
        if "outfield_arm_context" not in frame.columns:
            frame = frame.with_columns(
                pl.lit(None, dtype=pl.Boolean).alias("outfield_arm_context")
            )
        frames.append(frame)
    return (
        pl.concat(frames, how="diagonal_relaxed")
        .sort(["game_pk", "at_bat_index", "origin_base", "source_asset"])
        .unique(
            subset=["game_pk", "at_bat_index", "runner_id", "origin_base"],
            keep="first",
            maintain_order=True,
        )
    )


def _all_folds(
    effects: pl.DataFrame,
    *,
    minimum_target_opportunities: int,
) -> dict[tuple[int, float], pl.DataFrame]:
    years = sorted(effects.get_column("season").unique().to_list())
    result: dict[tuple[int, float], pl.DataFrame] = {}
    for year in years:
        for regression in REGRESSION_GRID:
            paired, _ = evaluate_effect_projection(
                effects,
                target_season=int(year),
                regression_opportunities=regression,
                minimum_target_opportunities=minimum_target_opportunities,
            )
            result[(int(year), regression)] = paired
    return result


def _select_nested(
    pairs: dict[tuple[int, float], pl.DataFrame],
    *,
    minimum_prior_pairs: int,
) -> tuple[list[pl.DataFrame], list[dict[str, Any]]]:
    years = sorted({year for year, _ in pairs})
    selected: list[pl.DataFrame] = []
    decisions: list[dict[str, Any]] = []
    for year in years:
        choices = []
        for regression in REGRESSION_GRID:
            history = [
                frame
                for (old_year, candidate), frame in pairs.items()
                if old_year < year and candidate == regression and not frame.is_empty()
            ]
            if not history:
                continue
            pooled = pl.concat(history, how="diagonal_relaxed")
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
                "prior_selection_sse": prior_sse,
                "evaluation_player_count": int(frame.height),
            }
        )
    return selected, decisions


def _pooled(frames: list[pl.DataFrame]) -> dict[str, Any]:
    if not frames:
        return {"player_test_count": 0}
    pooled = pl.concat(frames, how="diagonal_relaxed")
    row = pooled.select(
        pl.len().alias("player_test_count"),
        pl.col("candidate_error").pow(2).mean().sqrt().alias("candidate_rmse"),
        pl.col("neutral_error").pow(2).mean().sqrt().alias("neutral_rmse"),
        pl.corr("projected_effect", "actual_effect").alias("correlation"),
    ).row(0, named=True)
    return {
        "player_test_count": int(row["player_test_count"]),
        "candidate_rmse": float(row["candidate_rmse"]),
        "neutral_rmse": float(row["neutral_rmse"]),
        "rmse_change": float(row["candidate_rmse"] - row["neutral_rmse"]),
        "correlation": float(row["correlation"]),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# PBP runner and outfielder-arm pilot",
        "",
        "The model compares each advancement with similar hit, out, park, level and",
        "handedness situations, then jointly separates the runner from the outfielder.",
        "",
        f"- Runner opportunities retained: {report['runner_opportunity_count']:,}",
        f"- Joint outfield opportunities: {report['joint_outfield_opportunity_count']:,}",
        f"- Years: {report['years']}",
        "- 2026 accessed: **false**",
        "",
    ]
    for label in ("runner", "outfield_arm"):
        metrics = report[f"{label}_pooled_metrics"]
        lines.extend([f"## {label.replace('_', ' ').title()}", ""])
        if metrics.get("player_test_count"):
            lines.extend(
                [
                    f"- Later-season player tests: {metrics['player_test_count']:,}",
                    f"- Candidate RMSE: {metrics['candidate_rmse']:.6f}",
                    f"- Neutral RMSE: {metrics['neutral_rmse']:.6f}",
                    f"- RMSE change: {metrics['rmse_change']:+.6f}",
                    f"- Correlation: {metrics['correlation']:.4f}",
                ]
            )
        else:
            lines.append("- Insufficient repeat samples for a nested result.")
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "Negative RMSE change means the prior PBP component beat assuming an average",
            "runner or arm. This uses an ordinal advancement target for the first signal",
            "test; RE24 conversion and full-history validation are still required.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = _parser().parse_args()
    opportunities = _load(args.input_root)
    scored = score_contextual_advancement_residuals(opportunities)
    runners, arms = fit_crossed_runner_arm_effects(scored)
    runner_pairs = _all_folds(
        runners,
        minimum_target_opportunities=args.minimum_runner_target_opportunities,
    )
    arm_pairs = _all_folds(
        arms,
        minimum_target_opportunities=args.minimum_arm_target_opportunities,
    )
    runner_selected, runner_decisions = _select_nested(
        runner_pairs, minimum_prior_pairs=25
    )
    arm_selected, arm_decisions = _select_nested(
        arm_pairs, minimum_prior_pairs=15
    )
    report = {
        "report_schema_version": "0.1",
        "component": "joint_pbp_runner_outfielder_arm_pilot",
        "data_scope": "all nonempty materialized public 2016-2024 MiLB PBP partitions",
        "years": sorted(scored.get_column("season").unique().to_list()),
        "runner_opportunity_count": int(scored.height),
        "joint_outfield_opportunity_count": int(runners.get_column("opportunities").sum())
        if runners.height
        else 0,
        "runner_nested_selection": runner_decisions,
        "outfield_arm_nested_selection": arm_decisions,
        "runner_pooled_metrics": _pooled(runner_selected),
        "outfield_arm_pooled_metrics": _pooled(arm_selected),
        "mean_absolute_park_adjustment": float(
            scored.get_column("park_advancement_adjustment").abs().mean()
        ),
        "protected_2026_accessed": False,
        "promotion_decision": "pilot_only_pending_RE24_and_full_history_validation",
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    (args.output_root / "report.md").write_text(_markdown(report), encoding="utf-8")
    if runner_selected:
        pl.concat(runner_selected, how="diagonal_relaxed").write_parquet(
            args.output_root / "runner_nested_predictions.parquet"
        )
    if arm_selected:
        pl.concat(arm_selected, how="diagonal_relaxed").write_parquet(
            args.output_root / "arm_nested_predictions.parquet"
        )
    print(_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
