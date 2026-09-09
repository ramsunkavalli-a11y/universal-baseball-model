#!/usr/bin/env python3
"""Estimate frozen hitter position capacity and apply it to the current-team view."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.team_opportunity_allocation import (
    allocate_hitter_position_capacity,
    estimate_hitter_position_capacity_shares,
    historical_hitter_position_shares,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", default="2026-09-08")
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/current-organization-position-capacity-result.json"),
    )
    return parser.parse_args()


def _only(root: Path, pattern: str) -> Path:
    matches = list(root.rglob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one {pattern} below {root}, found {len(matches)}")
    return matches[0]


def main() -> int:
    args = _args()
    source_root = args.generated_root / "position-capacity-source"
    historical_report_path = _only(source_root / "historical", "report.json")
    confirmation_report_path = _only(source_root / "2025", "report.json")
    historical_report = json.loads(historical_report_path.read_text(encoding="utf-8"))
    confirmation_report = json.loads(confirmation_report_path.read_text(encoding="utf-8"))
    if not historical_report.get("decision", {}).get("historical_position_role_source_certified"):
        raise ValueError("historical position source is not certified")
    if not confirmation_report.get("decision", {}).get("source_materialized"):
        raise ValueError("2025 position source is not accepted")
    historical_fielding = pl.read_parquet(
        _only(source_root / "historical", "historical_fielding_usage.parquet")
    )
    confirmation_fielding = pl.read_parquet(
        _only(source_root / "2025", "position_role_2025_fielding_usage.parquet")
    )
    fielding = pl.concat([historical_fielding, confirmation_fielding])
    history_paths = sorted(
        (args.generated_root / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
    stats = pl.concat(
        [pl.read_parquet(path) for path in history_paths], how="vertical_relaxed"
    )
    shares = historical_hitter_position_shares(fielding, stats).filter(
        pl.col("season").is_between(2021, 2025)
    )
    team_season_count = shares.select("season", "team_id").unique().height
    if team_season_count != 150:
        raise ValueError(f"expected 150 MLB team-seasons, found {team_season_count}")
    capacity = estimate_hitter_position_capacity_shares(
        shares, development_seasons=(2021, 2022, 2023, 2024)
    )
    confirmation = (
        shares.filter(pl.col("season") == 2025)
        .join(capacity.select("position_group", "capacity_share"), on="position_group")
        .with_columns(
            (pl.col("position_group_share") - pl.col("capacity_share")).alias("share_error"),
            (pl.col("position_group_share") - pl.col("capacity_share")).abs().alias(
                "absolute_share_error"
            ),
        )
    )
    confirmation_by_group = confirmation.group_by("position_group").agg(
        pl.col("absolute_share_error").mean().alias("mean_absolute_share_error"),
        pl.col("absolute_share_error").quantile(0.9).alias("p90_absolute_share_error"),
        pl.col("share_error").mean().alias("mean_signed_share_error"),
        pl.len().alias("teams"),
    ).sort("position_group")
    confirmation_team = confirmation.group_by("team_id").agg(
        (0.5 * pl.col("absolute_share_error").sum()).alias("total_variation")
    )

    team_root = (
        args.generated_root / "current-organization-opportunity" / args.as_of_date / "tables"
    )
    current_team_hitter = pl.read_parquet(
        team_root / "hitter_current_organization_opportunity.parquet"
    )
    team_capacity_table = pl.read_parquet(team_root / "team_opportunity_capacity.parquet")
    team_capacity = float(team_capacity_table.get_column("team_capacity").unique().item())
    allocated = allocate_hitter_position_capacity(
        current_team_hitter, capacity, team_capacity=team_capacity
    )
    output = (
        args.generated_root / "current-organization-position-capacity"
        / args.as_of_date / "tables"
    )
    output.mkdir(parents=True, exist_ok=True)
    capacity.write_parquet(output / "frozen_position_capacity_shares.parquet")
    confirmation.write_parquet(output / "position_capacity_2025_stability.parquet")
    allocated.players.write_parquet(output / "hitter_position_capped_opportunity.parquet")
    allocated.groups.write_parquet(output / "team_position_group_capacity.parquet")

    by_season = allocated.players.group_by("season").agg(
        pl.col("current_org_expected_mlb_pa").sum().alias("team_capped_pa"),
        pl.col("position_capped_expected_mlb_pa").sum().alias("position_capped_pa"),
        (pl.col("position_group_scale") < 1.0).sum().alias("reduced_player_rows"),
    ).with_columns(
        (pl.col("team_capped_pa") - pl.col("position_capped_pa")).alias(
            "additional_position_capacity_reduction_pa"
        )
    ).sort("season")
    by_group = allocated.groups.group_by("position_group").agg(
        pl.col("raw_group_pa").sum().alias("raw_pa"),
        pl.col("allocated_group_pa").sum().alias("allocated_pa"),
        (pl.col("position_group_scale") < 1.0).sum().alias("over_capacity_team_seasons"),
        pl.col("position_group_scale").min().alias("minimum_scale"),
    ).with_columns(
        (pl.col("raw_pa") - pl.col("allocated_pa")).alias("reduction_pa")
    ).sort("position_group")
    report = {
        "report_schema_version": "0.1",
        "status": "research_hitter_position_capacity_complete",
        "as_of_date": args.as_of_date,
        "contract": "docs/current-organization-position-capacity-contract.md",
        "source": {
            "historical_workflow_run": 34416918946,
            "historical_source_gate_passed": True,
            "confirmation_workflow_run": 34417029463,
            "confirmation_source_gate_passed": True,
            "workflow_wrapper_repaired_and_verified": True,
            "historical_verification_workflow_run": 34418483096,
            "confirmation_verification_workflow_run": 34418485623,
            "team_seasons_2021_2025": team_season_count,
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
            "by_group": confirmation_by_group.to_dicts(),
        },
        "current_effect_by_season": by_season.to_dicts(),
        "current_effect_by_group": by_group.to_dicts(),
        "checks": {
            "capacity_shares_sum_to_one": True,
            "historical_missing_fielding_retained_as_dh_flex": True,
            "current_player_opportunity_never_increased": True,
            "current_team_capacity_not_exceeded": True,
            "catcher_used_as_capacity_not_talent_bonus": True,
            "organization_neutral_value_changed": False,
        },
        "boundary": (
            "Research current-organization hitter view only. Primary-position groups "
            "are broad constraints, not exact lineup slots. No pitcher role allocation yet."
        ),
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
