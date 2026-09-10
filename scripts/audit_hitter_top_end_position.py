#!/usr/bin/env python3
"""Describe position concentration and positional-run sensitivity at the hitter top end."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_value import display_fv, model_fv_from_expected_war


def _counts(frame: pl.DataFrame) -> list[dict[str, object]]:
    total = frame.height
    return (
        frame.group_by("primary_position")
        .len(name="players")
        .with_columns((pl.col("players") / total).alias("share"))
        .sort("players", descending=True)
        .to_dicts()
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output", type=Path,
        default=Path("docs/hitter-top-end-position-audit-result.json"),
    )
    args = parser.parse_args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    ).filter(
        pl.col("player_name").is_not_null()
        & pl.col("ordered_arrival_probability").is_not_null()
        & (pl.col("model_player_type") == "hitter")
    )
    paths_root = root / "phase2-conditional-war-paths" / dated
    rates = pl.read_parquet(
        paths_root / "tables/hitter_expected_war_paths.parquet"
    ).group_by("player_id").agg(
        pl.col("positional_runs_per_600").mean(),
        pl.col("batting_runs_per_600").mean(),
        pl.col("baserunning_runs_per_600").mean(),
        pl.col("defense_runs_per_600").mean(),
        pl.col("weighted_history_pa").max(),
    )
    war_report = json.loads((paths_root / "report.json").read_text(encoding="utf-8"))
    runs_per_win = float(war_report["reference_environment"]["runs_per_win"])
    evaluated = nested.join(rates, on="player_id", how="left", validate="1:1").with_columns(
        (
            pl.col("positional_runs_per_600")
            * pl.col("three_tier_expected_workload")
            / 600.0
            / runs_per_win
        ).alias("expected_position_war")
    ).with_columns(
        (
            pl.col("three_tier_expected_six_year_war") - pl.col("expected_position_war")
        ).alias("neutral_position_expected_war")
    ).with_columns(
        pl.struct("neutral_position_expected_war", "model_player_type")
        .map_elements(
            lambda row: model_fv_from_expected_war(
                float(row["neutral_position_expected_war"]),
                str(row["model_player_type"]),
            ),
            return_dtype=pl.Float64,
        )
        .alias("neutral_position_fv_granular")
    ).with_columns(
        pl.col("neutral_position_fv_granular")
        .map_elements(display_fv, return_dtype=pl.Int64)
        .alias("neutral_position_fv_display")
    )
    thresholds = {}
    for threshold in (40, 45, 50, 55):
        group = evaluated.filter(pl.col("three_tier_model_fv_display") >= threshold)
        thresholds[str(threshold)] = {
            "players": group.height,
            "by_position": _counts(group),
        }
    catchers = evaluated.filter(pl.col("primary_position") == "C")
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "hitter_top_end_position_diagnostic_complete",
        "players": evaluated.height,
        "population_by_position": _counts(evaluated),
        "thresholds": thresholds,
        "catcher_sensitivity": {
            "catchers": catchers.height,
            "current_50_plus": catchers.filter(
                pl.col("three_tier_model_fv_display") >= 50
            ).height,
            "neutral_position_50_plus": catchers.filter(
                pl.col("neutral_position_fv_display") >= 50
            ).height,
            "current_55_plus": catchers.filter(
                pl.col("three_tier_model_fv_display") >= 55
            ).height,
            "neutral_position_55_plus": catchers.filter(
                pl.col("neutral_position_fv_display") >= 55
            ).height,
        },
        "top_20": evaluated.sort(
            "three_tier_expected_six_year_war", descending=True
        ).select(
            "player_id", "player_name", "primary_position",
            "three_tier_expected_six_year_war", "three_tier_model_fv_display",
            "ordered_arrival_probability", "ordered_established_probability",
            "three_tier_expected_workload", "weighted_history_pa",
            "batting_runs_per_600", "baserunning_runs_per_600",
            "defense_runs_per_600", "positional_runs_per_600",
            "expected_position_war", "neutral_position_expected_war",
            "neutral_position_fv_display",
        ).head(20).to_dicts(),
        "interpretation": {
            "neutral_position_is_diagnostic_not_candidate": True,
            "position_quota_or_grade_target_used": False,
            "outside_fv_used": False,
            "current_2026_outcomes_used": False,
            "position_transition_candidate_previously_rejected": True,
        },
    }
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["catcher_sensitivity"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
