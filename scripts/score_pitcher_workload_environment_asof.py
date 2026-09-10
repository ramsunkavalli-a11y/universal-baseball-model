#!/usr/bin/env python3
"""Score the frozen cutoff-safe pitcher workload environment candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_workload_validation import (
    build_pitcher_environment_asof_scores,
)


BASELINE = "raw_pooled_tier"


def _summary(scores: pl.DataFrame, groups: list[str]) -> pl.DataFrame:
    return scores.group_by(groups).agg(
        pl.len().alias("players"),
        pl.col("crps").mean().alias("mean_crps"),
        pl.col("covered_80").mean().alias("coverage_80"),
        pl.col("median_error").median().alias("median_error"),
    ).sort(groups)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--annual-paths", type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/"
            "post-debut-annual-workload-paths.parquet"
        ),
    )
    parser.add_argument(
        "--pitcher-seasons", type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/"
            "mlb_pitching_2009_2025.parquet"
        ),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/pitcher-workload-environment-asof-result.json"),
    )
    args = parser.parse_args()
    scores = build_pitcher_environment_asof_scores(
        pl.read_parquet(args.annual_paths), pl.read_parquet(args.pitcher_seasons)
    )
    overall = _summary(scores, ["candidate_id"])
    by_year = _summary(scores, ["candidate_id", "evaluation_year"])
    by_tier = _summary(scores, ["candidate_id", "outcome_tier_v2"])
    by_role = _summary(scores, ["candidate_id", "granular_role"])
    baseline_crps = float(
        overall.filter(pl.col("candidate_id") == BASELINE).item(0, "mean_crps")
    )
    decisions = []
    for row in overall.to_dicts():
        candidate_id = str(row["candidate_id"])
        year_rows = by_year.filter(pl.col("candidate_id") == candidate_id)
        baseline_years = by_year.filter(pl.col("candidate_id") == BASELINE)
        year_safe = all(
            item["mean_crps"]
            <= baseline_years.filter(
                pl.col("evaluation_year") == item["evaluation_year"]
            ).item(0, "mean_crps")
            for item in year_rows.to_dicts()
        )
        decisions.append(
            {
                "candidate_id": candidate_id,
                "pooled_crps_improved": float(row["mean_crps"]) < baseline_crps,
                "both_years_nonworse": year_safe,
                "development_gate_passed": (
                    candidate_id != BASELINE
                    and float(row["mean_crps"]) < baseline_crps
                    and year_safe
                ),
            }
        )
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_environment_asof_development_scored",
        "contract": "docs/pitcher-workload-environment-asof-plan.md",
        "baseline": BASELINE,
        "overall": overall.to_dicts(),
        "by_evaluation_year": by_year.to_dicts(),
        "by_outcome_tier": by_tier.to_dicts(),
        "by_granular_role": by_role.to_dicts(),
        "decisions": decisions,
        "chronology": scores.group_by("evaluation_year").agg(
            pl.col("maximum_training_window_end").max(),
            pl.col("environment_slope").first(),
        ).sort("evaluation_year").to_dicts(),
        "boundaries": {
            "complete_training_paths_end_before_forecast": True,
            "environment_fit_uses_pre_forecast_seasons_only": True,
            "conditional_on_eventual_tier_and_role": True,
            "development_evidence_only": True,
            "outside_fv_used": False,
            "current_2026_outcomes_used": False,
            "current_values_changed": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
