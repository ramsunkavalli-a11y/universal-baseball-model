#!/usr/bin/env python
"""Evaluate all-level catcher battery support on later affiliated seasons."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from universal_baseball.historical_battery_support import (
    classify_battery_plate_appearances,
    fit_crossed_battery_effects,
)
from universal_baseball.historical_runner_arm import (
    evaluate_effect_projection,
    project_effects,
)


REGRESSION_GRID = (0.0, 250.0, 500.0, 1_000.0, 2_000.0, 4_000.0, 8_000.0, 16_000.0)
OUTCOMES = {
    "control_failure": {
        "catcher_prior": 2_000.0,
        "minimum_target_opportunities": 150,
    },
    "unintentional_walk": {
        "catcher_prior": 2_000.0,
        "minimum_target_opportunities": 150,
    },
    "hit_by_pitch": {
        "catcher_prior": 4_000.0,
        "minimum_target_opportunities": 150,
    },
    "defense_independent_run_value": {
        "catcher_prior": 4_000.0,
        "minimum_target_opportunities": 150,
    },
}


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
        default=Path("reports/generated/catcher-battery-support-v1"),
    )
    return parser


def _read_terminal(root: Path) -> pl.DataFrame:
    paths = sorted(root.glob("season=*/level=*/terminal/*.parquet"))
    if not paths:
        raise FileNotFoundError(f"no terminal partitions under {root}")
    columns = [
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "batter",
        "pitcher",
        "fielder_2",
        "stand",
        "p_throws",
        "park_key",
        "bb_type",
        "pa_description",
        "terminal_outcome_group",
        "terminal_outcome_status",
        "source_asset",
    ]
    frame = pl.concat(
        [pl.read_parquet(path, columns=columns) for path in paths],
        how="diagonal_relaxed",
    )
    return frame.sort("game_pk", "at_bat_index", "source_asset").unique(
        subset=["game_pk", "at_bat_index"], keep="first", maintain_order=True
    )


def _cluster_interval(paired: pl.DataFrame, *, seed: int = 20260921) -> list[float]:
    if paired.is_empty():
        return [float("nan"), float("nan")]
    grouped = paired.group_by("player_id").agg(
        pl.col("candidate_error").pow(2).sum().alias("candidate_sse"),
        pl.col("neutral_error").pow(2).sum().alias("neutral_sse"),
        pl.len().alias("n"),
    )
    candidate = grouped.get_column("candidate_sse").to_numpy()
    neutral = grouped.get_column("neutral_sse").to_numpy()
    counts = grouped.get_column("n").to_numpy()
    rng = np.random.default_rng(seed)
    changes = np.empty(2_000, dtype=float)
    for index in range(changes.size):
        draw = rng.integers(0, grouped.height, size=grouped.height)
        n = counts[draw].sum()
        changes[index] = np.sqrt(candidate[draw].sum() / n) - np.sqrt(
            neutral[draw].sum() / n
        )
    return [float(value) for value in np.quantile(changes, [0.025, 0.975])]


def _nested_projection(
    effects: pl.DataFrame,
    *,
    minimum_target_opportunities: int,
) -> tuple[pl.DataFrame, list[dict[str, Any]], dict[str, Any]]:
    years = sorted(int(value) for value in effects.get_column("season").unique())
    pairs: dict[tuple[int, float], pl.DataFrame] = {}
    for year in years:
        for regression in REGRESSION_GRID:
            paired, _ = evaluate_effect_projection(
                effects,
                target_season=year,
                regression_opportunities=regression,
                minimum_target_opportunities=minimum_target_opportunities,
            )
            pairs[(year, regression)] = paired

    selected: list[pl.DataFrame] = []
    decisions: list[dict[str, Any]] = []
    for year in years:
        choices: list[tuple[float, float, int]] = []
        for regression in REGRESSION_GRID:
            prior = [
                frame
                for (old_year, candidate), frame in pairs.items()
                if old_year < year and candidate == regression and not frame.is_empty()
            ]
            if not prior:
                continue
            pooled = pl.concat(prior, how="diagonal_relaxed")
            if pooled.height < 30:
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
        _, regression, prior_count = min(choices)
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
        return pl.DataFrame(), decisions, {"player_test_count": 0}
    pooled = pl.concat(selected, how="diagonal_relaxed")
    metrics = pooled.select(
        pl.len().alias("player_test_count"),
        pl.col("candidate_error").pow(2).mean().sqrt().alias("candidate_rmse"),
        pl.col("neutral_error").pow(2).mean().sqrt().alias("neutral_rmse"),
        pl.corr("projected_effect", "actual_effect").alias("correlation"),
    ).row(0, named=True)
    result = {
        "player_test_count": int(metrics["player_test_count"]),
        "candidate_rmse": float(metrics["candidate_rmse"]),
        "neutral_rmse": float(metrics["neutral_rmse"]),
        "rmse_change": float(metrics["candidate_rmse"] - metrics["neutral_rmse"]),
        "correlation": float(metrics["correlation"]),
        "cluster_95_interval_rmse_change": _cluster_interval(pooled),
    }
    return pooled, decisions, result


def _pair_projection(pairs: pl.DataFrame) -> dict[str, Any]:
    pair_keys = pairs.select("pair_id").unique().with_row_index("player_id")
    effects = pairs.join(pair_keys, on="pair_id", validate="m:1").select(
        "season",
        pl.col("player_id").cast(pl.Int64),
        pl.col("pair_opportunities").alias("opportunities"),
        pl.col("pair_effect").alias("effect"),
    )
    pooled, _, metrics = _nested_projection(
        effects, minimum_target_opportunities=75
    )
    metrics["interpretation"] = (
        "repeat-pair chemistry only; it is not transferable catcher talent"
    )
    metrics["paired_rows_written"] = int(pooled.height)
    return metrics


def _new_pitcher_projection(
    fit: Any,
    *,
    catcher_prior: float,
    decisions: list[dict[str, Any]],
    minimum_target_opportunities: int,
) -> dict[str, Any]:
    """Test prior catcher estimates only on pitchers new to that catcher."""

    first_pair_season = fit.cells.group_by("pair_id").agg(
        pl.col("season").min().alias("first_pair_season")
    )
    new_pair_cells = (
        fit.cells.join(first_pair_season, on="pair_id", validate="m:1")
        .filter(pl.col("season") == pl.col("first_pair_season"))
        .with_columns(
            (
                pl.col("outcome_sum")
                - pl.col("baseline_sum")
                - pl.col("opportunities")
                * (pl.col("pitcher_effect") + pl.col("batter_effect"))
            ).alias("catcher_numerator")
        )
        .group_by("season", "catcher_id")
        .agg(
            pl.col("opportunities").sum().alias("opportunities"),
            pl.col("catcher_numerator").sum().alias("catcher_numerator"),
        )
        .with_columns(
            (
                pl.col("catcher_numerator")
                / (pl.col("opportunities") + float(catcher_prior))
            ).alias("effect")
        )
        .rename({"catcher_id": "player_id"})
    )
    centers = new_pair_cells.group_by("season").agg(
        (
            (pl.col("effect") * pl.col("opportunities")).sum()
            / pl.col("opportunities").sum()
        ).alias("center")
    )
    targets = (
        new_pair_cells.join(centers, on="season", validate="m:1")
        .with_columns((pl.col("effect") - pl.col("center")).alias("effect"))
        .drop("center", "catcher_numerator")
    )

    selected: list[pl.DataFrame] = []
    for decision in decisions:
        year = int(decision["target_season"])
        regression = float(decision["selected_regression_opportunities"])
        projected = project_effects(
            fit.catchers,
            target_season=year,
            regression_opportunities=regression,
        )
        target = targets.filter(
            (pl.col("season") == year)
            & (pl.col("opportunities") >= minimum_target_opportunities)
        ).select(
            "player_id",
            pl.col("opportunities").alias("target_opportunities"),
            pl.col("effect").alias("actual_effect"),
        )
        paired = target.join(projected, on="player_id", how="inner", validate="1:1")
        if paired.is_empty():
            continue
        selected.append(
            paired.with_columns(
                (pl.col("projected_effect") - pl.col("actual_effect")).alias(
                    "candidate_error"
                ),
                (-pl.col("actual_effect")).alias("neutral_error"),
                pl.lit(year).alias("target_season"),
            )
        )
    if not selected:
        return {"player_test_count": 0}
    pooled = pl.concat(selected, how="diagonal_relaxed")
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
        "cluster_95_interval_rmse_change": _cluster_interval(pooled, seed=20260922),
        "target_definition": "first observed season of each pitcher-catcher pair",
    }


def _dominant_catcher_levels(plate_appearances: pl.DataFrame) -> pl.DataFrame:
    return (
        plate_appearances.group_by("season", "catcher_id", "level")
        .agg(pl.len().alias("level_opportunities"))
        .sort(
            "season",
            "catcher_id",
            "level_opportunities",
            "level",
            descending=[False, False, True, False],
        )
        .unique(subset=["season", "catcher_id"], keep="first", maintain_order=True)
        .rename({"catcher_id": "player_id", "level": "target_level"})
    )


def _projection_segments(
    pooled: pl.DataFrame,
    dominant_levels: pl.DataFrame,
) -> dict[str, list[dict[str, Any]]]:
    if pooled.is_empty():
        return {"target_level": [], "level_transition": []}
    level_rows = dominant_levels.select(
        "season", "player_id", "target_level"
    ).to_dicts()
    lookup = {
        (int(row["player_id"]), int(row["season"])): str(row["target_level"])
        for row in level_rows
    }
    history: dict[int, list[tuple[int, str]]] = {}
    for row in level_rows:
        history.setdefault(int(row["player_id"]), []).append(
            (int(row["season"]), str(row["target_level"]))
        )
    level_rank = {"rk": 0, "a-": 1, "a": 2, "a+": 3, "aa": 4, "aaa": 5}
    enriched = []
    for row in pooled.to_dicts():
        player_id = int(row["player_id"])
        target_season = int(row["target_season"])
        target_level = lookup.get((player_id, target_season))
        prior = [
            (season, level)
            for season, level in history.get(player_id, [])
            if season < target_season
        ]
        prior_level = max(prior)[1] if prior else None
        if target_level is None or prior_level is None:
            transition = "unknown"
        else:
            difference = level_rank.get(target_level, -99) - level_rank.get(
                prior_level, -99
            )
            transition = (
                "advanced" if difference > 0 else "same" if difference == 0 else "down"
            )
        enriched.append(
            {**row, "target_level": target_level or "unknown", "level_transition": transition}
        )
    frame = pl.DataFrame(enriched)

    def summarize(column: str) -> list[dict[str, Any]]:
        results = []
        for value in sorted(frame.get_column(column).unique().to_list()):
            cell = frame.filter(pl.col(column) == value)
            row = cell.select(
                pl.len().alias("player_test_count"),
                pl.col("candidate_error").pow(2).mean().sqrt().alias("candidate_rmse"),
                pl.col("neutral_error").pow(2).mean().sqrt().alias("neutral_rmse"),
                pl.corr("projected_effect", "actual_effect").alias("correlation"),
            ).row(0, named=True)
            results.append(
                {
                    column: value,
                    "player_test_count": int(row["player_test_count"]),
                    "rmse_change": float(row["candidate_rmse"] - row["neutral_rmse"]),
                    "correlation": None
                    if row["correlation"] is None
                    else float(row["correlation"]),
                }
            )
        return results

    return {
        "target_level": summarize("target_level"),
        "level_transition": summarize("level_transition"),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# All-level catcher battery-support screen",
        "",
        f"- Completed non-intentional PAs: {report['eligible_plate_appearances']:,}",
        f"- Catcher identity coverage: {report['catcher_identity_coverage']:.6%}",
        f"- Seasons: {report['seasons']}",
        f"- Levels: {report['levels']}",
        "- 2020 MiLB season: not played",
        "- 2026 outcomes accessed: **false**",
        "",
        "The model compares catcher results after simultaneous shrinkage for pitcher and",
        "batter, plus level-season, handedness and park context. Lower effects are better.",
        "Pitcher-catcher pair chemistry is measured separately.",
        "",
    ]
    for outcome in OUTCOMES:
        metrics = report["outcomes"][outcome]["catcher_projection"]
        pair = report["outcomes"][outcome]["pair_projection"]
        new_pitcher = report["outcomes"][outcome]["new_pitcher_projection"]
        segments = report["outcomes"][outcome]["projection_segments"]
        lines.extend(
            [
                f"## {outcome.replace('_', ' ').title()}",
                "",
                f"- Later-season catcher tests: {metrics['player_test_count']:,}",
                f"- Candidate RMSE: {metrics['candidate_rmse']:.8f}",
                f"- Neutral RMSE: {metrics['neutral_rmse']:.8f}",
                f"- RMSE change: {metrics['rmse_change']:+.8f}",
                f"- Catcher year-to-year correlation: {metrics['correlation']:.4f}",
                "- Player-clustered 95% interval for RMSE change: "
                f"[{metrics['cluster_95_interval_rmse_change'][0]:+.8f}, "
                f"{metrics['cluster_95_interval_rmse_change'][1]:+.8f}]",
                f"- Repeat-pair tests: {pair.get('player_test_count', 0):,}",
                f"- New-pitcher catcher tests: {new_pitcher.get('player_test_count', 0):,}",
            ]
        )
        if pair.get("player_test_count"):
            lines.extend(
                [
                    f"- Pair RMSE change: {pair['rmse_change']:+.8f}",
                    f"- Pair year-to-year correlation: {pair['correlation']:.4f}",
                ]
            )
        if new_pitcher.get("player_test_count"):
            lines.extend(
                [
                    f"- New-pitcher RMSE change: {new_pitcher['rmse_change']:+.8f}",
                    f"- New-pitcher correlation: {new_pitcher['correlation']:.4f}",
                    "- New-pitcher 95% interval: "
                    f"[{new_pitcher['cluster_95_interval_rmse_change'][0]:+.8f}, "
                    f"{new_pitcher['cluster_95_interval_rmse_change'][1]:+.8f}]",
                ]
            )
        lines.append("- By level transition: " + ", ".join(
            f"{row['level_transition']} {row['rmse_change']:+.8f} (n={row['player_test_count']:,})"
            for row in segments["level_transition"]
        ))
        lines.append("")
    lines.extend(
        [
            "## Interpretation boundary",
            "",
            "This can detect transferable catcher-associated support and recurring pair",
            "chemistry. It cannot identify who selected a pitch or where the catcher set",
            "the target. No result is promoted to catcher WAR unless it improves a later",
            "whole-player projection test.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = _parser().parse_args()
    terminal = _read_terminal(args.input_root)
    catcher_identity_coverage = float(terminal.get_column("fielder_2").is_not_null().mean())
    plate_appearances = classify_battery_plate_appearances(terminal)
    coverage = (
        plate_appearances.group_by("season", "level")
        .agg(
            pl.len().alias("plate_appearances"),
            pl.col("catcher_id").n_unique().alias("catchers"),
            pl.col("pitcher_id").n_unique().alias("pitchers"),
        )
        .sort("season", "level")
    )

    report: dict[str, Any] = {
        "report_schema_version": "0.1",
        "component": "all_level_catcher_battery_support_v1",
        "eligible_plate_appearances": int(plate_appearances.height),
        "source_terminal_rows": int(terminal.height),
        "catcher_identity_coverage": catcher_identity_coverage,
        "seasons": sorted(plate_appearances.get_column("season").unique().to_list()),
        "levels": sorted(plate_appearances.get_column("level").unique().to_list()),
        "outcomes": {},
        "protected_2026_accessed": False,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    coverage.write_parquet(args.output_root / "coverage.parquet")
    dominant_levels = _dominant_catcher_levels(plate_appearances)
    dominant_levels.write_parquet(args.output_root / "catcher-dominant-levels.parquet")

    for outcome, config in OUTCOMES.items():
        fit = fit_crossed_battery_effects(
            plate_appearances,
            outcome_column=outcome,
            catcher_prior=float(config["catcher_prior"]),
        )
        pooled, decisions, metrics = _nested_projection(
            fit.catchers,
            minimum_target_opportunities=int(config["minimum_target_opportunities"]),
        )
        outcome_root = args.output_root / outcome
        outcome_root.mkdir(parents=True, exist_ok=True)
        fit.catchers.write_parquet(outcome_root / "catcher-season-effects.parquet")
        fit.pairs.write_parquet(outcome_root / "battery-pair-season-effects.parquet")
        if not pooled.is_empty():
            pooled.write_parquet(outcome_root / "nested-catcher-predictions.parquet")
        report["outcomes"][outcome] = {
            "catcher_prior_opportunities": config["catcher_prior"],
            "nested_selection": decisions,
            "catcher_projection": metrics,
            "pair_projection": _pair_projection(fit.pairs),
            "new_pitcher_projection": _new_pitcher_projection(
                fit,
                catcher_prior=float(config["catcher_prior"]),
                decisions=decisions,
                minimum_target_opportunities=int(
                    config["minimum_target_opportunities"]
                ),
            ),
            "projection_segments": _projection_segments(pooled, dominant_levels),
        }

    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    markdown = _markdown(report)
    (args.output_root / "report.md").write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
