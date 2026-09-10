#!/usr/bin/env python3
"""Run the frozen chronology-safe conditional workload replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_workload_validation import (
    build_workload_asof_predictions,
    summarize_workload_coverage,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--paths", type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/"
            "post-debut-workload-paths.parquet"
        ),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-workload-asof-validation-result.json"),
    )
    args = parser.parse_args()
    predictions = build_workload_asof_predictions(pl.read_parquet(args.paths))
    summaries = {
        "overall": summarize_workload_coverage(
            predictions, ["player_type"]
        ).to_dicts(),
        "by_evaluation_year": summarize_workload_coverage(
            predictions, ["evaluation_year", "player_type"]
        ).to_dicts(),
        "by_outcome_tier": summarize_workload_coverage(
            predictions, ["player_type", "outcome_tier_v2"]
        ).to_dicts(),
        "by_sample_source": summarize_workload_coverage(
            predictions, ["player_type", "sample_source"]
        ).to_dicts(),
    }
    chronology = predictions.group_by("evaluation_year").agg(
        pl.col("maximum_training_window_end").max(),
        pl.col("training_players").min().alias("minimum_training_cell"),
        pl.len().alias("evaluation_players"),
    ).sort("evaluation_year")
    report = {
        "report_schema_version": "0.1",
        "status": "chronology_safe_conditional_workload_validation_complete",
        "contract": "docs/prospect-workload-asof-validation-plan.md",
        "chronology": chronology.to_dicts(),
        **summaries,
        "boundaries": {
            "forecast_time_chronology_safe": True,
            "training_windows_end_before_evaluation_year": bool(
                predictions.filter(
                    pl.col("maximum_training_window_end")
                    >= pl.col("evaluation_year")
                ).is_empty()
            ),
            "conditional_on_actual_debut_tier_and_role": True,
            "arrival_skill_and_value_validated": False,
            "current_2026_outcomes_used": False,
            "outside_fv_used": False,
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
