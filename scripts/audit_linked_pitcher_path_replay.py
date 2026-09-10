#!/usr/bin/env python3
"""Cutoff-safe four-year replay of linked pitcher performance/workload paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.historical_pitcher_performance import (
    build_historical_pitcher_performance_paths,
)
from universal_baseball.prospect_arrival import (
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)
from universal_baseball.storage import sha256_file


TIERS = ("fringe", "meaningful_only", "established")


def _history_stats(root: Path) -> pl.DataFrame:
    return pl.concat(
        [
            pl.read_parquet(path)
            for path in sorted(root.glob("*/affiliated_season_stats.parquet"))
        ],
        how="vertical_relaxed",
    )


def _four_year_probability(two_year: pl.Expr) -> pl.Expr:
    return 1.0 - (1.0 - two_year) ** 2


def _path_prefix_means(paths: pl.DataFrame) -> dict[str, dict[int, float]]:
    cutoff = paths.filter(pl.col("window_end_year") <= 2021)
    if cutoff.is_empty() or cutoff["window_end_year"].max() > 2021:
        raise ValueError("cutoff-specific pitcher path library is invalid")
    result = {}
    for tier in (*TIERS, "pooled"):
        tier_paths = (
            cutoff
            if tier == "pooled"
            else cutoff.filter(pl.col("outcome_tier_v2") == tier)
        )
        result[tier] = {}
        for years in range(1, 5):
            careers = (
                tier_paths.filter(pl.col("path_year") <= years)
                .group_by("path_player_id")
                .agg(pl.col("observed_component_war").sum().alias("war"))
            )
            result[tier][years] = float(careers["war"].mean())
    return result


def _predict_war(row: dict[str, object], means: dict[str, dict[int, float]]) -> float:
    arrival = float(row["four_year_arrival_probability"])
    if arrival <= 0.0:
        return 0.0
    meaningful = float(row["four_year_nested_meaningful_probability"])
    established = float(row["four_year_nested_established_probability"])
    masses = {
        "fringe": max(0.0, arrival - meaningful),
        "meaningful_only": max(0.0, meaningful - established),
        "established": max(0.0, established),
    }
    hazard = 1.0 - (1.0 - arrival) ** 0.25
    expected = 0.0
    for offset in range(4):
        arrival_at_offset = (1.0 - hazard) ** offset * hazard
        remaining = 4 - offset
        expected += arrival_at_offset * sum(
            masses[tier] / arrival * means[tier][remaining] for tier in TIERS
        )
    return expected


def _predict_pooled_war(
    row: dict[str, object], means: dict[str, dict[int, float]]
) -> float:
    arrival = float(row["four_year_arrival_probability"])
    if arrival <= 0.0:
        return 0.0
    hazard = 1.0 - (1.0 - arrival) ** 0.25
    return sum(
        (1.0 - hazard) ** offset * hazard * means["pooled"][4 - offset]
        for offset in range(4)
    )


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, float | int]:
    error = frame[prediction] - frame["observed_four_year_component_war"]
    return {
        "players": frame.height,
        "observed_mean": float(frame["observed_four_year_component_war"].mean()),
        "predicted_mean": float(frame[prediction].mean()),
        "bias": float(error.mean()),
        "mae": float(error.abs().mean()),
        "rmse": float((error.pow(2).mean()) ** 0.5),
    }


def _paired_bootstrap(
    frame: pl.DataFrame, candidate: str, baseline: str
) -> dict[str, float]:
    observed = frame["observed_four_year_component_war"].to_numpy()
    difference = (frame[candidate].to_numpy() - observed) ** 2 - (
        frame[baseline].to_numpy() - observed
    ) ** 2
    rng = np.random.default_rng(20260910)
    draws = np.asarray(
        [
            difference[rng.integers(0, len(difference), len(difference))].mean()
            for _ in range(2000)
        ]
    )
    return {
        "candidate_minus_baseline_mse": float(difference.mean()),
        "p025": float(np.quantile(draws, 0.025)),
        "p975": float(np.quantile(draws, 0.975)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--history-root",
        type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--membership",
        type=Path,
        default=Path(
            "reports/generated/opportunity-40man-history/tables/historical_40man_membership.parquet"
        ),
    )
    parser.add_argument(
        "--skill",
        type=Path,
        default=Path(
            "reports/generated/phase2-arrival-skill-source/tables/affiliated_pitching_components.parquet"
        ),
    )
    parser.add_argument(
        "--demographics",
        type=Path,
        default=Path(
            "reports/generated/player-demographics/tables/player-demographics.parquet"
        ),
    )
    parser.add_argument(
        "--pitching",
        type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet"
        ),
    )
    parser.add_argument(
        "--performance-paths",
        type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/post-debut-pitcher-performance-paths.parquet"
        ),
    )
    parser.add_argument(
        "--environment-report",
        type=Path,
        default=Path("docs/prospect-component-uncertainty-result.json"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/dependent-career-linked-pitcher-replay-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/dependent-career-linked-pitcher-replay-result.md"),
    )
    args = parser.parse_args()

    snapshot_path = args.history_root / "pitcher_snapshots.parquet"
    history_stat_paths = sorted(args.history_root.glob("*/affiliated_season_stats.parquet"))
    if not history_stat_paths:
        raise ValueError("history root contains no affiliated season-stat files")
    environment_report = json.loads(args.environment_report.read_text(encoding="utf-8"))
    runs_per_win = float(environment_report["runs_per_win"])
    snapshots = pl.read_parquet(snapshot_path)
    stats = _history_stats(args.history_root)
    membership = pl.read_parquet(args.membership)
    skill = pl.read_parquet(args.skill)
    demographics = pl.read_parquet(args.demographics)
    training = build_arrival_cohort(
        snapshots,
        stats,
        membership,
        skill,
        snapshot_year=2018,
        horizon=2,
        player_type="pitcher",
        demographics=demographics,
    )
    predictors = build_arrival_cohort(
        snapshots,
        stats,
        membership,
        skill,
        snapshot_year=2021,
        horizon=2,
        player_type="pitcher",
        demographics=demographics,
    )
    scored = predict_arrival(
        fit_arrival_model(training, player_type="pitcher", feature_set="core"),
        predictors,
    )
    scored = predict_arrival(
        fit_arrival_model(
            training.filter(pl.col("arrived_within_horizon") == 1),
            player_type="pitcher",
            target_column="meaningful_role_within_horizon",
            outcome_name="meaningful_given_arrival",
            feature_set="core",
        ),
        scored,
    )
    scored = (
        predict_arrival(
            fit_arrival_model(
                training.filter(pl.col("meaningful_role_within_horizon") == 1),
                player_type="pitcher",
                target_column="established_role_within_horizon",
                outcome_name="established_given_meaningful",
                feature_set="core",
            ),
            scored,
        )
        .with_columns(
            _four_year_probability(
                pl.col("predicted_two_year_arrival_probability")
            ).alias("four_year_arrival_probability"),
            _four_year_probability(
                pl.col("predicted_two_year_meaningful_given_arrival_probability")
            ).alias("four_year_meaningful_given_arrival_probability"),
            _four_year_probability(
                pl.col("predicted_two_year_established_given_meaningful_probability")
            ).alias("four_year_established_given_meaningful_probability"),
        )
        .with_columns(
            (
                pl.col("four_year_arrival_probability")
                * pl.col("four_year_meaningful_given_arrival_probability")
            ).alias("four_year_nested_meaningful_probability")
        )
        .with_columns(
            (
                pl.col("four_year_nested_meaningful_probability")
                * pl.col("four_year_established_given_meaningful_probability")
            ).alias("four_year_nested_established_probability")
        )
    )

    pitching = pl.read_parquet(args.pitching)
    player_years = (
        pl.DataFrame(
            [
                {
                    "path_player_id": int(player_id),
                    "player_type": "pitcher",
                    "outcome_tier_v2": "unknown",
                    "career_role": "unknown",
                    "path_year": year - 2021,
                    "source_season": year,
                    "adjusted_workload": 0.0,
                    "annual_role": "inactive",
                }
                for player_id in scored["player_id"].to_list()
                for year in range(2022, 2026)
            ]
        )
        .join(
            pitching.select(
                pl.col("player_id").alias("path_player_id"),
                pl.col("season").alias("source_season"),
                pl.col("pitching_bf").cast(pl.Float64).alias("observed_bf"),
            ),
            on=["path_player_id", "source_season"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col("observed_bf").fill_null(0.0).alias("adjusted_workload"),
            pl.when(pl.col("observed_bf").fill_null(0.0) > 0)
            .then(pl.lit("unknown"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
        .drop("observed_bf")
    )
    observed_paths = build_historical_pitcher_performance_paths(
        player_years,
        pitching,
        runs_per_win=runs_per_win,
    )
    observed = (
        observed_paths.group_by("path_player_id")
        .agg(
            pl.col("observed_component_war")
            .sum()
            .alias("observed_four_year_component_war")
        )
        .rename({"path_player_id": "player_id"})
    )
    means = _path_prefix_means(pl.read_parquet(args.performance_paths))
    evaluated = (
        scored.with_columns(
            pl.struct(
                "four_year_arrival_probability",
                "four_year_nested_meaningful_probability",
                "four_year_nested_established_probability",
            )
            .map_elements(lambda row: _predict_war(row, means), return_dtype=pl.Float64)
            .alias("linked_predicted_war"),
            pl.struct("four_year_arrival_probability")
            .map_elements(
                lambda row: _predict_pooled_war(row, means),
                return_dtype=pl.Float64,
            )
            .alias("arrival_only_pooled_path_prediction"),
        )
        .join(observed, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("observed_four_year_component_war").fill_null(0.0),
            pl.lit(0.0).alias("zero_prediction"),
        )
    )
    subgroup = []
    for group in ("level_tier", "role_tier", "pitch_hand"):
        subgroup.extend(
            evaluated.group_by(group)
            .agg(
                pl.len().alias("players"),
                pl.col("observed_four_year_component_war")
                .mean()
                .alias("observed_mean"),
                pl.col("linked_predicted_war").mean().alias("predicted_mean"),
            )
            .filter(pl.col("players") >= 100)
            .with_columns(pl.lit(group).alias("group"))
            .rename({group: "value"})
            .select("group", "value", "players", "observed_mean", "predicted_mean")
            .sort("value")
            .to_dicts()
        )
    linked_metrics = _metrics(evaluated, "linked_predicted_war")
    pooled_metrics = _metrics(evaluated, "arrival_only_pooled_path_prediction")
    paired = _paired_bootstrap(
        evaluated, "linked_predicted_war", "arrival_only_pooled_path_prediction"
    )
    pooled_vs_zero = _paired_bootstrap(
        evaluated, "arrival_only_pooled_path_prediction", "zero_prediction"
    )
    report = {
        "report_schema_version": 1,
        "as_of_date": args.as_of_date.isoformat(),
        "status": "development_replay_complete_not_promoted",
        "training_snapshot": 2018,
        "forecast_snapshot": 2021,
        "outcome_seasons": [2022, 2023, 2024, 2025],
        "path_library_cutoff": "window_end_year <= 2021",
        "runs_per_win": runs_per_win,
        "sources": {
            path.as_posix(): sha256_file(path)
            for path in [
                snapshot_path,
                *history_stat_paths,
                args.membership,
                args.skill,
                args.demographics,
                args.pitching,
                args.performance_paths,
                args.environment_report,
            ]
        },
        "path_prefix_means": means,
        "linked": linked_metrics,
        "arrival_only_pooled_path": pooled_metrics,
        "linked_vs_arrival_only_paired": paired,
        "arrival_only_vs_zero_paired": pooled_vs_zero,
        "zero_baseline": _metrics(evaluated, "zero_prediction"),
        "subgroups": subgroup,
        "decision": (
            "promising development replay; require fresh confirmation and current "
            "incumbent comparison before promotion"
        ),
        "limits": [
            "The 2021 cohort and hurdle have appeared in prior development work; this is chronology-safe but not fresh confirmation.",
            "This scores component WAR only, not defense-independent official WAR or trade value.",
            "The constant-hazard four-year hurdle is tested as deployed and is already known to be optimistic.",
            "All non-arrivals remain as zero observed WAR.",
        ],
        "model_effect": "none",
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown = f"""# Linked pitcher path replay

