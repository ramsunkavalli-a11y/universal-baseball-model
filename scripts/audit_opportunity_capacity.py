#!/usr/bin/env python3
"""Audit whether projected hitter and pitcher workloads form one closed system."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.opportunity_capacity import (
    audit_projected_workload_capacity,
    historical_mlb_workload_pools,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", default="2026-09-08")
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("docs/opportunity-capacity-audit-result.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    history_paths = sorted(
        (args.generated_root / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
    history = pl.concat(
        [pl.read_parquet(path) for path in history_paths], how="vertical_relaxed"
    )
    actual = historical_mlb_workload_pools(history)
    if actual.filter(pl.col("pa_minus_bf") != 0).height:
        raise ValueError("historical PA and BF do not satisfy the closed-system identity")
    full_seasons = actual.filter(pl.col("actual_pa") > 100_000)
    reference = float(full_seasons.get_column("actual_pa").median())
    tables = (
        args.generated_root
        / "phase2-conditional-war-paths"
        / args.as_of_date
        / "tables"
    )
    audit = audit_projected_workload_capacity(
        pl.read_parquet(tables / "hitter_expected_war_paths.parquet"),
        pl.read_parquet(tables / "pitcher_expected_war_paths.parquet"),
        reference_league_workload=reference,
    )
    report = {
        "report_schema_version": "0.1",
        "status": "diagnostic_failed_closed_system_identity",
        "historical_full_season_reference": {
            "seasons": full_seasons.get_column("season").to_list(),
            "median_league_pa_and_bf": reference,
            "actual_pa_equals_bf_every_season": True,
        },
        "projected_seasons": audit.to_dicts(),
        "summary": {
            "capacity_exceeded_seasons": int(
                audit.filter(
                    ~pl.col("hitter_capacity_not_exceeded")
                    | ~pl.col("pitcher_capacity_not_exceeded")
                ).height
            ),
            "closed_system_identity_failed_seasons": int(
                audit.filter(~pl.col("closed_system_identity_passed")).height
            ),
            "maximum_hitter_pitcher_gap_share": float(
                audit.get_column("hitter_pitcher_gap_share").max()
            ),
        },
        "decision": (
            "Do not rescale skill or Model FV. Reconcile both opportunity sides to "
            "one league-season pool, retaining explicit replacement/external share."
        ),
        "research_reconciliation": (
            "Use the capacity-capped arithmetic mean of independently assigned hitter "
            "and pitcher workload as the shared pool. This is the symmetric least-"
            "squares projection onto PA=BF. Scale opportunity, never skill, and retain "
            "the difference from league capacity as external/replacement share."
        ),
    }
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
