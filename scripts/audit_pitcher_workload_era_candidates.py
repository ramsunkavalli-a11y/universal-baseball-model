#!/usr/bin/env python3
"""Score the frozen era-aware pitcher workload candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_workload_validation import (
    build_pitcher_workload_era_scores,
)


BASELINE = "equal__supported_role"


def _summary(scores: pl.DataFrame, groups: list[str]) -> pl.DataFrame:
    return scores.group_by(groups).agg(
        pl.len().alias("players"),
        pl.col("crps").mean().alias("mean_crps"),
        pl.col("covered_80").mean().alias("coverage_80"),
        pl.col("covered_50").mean().alias("coverage_50"),
        pl.col("median_error").median().alias("median_error"),
    ).sort(groups)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--paths", type=Path,
        default=Path("reports/generated/prospect-outcome-quality/post-debut-workload-paths.parquet"),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/pitcher-workload-era-candidate-result.json"),
    )
    args = parser.parse_args()
    scores = build_pitcher_workload_era_scores(pl.read_parquet(args.paths))
    overall = _summary(scores, ["candidate_id"])
    tiers = _summary(scores, ["candidate_id", "outcome_tier_v2"])
    baseline_crps = overall.filter(pl.col("candidate_id") == BASELINE).item(
        0, "mean_crps"
    )
    baseline_tiers = {
        row["outcome_tier_v2"]: row
        for row in tiers.filter(pl.col("candidate_id") == BASELINE).to_dicts()
    }
    decisions = []
    for row in overall.to_dicts():
        candidate_id = row["candidate_id"]
        candidate_tiers = {
            item["outcome_tier_v2"]: item
            for item in tiers.filter(
                pl.col("candidate_id") == candidate_id
            ).to_dicts()
        }
        established_improved = (
            candidate_tiers["established"]["mean_crps"]
            < baseline_tiers["established"]["mean_crps"]
        )
        supported_tiers_safe = all(
            candidate_tiers[tier]["mean_crps"]
            <= baseline["mean_crps"] * 1.01
            for tier, baseline in baseline_tiers.items()
            if baseline["players"] >= 30
        )
        decisions.append(
            {
                "candidate_id": candidate_id,
                "overall_improved": row["mean_crps"] < baseline_crps,
                "established_improved": established_improved,
                "supported_tiers_safe": supported_tiers_safe,
                "passes_research_gate": (
                    candidate_id != BASELINE
                    and row["mean_crps"] < baseline_crps
                    and established_improved
                    and supported_tiers_safe
                ),
            }
        )
    passing = [
        row["candidate_id"] for row in decisions if row["passes_research_gate"]
    ]
    selected = None
    if passing:
        selected = min(
            passing,
            key=lambda candidate: overall.filter(
                pl.col("candidate_id") == candidate
            ).item(0, "mean_crps"),
        )
    report = {
        "report_schema_version": "0.1",
        "status": "retrospective_era_candidate_score_complete",
        "contract": "docs/pitcher-workload-era-candidate-plan.md",
        "baseline_candidate": BASELINE,
        "research_preferred_candidate": selected,
        "overall": overall.to_dicts(),
        "by_outcome_tier": tiers.to_dicts(),
        "gate_decisions": decisions,
        "boundaries": {
            "retrospective_development_only": True,
            "untouched_confirmation": False,
            "current_values_changed": False,
            "outside_fv_used": False,
            "current_2026_outcomes_used": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