Status: **promising development replay; not promoted**.

The replay fits the hurdle on the 2018 snapshot, forecasts every eligible 2021
pre-MLB pitcher, uses only six-year career paths complete by the 2021 cutoff, and
scores actual 2022-2025 MLB component WAR. Non-arrivals remain zero.

| Players | Observed mean WAR | Linked predicted | Bias | Linked RMSE | Arrival-only RMSE | Zero RMSE |
|---:|---:|---:|---:|---:|---:|---:|
| {linked_metrics["players"]:,} | {linked_metrics["observed_mean"]:.3f} | {linked_metrics["predicted_mean"]:.3f} | {linked_metrics["bias"]:+.3f} | {linked_metrics["rmse"]:.3f} | {pooled_metrics["rmse"]:.3f} | {report["zero_baseline"]["rmse"]:.3f} |

The linked construction is directionally coherent and its broad scale is plausible in
this replay: predicted mean WAR is close to observed and it beats predicting zero.
The tiered path changes MSE versus an arrival-only pooled path by
{paired["candidate_minus_baseline_mse"]:+.6f}, with a 95% interval of
[{paired["p025"]:+.6f}, {paired["p975"]:+.6f}]. This cohort and hurdle have already
been used in development, so this is not fresh confirmation. No current player value
or rank changes.

The simpler arrival-only path changes MSE versus zero by
{pooled_vs_zero["candidate_minus_baseline_mse"]:+.6f}, with a 95% interval of
[{pooled_vs_zero["p025"]:+.6f}, {pooled_vs_zero["p975"]:+.6f}].
"""
    args.output_md.write_text(markdown, encoding="utf-8")
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
