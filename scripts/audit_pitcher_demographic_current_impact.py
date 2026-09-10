#!/usr/bin/env python3
"""Measure the exact current private-value impact of the pitcher adjustment."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.model_fv import apply_pre_mlb_three_tier_workload


ROOT = Path("reports/generated")
DATED = "2026-09-08"
OUTPUT = Path("docs/pitcher-demographic-current-impact-result.json")


def _counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(threshold): frame.filter(pl.col(column) >= threshold).height
        for threshold in (40, 45, 50, 55, 60)
    }


def main() -> int:
    control = pl.read_parquet(
        ROOT / "league-control" / DATED / "league-control-snapshot.parquet"
    )
    pre_mlb = control.filter(pl.col("mlb_debut_date").is_null()).select(
        "player_id", "player_name", "organization_id"
    )
    pre_mlb_ids = set(pre_mlb.get_column("player_id").to_list())
    priors = pl.read_parquet(
        ROOT / "prospect-outcome-quality/post-debut-workload-priors-v2.parquet"
    )
    adjusted = pl.read_parquet(
        ROOT / "phase2-nested-career-fv" / DATED / "nested-career-model-fv.parquet"
    )
    counterfactual_model_fv = pl.read_parquet(
        ROOT / "phase2-model-fv-no-pitcher-demo" / DATED / "model-fv.parquet"
    )
    counterfactual = apply_pre_mlb_three_tier_workload(
        counterfactual_model_fv,
        priors,
        pre_mlb_player_ids=pre_mlb_ids,
    ).join(pre_mlb, on="player_id", how="left", validate="1:1")
    comparison = adjusted.select(
        "player_id", "player_name", "model_player_type",
        pl.col("three_tier_expected_six_year_war").alias("adjusted_war"),
        pl.col("three_tier_model_fv_display").alias("adjusted_fv"),
    ).join(
        counterfactual.select(
            "player_id",
            pl.col("three_tier_expected_six_year_war").alias("counterfactual_war"),
            pl.col("three_tier_model_fv_display").alias("counterfactual_fv"),
        ),
        on="player_id",
        how="inner",
        validate="1:1",
    ).with_columns(
        (pl.col("adjusted_war") - pl.col("counterfactual_war")).alias("war_delta"),
        (pl.col("adjusted_fv") - pl.col("counterfactual_fv")).alias("fv_delta"),
    )
    pitchers = comparison.filter(
        (pl.col("model_player_type") == "pitcher") & pl.col("player_name").is_not_null()
    )
    hitters = comparison.filter(
        (pl.col("model_player_type") == "hitter") & pl.col("player_name").is_not_null()
    )
    adjusted_types = pl.read_parquet(
        ROOT / "phase2-model-fv" / DATED / "model-fv.parquet"
    ).select("player_id", "model_player_type")
    counterfactual_types = counterfactual_model_fv.select(
        "player_id", pl.col("model_player_type").alias("counterfactual_player_type")
    )
    type_switches = adjusted_types.join(
        counterfactual_types, on="player_id", how="inner", validate="1:1"
    ).filter(
        pl.col("model_player_type") != pl.col("counterfactual_player_type")
    ).height
    report = {
        "report_schema_version": "0.1",
        "status": "pitcher_demographic_current_impact_complete",
        "contract": "docs/pitcher-demographic-current-impact-plan.md",
        "pitchers": pitchers.height,
        "expected_six_year_war": {
            "counterfactual_total": float(pitchers.get_column("counterfactual_war").sum()),
            "adjusted_total": float(pitchers.get_column("adjusted_war").sum()),
            "total_delta": float(pitchers.get_column("war_delta").sum()),
            "mean_delta": float(pitchers.get_column("war_delta").mean()),
            "median_delta": float(pitchers.get_column("war_delta").median()),
        },
        "counterfactual_fv_counts": _counts(pitchers, "counterfactual_fv"),
        "adjusted_fv_counts": _counts(pitchers, "adjusted_fv"),
        "players_with_display_grade_change": pitchers.filter(
            pl.col("fv_delta") != 0
        ).height,
        "players_grade_up": pitchers.filter(pl.col("fv_delta") > 0).height,
        "players_grade_down": pitchers.filter(pl.col("fv_delta") < 0).height,
        "largest_war_increases": pitchers.sort(
            "war_delta", descending=True
        ).select(
            "player_id", "player_name", "counterfactual_war", "adjusted_war",
            "war_delta", "counterfactual_fv", "adjusted_fv",
        ).head(15).to_dicts(),
        "largest_war_decreases": pitchers.sort("war_delta").select(
            "player_id", "player_name", "counterfactual_war", "adjusted_war",
            "war_delta", "counterfactual_fv", "adjusted_fv",
        ).head(15).to_dicts(),
        "hitter_invariance": {
            "players": hitters.height,
            "nonzero_war_differences": hitters.filter(
                pl.col("war_delta").abs() > 1e-12
            ).height,
            "display_grade_changes": hitters.filter(pl.col("fv_delta") != 0).height,
        },
        "player_type_switches": type_switches,
        "boundaries": {
            "only_pitcher_demographic_adjustment_toggled": True,
            "coefficients_or_thresholds_retuned": False,
            "outside_fv_used": False,
        },
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "war": report["expected_six_year_war"],
        "counterfactual_fv_counts": report["counterfactual_fv_counts"],
        "adjusted_fv_counts": report["adjusted_fv_counts"],
        "grade_changes": report["players_with_display_grade_change"],
        "hitter_invariance": report["hitter_invariance"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
