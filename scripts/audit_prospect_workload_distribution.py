#!/usr/bin/env python3
"""Run the frozen early/late prospect workload distribution check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_workload_validation import (
    build_workload_holdout_predictions,
    summarize_workload_coverage,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--paths", type=Path,
        default=Path("reports/generated/prospect-outcome-quality/post-debut-workload-paths.parquet"),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-workload-distribution-validation-result.json"),
    )
    args = parser.parse_args()
    predictions = build_workload_holdout_predictions(pl.read_parquet(args.paths))
    overall = summarize_workload_coverage(predictions, ["player_type"])
    tiers = summarize_workload_coverage(
        predictions, ["player_type", "outcome_tier_v2"]
    )
    sources = summarize_workload_coverage(
        predictions, ["player_type", "sample_source"]
    )
    report = {
        "report_schema_version": "0.1",
        "status": "retrospective_cohort_stability_check_complete",
        "contract": "docs/prospect-workload-distribution-validation-plan.md",
        "chronology": {
            "training_debut_years": [2015, 2017],
            "evaluation_debut_years": [2018, 2019],
        },
        "evaluation_players": predictions.height,
        "overall": overall.to_dicts(),
        "by_outcome_tier": tiers.to_dicts(),
        "by_sample_source": sources.to_dicts(),
        "boundaries": {
            "forecast_time_chronology_safe": False,
            "training_path_outcomes_extend_past_evaluation_debut": True,
            "conditional_on_mlb_debut": True,
            "conditional_on_observed_career_tier_and_role": True,
            "arrival_probability_validated": False,
            "war_or_skill_validated": False,
            "outside_fv_used": False,
            "current_2026_outcomes_used": False,
            "production_value_changed": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
