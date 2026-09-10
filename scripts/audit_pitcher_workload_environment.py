#!/usr/bin/env python3
"""Measure MLB pitcher workload-environment drift without fitting a candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


def summarize_environment(stats: pl.DataFrame) -> pl.DataFrame:
    required = {
        "season", "player_id", "pitching_bf", "pitching_games", "pitching_starts"
    }
    if missing := sorted(required - set(stats.columns)):
        raise ValueError(f"pitcher workload source missing fields: {missing}")
    source = stats.filter(pl.col("pitching_bf") > 0)
    if source.group_by("season", "player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("pitcher workload source violates player-season grain")
    return source.group_by("season").agg(
        pl.col("player_id").n_unique().alias("active_pitchers"),
        pl.col("pitching_bf").sum().alias("league_bf"),
        pl.col("pitching_starts").sum().alias("league_starts"),
        pl.col("pitching_bf").mean().alias("mean_bf_per_pitcher"),
        pl.col("pitching_bf").median().alias("median_bf_per_pitcher"),
        pl.col("pitching_bf").quantile(0.75).alias("p75_bf_per_pitcher"),
        pl.col("pitching_bf").quantile(0.90).alias("p90_bf_per_pitcher"),
        (pl.col("pitching_starts") > 0).sum().alias("pitchers_with_start"),
    ).sort("season")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stats", type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory/tables/"
            "mlb_pitching_2015_2024.parquet"
        ),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/pitcher-workload-environment-result.json"),
    )
    args = parser.parse_args()
    annual = summarize_environment(pl.read_parquet(args.stats))
    pre = annual.filter(pl.col("season").is_between(2015, 2019))
    modern = annual.filter(pl.col("season").is_between(2021, 2024))
    metrics = (
        "active_pitchers", "mean_bf_per_pitcher", "median_bf_per_pitcher",
        "p75_bf_per_pitcher", "p90_bf_per_pitcher", "pitchers_with_start",
    )
    comparison = {
        metric: {
            "2015_2019_mean": float(pre[metric].mean()),
            "2021_2024_mean": float(modern[metric].mean()),
            "modern_to_prior_ratio": float(modern[metric].mean() / pre[metric].mean()),
        }
        for metric in metrics
    }
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_workload_environment_diagnostic_complete",
        "source": str(args.stats),
        "annual": annual.to_dicts(),
        "era_comparison": comparison,
        "interpretation": (
            "league BF remains stable while more pitchers share it; future career "
            "workload should separate the league environment from player-relative role"
        ),
        "boundaries": {
            "descriptive_only": True,
            "candidate_parameter_selected": False,
            "shortened_2020_excluded_from_era_means": True,
            "current_2026_outcomes_used": False,
            "outside_fv_used": False,
            "current_values_changed": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"era_comparison": comparison}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
