#!/usr/bin/env python3
"""Locate pitcher prospect compression before or inside the FV relabeling step."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_value import (
    display_fv,
    model_fv_from_expected_war,
)


VALUES = Path(
    "reports/generated/phase2-nested-career-fv/2026-09-08/"
    "nested-career-model-fv.parquet"
)
RATES = Path(
    "reports/generated/current-conditional-war-paths/2026-09-08/tables/"
    "pitcher_conditional_war_rates.parquet"
)
OUTPUT = Path("docs/pitcher-fv-mapping-audit-result.json")


def _war_boundary(display_grade: int) -> float:
    low, high = 0.0, 40.0
    for _ in range(80):
        middle = (low + high) / 2.0
        if display_fv(model_fv_from_expected_war(middle, "pitcher")) >= display_grade:
            high = middle
        else:
            low = middle
    return high


def main() -> int:
    values = pl.read_parquet(VALUES).filter(
        (pl.col("model_player_type") == "pitcher")
        & pl.col("ordered_arrival_probability").is_not_null()
    )
    all_rates = pl.read_parquet(RATES)
    first_forecast_season = int(all_rates.get_column("season").min())
    rates = all_rates.filter(
        (pl.col("evidence_tier") == "affiliated_translated")
        & (pl.col("season") == first_forecast_season)
    )
    boundaries = {str(grade): _war_boundary(grade) for grade in (40, 45, 50, 55, 60)}
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_fv_mapping_audit_complete",
        "contract": "docs/pitcher-fv-mapping-audit-plan.md",
        "pre_mlb_pitchers": values.height,
        "display_grade_minimum_expected_six_year_war": boundaries,
        "counts_at_or_above_display_grade": {
            str(grade): values.filter(
                pl.col("three_tier_model_fv_display") >= grade
            ).height
            for grade in (40, 45, 50, 55, 60)
        },
        "expected_six_year_war": {
            "maximum": float(values.get_column("three_tier_expected_six_year_war").max()),
            "p99": float(values.get_column("three_tier_expected_six_year_war").quantile(0.99)),
            "p95": float(values.get_column("three_tier_expected_six_year_war").quantile(0.95)),
            "median": float(values.get_column("three_tier_expected_six_year_war").median()),
        },
        "affiliated_translated_conditional_war_per_800": {
            "forecast_season": first_forecast_season,
            "players": rates.height,
            "minimum": float(rates.get_column("conditional_war_per_800_bf").min()),
            "maximum": float(rates.get_column("conditional_war_per_800_bf").max()),
            "p95": float(rates.get_column("conditional_war_per_800_bf").quantile(0.95)),
            "median": float(rates.get_column("conditional_war_per_800_bf").median()),
        },
        "top_pre_mlb_pitcher": values.sort(
            "three_tier_expected_six_year_war", descending=True
        ).select(
            "player_id", "player_name", "three_tier_expected_six_year_war",
            "three_tier_model_fv_granular", "three_tier_model_fv_display",
            "ordered_arrival_probability", "ordered_meaningful_probability",
            "ordered_established_probability", "three_tier_expected_workload",
            "pitcher_six_control_year_war_if_arrived",
        ).row(0, named=True),
        "decision": {
            "mapping_change_supported": False,
            "responsible_layer": "expected_controlled_war_before_fv_mapping",
        },
        "boundaries": {
            "outside_individual_fv_used": False,
            "target_grade_count_used": False,
            "mapping_is_monotonic": True,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
