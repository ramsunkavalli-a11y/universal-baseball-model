"""Conservative current-organization opportunity capacity allocation."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True, slots=True)
class TeamOpportunityAllocation:
    hitter: pl.DataFrame
    pitcher: pl.DataFrame
    teams: pl.DataFrame


def _allocate_side(
    paths: pl.DataFrame,
    ownership: pl.DataFrame,
    *,
    workload_column: str,
    allocated_column: str,
    side: str,
    team_capacity: float,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    required = {"player_id", "season", workload_column, "is_controlled_season"}
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"{side} paths missing fields: {missing}")
    owner_required = {"player_id", "control_year", "organization_id"}
    if missing := sorted(owner_required - set(ownership.columns)):
        raise ValueError(f"ownership missing fields: {missing}")
    if paths.group_by("player_id", "season").len().filter(pl.col("len") > 1).height:
        raise ValueError(f"{side} paths duplicate a player-season")
    if ownership.group_by("player_id", "control_year").len().filter(pl.col("len") > 1).height:
        raise ValueError("ownership duplicates a player-season")
    invalid = paths.filter(
        pl.col(workload_column).is_null()
        | ~pl.col(workload_column).is_finite()
        | (pl.col(workload_column) < 0)
    )
    if not invalid.is_empty():
        raise ValueError(f"{side} paths contain invalid workload")

    controlled = (
        paths.filter(pl.col("is_controlled_season") == True)  # noqa: E712
        .join(
            ownership.select(
                "player_id", pl.col("control_year").alias("season"), "organization_id"
            ),
            on=["player_id", "season"], how="inner", validate="1:1",
        )
        .filter(pl.col("organization_id").is_not_null())
    )
    totals = controlled.group_by("organization_id", "season").agg(
        pl.col(workload_column).sum().alias(f"raw_{side}_workload")
    ).with_columns(
        pl.min_horizontal(
            pl.lit(float(team_capacity)), pl.col(f"raw_{side}_workload")
        ).alias(f"allocated_{side}_workload")
    ).with_columns(
        (
            pl.col(f"allocated_{side}_workload") / pl.col(f"raw_{side}_workload")
        ).alias(f"{side}_scale"),
        (
            pl.lit(float(team_capacity)) - pl.col(f"allocated_{side}_workload")
        ).alias(f"unassigned_{side}_workload"),
    )
    allocated = (
        controlled.join(totals, on=["organization_id", "season"], how="left", validate="m:1")
        .with_columns(
            (pl.col(workload_column) * pl.col(f"{side}_scale")).alias(allocated_column)
        )
    )
    return allocated, totals


def allocate_current_organization_opportunity(
    hitter_paths: pl.DataFrame,
    pitcher_paths: pl.DataFrame,
    ownership: pl.DataFrame,
    *,
    team_capacity: float,
    expected_organizations: int = 30,
) -> TeamOpportunityAllocation:
    """Cap known controlled workload and preserve explicit team-season open share."""

    if team_capacity <= 0:
        raise ValueError("team capacity must be positive")
    hitter, hitter_totals = _allocate_side(
        hitter_paths, ownership, workload_column="expected_mlb_pa",
        allocated_column="current_org_expected_mlb_pa", side="hitter",
        team_capacity=team_capacity,
    )
    pitcher, pitcher_totals = _allocate_side(
        pitcher_paths, ownership, workload_column="expected_mlb_bf",
        allocated_column="current_org_expected_mlb_bf", side="pitcher",
        team_capacity=team_capacity,
    )
    seasons = sorted(
        set(hitter_paths.get_column("season").to_list())
        | set(pitcher_paths.get_column("season").to_list())
    )
    organizations = sorted(
        int(value) for value in ownership.get_column("organization_id").drop_nulls().unique()
    )
    if len(organizations) != expected_organizations:
        raise ValueError(
            f"expected {expected_organizations} organizations, found {len(organizations)}"
        )
    universe = pl.DataFrame({"organization_id": organizations}).join(
        pl.DataFrame({"season": seasons}), how="cross"
    )
    teams = (
        universe.join(hitter_totals, on=["organization_id", "season"], how="left")
        .join(pitcher_totals, on=["organization_id", "season"], how="left")
        .with_columns(
            pl.col("raw_hitter_workload").fill_null(0.0),
            pl.col("allocated_hitter_workload").fill_null(0.0),
            pl.col("hitter_scale").fill_null(1.0),
            pl.col("unassigned_hitter_workload").fill_null(team_capacity),
            pl.col("raw_pitcher_workload").fill_null(0.0),
            pl.col("allocated_pitcher_workload").fill_null(0.0),
            pl.col("pitcher_scale").fill_null(1.0),
            pl.col("unassigned_pitcher_workload").fill_null(team_capacity),
            pl.lit(float(team_capacity)).alias("team_capacity"),
        )
        .with_columns(
            ((pl.col("allocated_hitter_workload") + pl.col("unassigned_hitter_workload"))
             - pl.col("team_capacity")).alias("hitter_closure_residual"),
            ((pl.col("allocated_pitcher_workload") + pl.col("unassigned_pitcher_workload"))
             - pl.col("team_capacity")).alias("pitcher_closure_residual"),
        )
        .sort("season", "organization_id")
    )
    tolerance = 1e-7
    if teams.filter(
        (pl.col("hitter_closure_residual").abs() > tolerance)
        | (pl.col("pitcher_closure_residual").abs() > tolerance)
    ).height:
        raise AssertionError("team opportunity allocation does not close")
    if hitter.filter(pl.col("current_org_expected_mlb_pa") > pl.col("expected_mlb_pa") + tolerance).height:
        raise AssertionError("hitter allocation increased player opportunity")
    if pitcher.filter(pl.col("current_org_expected_mlb_bf") > pl.col("expected_mlb_bf") + tolerance).height:
        raise AssertionError("pitcher allocation increased player opportunity")
    return TeamOpportunityAllocation(hitter=hitter, pitcher=pitcher, teams=teams)
