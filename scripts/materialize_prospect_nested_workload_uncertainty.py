#!/usr/bin/env python3
"""Materialize workload-only ranges for the private nested prospect preview."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_workload_uncertainty import (
    build_nested_workload_uncertainty,
)
from universal_baseball.storage import write_canonical_parquet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-nested-workload-uncertainty-result.json"),
    )
    args = parser.parse_args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    )
    paths = pl.read_parquet(
        root / "prospect-outcome-quality/post-debut-workload-paths.parquet"
    )
    result = build_nested_workload_uncertainty(nested, paths)
    output = root / "phase2-prospect-workload-uncertainty" / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result,
        output / "prospect-workload-uncertainty.parquet",
        table_name="phase2_prospect_workload_uncertainty",
    ).as_record()
    joined = nested.select(
        "player_id", "model_player_type", "three_tier_expected_six_year_war"
    ).join(result, on="player_id", how="inner", validate="1:1")
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "prospect_nested_workload_uncertainty_complete",
        "contract": "docs/prospect-nested-workload-uncertainty-plan.md",
        "players": result.height,
        "maximum_absolute_mean_difference": float(
            (joined["workload_war_mean"] - joined["three_tier_expected_six_year_war"])
            .abs().max()
        ),
        "by_player_type": [
            {
                "player_type": str(player_type[0]),
                "players": group.height,
                "mean_point_war": float(group["workload_war_mean"].mean()),
                "mean_p10_war": float(group["workload_war_p10"].mean()),
                "mean_p50_war": float(group["workload_war_p50"].mean()),
                "mean_p90_war": float(group["workload_war_p90"].mean()),
                "mean_workload_only_star_probability": float(
                    group["workload_only_star_probability"].mean()
                ),
            }
            for player_type, group in joined.partition_by(
                "model_player_type", as_dict=True
            ).items()
        ],
        "boundaries": {
            "workload_uncertainty_only": True,
            "skill_rate_uncertainty_included": False,
            "outside_fv_used": False,
            "current_2026_outcomes_used": False,
            "production_value_changed": False,
        },
        "storage": storage,
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "players": result.height,
        "maximum_absolute_mean_difference": report["maximum_absolute_mean_difference"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
