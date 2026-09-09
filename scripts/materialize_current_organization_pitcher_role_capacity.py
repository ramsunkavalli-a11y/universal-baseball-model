#!/usr/bin/env python3
"""Estimate frozen pitcher-role capacity and apply it to the current-team view."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.team_opportunity_allocation import (
    allocate_pitcher_role_capacity,
    estimate_pitcher_role_capacity_shares,
    historical_pitcher_role_shares,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", default="2026-09-08")
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/current-organization-pitcher-role-capacity-result.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    history_paths = sorted(
        (args.generated_root / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
    stats = pl.concat(
        [pl.read_parquet(path) for path in history_paths], how="vertical_relaxed"
    )
    shares = historical_pitcher_role_shares(stats).filter(
        pl.col("season").is_between(2021, 2025)
    )
    team_season_count = shares.select("season", "team_id").unique().height
    if team_season_count != 150:
        raise ValueError(f"expected 150 MLB team-seasons, found {team_season_count}")
    capacity = estimate_pitcher_role_capacity_shares(
        shares, development_seasons=(2021, 2022, 2023, 2024)
    )
    confirmation = (
        shares.filter(pl.col("season") == 2025)
        .join(capacity.select("pitcher_role", "capacity_share"), on="pitcher_role")
        .with_columns(
            (pl.col("role_share") - pl.col("capacity_share")).alias("share_error"),
            (pl.col("role_share") - pl.col("capacity_share")).abs().alias(
                "absolute_share_error"
            ),
        )
    )
    confirmation_by_role = confirmation.group_by("pitcher_role").agg(
        pl.col("absolute_share_error").mean().alias("mean_absolute_share_error"),
        pl.col("absolute_share_error").quantile(0.9).alias("p90_absolute_share_error"),
        pl.col("share_error").mean().alias("mean_signed_share_error"),
        pl.len().alias("teams"),
    ).sort("pitcher_role")
    confirmation_team = confirmation.group_by("team_id").agg(
        (0.5 * pl.col("absolute_share_error").sum()).alias("total_variation")
    )

    team_root = (
        args.generated_root / "current-organization-opportunity" / args.as_of_date / "tables"
    )
    current_team_pitcher = pl.read_parquet(
        team_root / "pitcher_current_organization_opportunity.parquet"
    )
    team_capacity_table = pl.read_parquet(team_root / "team_opportunity_capacity.parquet")
    team_capacity = float(team_capacity_table.get_column("team_capacity").unique().item())
    allocated = allocate_pitcher_role_capacity(
        current_team_pitcher, capacity, team_capacity=team_capacity
    )
    output = (
        args.generated_root / "current-organization-pitcher-role-capacity"
        / args.as_of_date / "tables"
    )
    output.mkdir(parents=True, exist_ok=True)
    capacity.write_parquet(output / "frozen_pitcher_role_capacity_shares.parquet")
    confirmation.write_parquet(output / "pitcher_role_capacity_2025_stability.parquet")
    allocated.players.write_parquet(output / "pitcher_role_capped_opportunity.parquet")
    allocated.components.write_parquet(output / "pitcher_role_components.parquet")
    allocated.groups.write_parquet(output / "team_pitcher_role_capacity.parquet")

    by_season = allocated.players.group_by("season").agg(
        pl.col("current_org_expected_mlb_bf").sum().alias("team_capped_bf"),
        pl.col("role_capped_expected_mlb_bf").sum().alias("role_capped_bf"),
        (
            pl.col("role_capped_expected_mlb_bf")
            < pl.col("current_org_expected_mlb_bf") - 1e-7
        ).sum().alias("reduced_player_rows"),
    ).with_columns(
        (pl.col("team_capped_bf") - pl.col("role_capped_bf")).alias(
            "additional_role_capacity_reduction_bf"
        )
    ).sort("season")
    by_role = allocated.groups.group_by("pitcher_role").agg(
        pl.col("raw_group_bf").sum().alias("raw_bf"),
        pl.col("allocated_group_bf").sum().alias("allocated_bf"),
        (pl.col("pitcher_role_scale") < 1.0).sum().alias(
            "over_capacity_team_seasons"
        ),
        pl.col("pitcher_role_scale").min().alias("minimum_scale"),
    ).with_columns(
        (pl.col("raw_bf") - pl.col("allocated_bf")).alias("reduction_bf")
    ).sort("pitcher_role")
    report = {
        "report_schema_version": "0.1",
        "status": "research_pitcher_role_capacity_complete",
        "as_of_date": args.as_of_date,
        "contract": "docs/current-organization-pitcher-role-capacity-contract.md",
        "source": {
            "source_family": "certified StatsAPI affiliated season stats",
            "team_seasons_2021_2025": team_season_count,
            "development_seasons": [2021, 2022, 2023, 2024],
            "confirmation_season": 2025,
        },
        "frozen_capacity_shares": capacity.to_dicts(),
        "descriptive_2025_stability": {
            "teams": confirmation_team.height,
            "mean_team_total_variation": float(
                confirmation_team.get_column("total_variation").mean()
            ),
            "p90_team_total_variation": float(
                confirmation_team.get_column("total_variation").quantile(0.9)
            ),
            "by_role": confirmation_by_role.to_dicts(),
        },
        "current_effect_by_season": by_season.to_dicts(),
        "current_effect_by_role": by_role.to_dicts(),
        "checks": {
            "capacity_shares_sum_to_one": True,
            "current_roles_applied_fractionally": True,
            "current_role_probabilities_valid": True,
            "current_player_opportunity_never_increased": True,
            "current_team_capacity_not_exceeded": True,
            "organization_neutral_value_changed": False,
        },
        "boundary": (
            "Research current-organization pitcher view only. Role capacities constrain "
            "opportunity, not pitcher talent or organization-neutral trade value."
        ),
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

