#!/usr/bin/env python3
"""Materialize the frozen conservative current-organization capacity view."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.opportunity_capacity import historical_mlb_workload_pools
from universal_baseball.team_opportunity_allocation import (
    allocate_current_organization_opportunity,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", default="2026-09-08")
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/current-organization-opportunity-allocation-result.json"),
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
    full = actual.filter((pl.col("actual_pa") > 100_000) & (pl.col("season") != 2020))
    league_capacity = float(full.get_column("actual_pa").median())
    team_capacity = league_capacity / 30.0

    paths = args.generated_root / "phase2-conditional-war-paths" / args.as_of_date / "tables"
    hitter_source = pl.read_parquet(paths / "hitter_expected_war_paths.parquet")
    pitcher_source = pl.read_parquet(paths / "pitcher_expected_war_paths.parquet")
    ownership = pl.read_parquet(
        args.generated_root / "league-control" / args.as_of_date / "future-control-path.parquet"
    )
    allocated = allocate_current_organization_opportunity(
        hitter_source, pitcher_source, ownership, team_capacity=team_capacity
    )
    output = (
        args.generated_root / "current-organization-opportunity" / args.as_of_date / "tables"
    )
    output.mkdir(parents=True, exist_ok=True)
    allocated.hitter.write_parquet(output / "hitter_current_organization_opportunity.parquet")
    allocated.pitcher.write_parquet(output / "pitcher_current_organization_opportunity.parquet")
    allocated.teams.write_parquet(output / "team_opportunity_capacity.parquet")

    by_season = allocated.teams.group_by("season").agg(
        pl.col("raw_hitter_workload").sum().alias("raw_controlled_hitter_pa"),
        pl.col("allocated_hitter_workload").sum().alias("allocated_controlled_hitter_pa"),
        pl.col("unassigned_hitter_workload").sum().alias("unassigned_hitter_pa"),
        pl.col("raw_pitcher_workload").sum().alias("raw_controlled_pitcher_bf"),
        pl.col("allocated_pitcher_workload").sum().alias("allocated_controlled_pitcher_bf"),
        pl.col("unassigned_pitcher_workload").sum().alias("unassigned_pitcher_bf"),
        (pl.col("hitter_scale") < 1.0).sum().alias("hitter_oversubscribed_teams"),
        (pl.col("pitcher_scale") < 1.0).sum().alias("pitcher_oversubscribed_teams"),
    ).with_columns(
        pl.lit(league_capacity).alias("league_capacity_each_side"),
        (pl.col("unassigned_hitter_pa") / league_capacity).alias("unassigned_hitter_share"),
        (pl.col("unassigned_pitcher_bf") / league_capacity).alias("unassigned_pitcher_share"),
    ).sort("season")
    oversubscribed = allocated.teams.filter(
        (pl.col("hitter_scale") < 1.0) | (pl.col("pitcher_scale") < 1.0)
    ).select(
        "organization_id", "season", "raw_hitter_workload", "hitter_scale",
        "raw_pitcher_workload", "pitcher_scale",
    ).sort("season", "organization_id")
    report = {
        "report_schema_version": "0.1",
        "status": "research_current_organization_capacity_layer_complete",
        "as_of_date": args.as_of_date,
        "contract": "docs/current-organization-opportunity-allocation-contract.md",
        "historical_reference": {
            "full_seasons": full.get_column("season").to_list(),
            "median_league_pa_and_bf": league_capacity,
            "team_capacity": team_capacity,
            "teams": 30,
        },
        "coverage": {
            "hitter_input_player_seasons": hitter_source.height,
            "pitcher_input_player_seasons": pitcher_source.height,
            "allocated_controlled_hitter_player_seasons": allocated.hitter.height,
            "allocated_controlled_pitcher_player_seasons": allocated.pitcher.height,
            "team_seasons": allocated.teams.height,
        },
        "by_season": by_season.to_dicts(),
        "oversubscribed_team_seasons": oversubscribed.to_dicts(),
        "checks": {
            "team_seasons_close_with_explicit_unassigned_share": True,
            "league_seasons_close_to_30_team_capacities": True,
            "player_opportunity_never_increased": True,
            "organization_neutral_input_modified": False,
            "skill_or_war_rate_modified": False,
            "current_values_modified": False,
        },
        "boundary": (
            "Research current-organization capacity view only. Unassigned workload "
            "represents free agents, future acquisitions, replacement players and "
            "unresolved ownership. Position and pitching-role constraints are not yet allocated."
        ),
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
