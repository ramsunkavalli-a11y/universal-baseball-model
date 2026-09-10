#!/usr/bin/env python3
"""Materialize research-only workload plus component uncertainty for prospects."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_workload_uncertainty import (
    build_nested_component_uncertainty,
)
from universal_baseball.storage import write_canonical_parquet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-component-uncertainty-result.json"),
    )
    args = parser.parse_args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    )
    workload_paths = pl.read_parquet(
        root / "prospect-outcome-quality" / "post-debut-workload-paths.parquet"
    )
    rates_root = root / "phase2-conditional-war-paths" / dated / "tables"
    hitter_rates = pl.read_parquet(rates_root / "hitter_conditional_war_rates.parquet")
    pitcher_rates = pl.read_parquet(rates_root / "pitcher_conditional_war_rates.parquet")
    rate_report = json.loads(
        (root / "phase2-conditional-war-paths" / dated / "report.json").read_text(
            encoding="utf-8"
        )
    )
    runs_per_win = float(rate_report["reference_environment"]["runs_per_win"])
    result = build_nested_component_uncertainty(
        nested,
        workload_paths,
        hitter_rates,
        pitcher_rates,
        runs_per_win=runs_per_win,
    )
    workload = pl.read_parquet(
        root / "phase2-prospect-workload-uncertainty" / dated
        / "prospect-workload-uncertainty.parquet"
    )
    joined = (
        nested.select("player_id", "model_player_type", "three_tier_expected_six_year_war")
        .join(result, on="player_id", how="inner", validate="1:1")
        .join(workload, on="player_id", how="inner", validate="1:1")
        .with_columns(
            (pl.col("component_workload_war_p90") - pl.col("component_workload_war_p10"))
            .alias("component_width"),
            (pl.col("workload_war_p90") - pl.col("workload_war_p10"))
            .alias("workload_width"),
        )
    )
    output = root / "phase2-prospect-component-uncertainty" / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result,
        output / "prospect-component-uncertainty.parquet",
        table_name="phase2_prospect_component_uncertainty",
    ).as_record()
    by_type = []
    for player_type, group in joined.partition_by("model_player_type", as_dict=True).items():
        by_type.append(
            {
                "player_type": str(player_type[0]),
                "players": group.height,
                "mean_point_war": float(group["component_workload_war_mean"].mean()),
                "mean_component_p10": float(group["component_workload_war_p10"].mean()),
                "mean_component_p50": float(group["component_workload_war_p50"].mean()),
                "mean_component_p90": float(group["component_workload_war_p90"].mean()),
                "mean_component_width": float(group["component_width"].mean()),
                "mean_workload_only_width": float(group["workload_width"].mean()),
                "mean_component_star_probability": float(
                    group["component_workload_star_probability"].mean()
                ),
            }
        )
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "research_only_component_uncertainty_complete",
        "contract": "docs/prospect-component-uncertainty-plan.md",
        "players": result.height,
        "runs_per_win": runs_per_win,
        "normal_quadrature_nodes": 41,
        "maximum_absolute_mean_difference": float(
            (
                joined["component_workload_war_mean"]
                - joined["three_tier_expected_six_year_war"]
            ).abs().max()
        ),
        "by_player_type": by_type,
        "boundaries": {
            "workload_uncertainty_included": True,
            "component_rate_uncertainty_included": True,
            "position_defense_running_uncertainty_included": False,
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
        "by_player_type": by_type,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
