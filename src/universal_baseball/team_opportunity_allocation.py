"""Conservative current-organization opportunity capacity allocation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from scipy.optimize import LinearConstraint, minimize


POSITION_GROUPS = (
    "CATCHER", "MIDDLE_INFIELD", "CORNER_INFIELD", "OUTFIELD", "DH_FLEX"
)
PITCHER_ROLE_GROUPS = ("STARTER", "SWINGMAN", "RELIEVER")
PITCHER_ROLE_PROBABILITIES = {
    "STARTER": "starter_probability_if_active",
    "SWINGMAN": "swingman_probability_if_active",
    "RELIEVER": "reliever_probability_if_active",
}
POSITION_ORDER = {value: index for index, value in enumerate(
    ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH")
)}


def position_group(value: object) -> str:
    position = str(value or "").upper()
    if position == "C":
        return "CATCHER"
    if position in {"2B", "SS"}:
        return "MIDDLE_INFIELD"
    if position in {"1B", "3B"}:
        return "CORNER_INFIELD"
    if position in {"LF", "CF", "RF", "OF"}:
        return "OUTFIELD"
    return "DH_FLEX"


@dataclass(frozen=True, slots=True)
class TeamOpportunityAllocation:
    hitter: pl.DataFrame
    pitcher: pl.DataFrame
    teams: pl.DataFrame


@dataclass(frozen=True, slots=True)
class PositionCapacityAllocation:
    players: pl.DataFrame
    groups: pl.DataFrame


@dataclass(frozen=True, slots=True)
class PitcherRoleCapacityAllocation:
    players: pl.DataFrame
    components: pl.DataFrame
    groups: pl.DataFrame


@dataclass(frozen=True, slots=True)
class FlexibleCapacityAllocation:
    players: pl.DataFrame
    groups: pl.DataFrame
    flows: pl.DataFrame


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


def historical_hitter_position_shares(
    fielding_usage: pl.DataFrame, hitting_stats: pl.DataFrame
) -> pl.DataFrame:
    """Attribute team PA to a deterministic observed primary position group."""

    fielding_required = {
        "season", "level_group", "team_id", "player_id", "position_abbreviation",
        "games_started", "games_played", "fielding_outs",
    }
    hitting_required = {
        "season", "stat_group", "sport_id", "team_id", "player_id", "plate_appearances"
    }
    if missing := sorted(fielding_required - set(fielding_usage.columns)):
        raise ValueError(f"fielding usage missing fields: {missing}")
    if missing := sorted(hitting_required - set(hitting_stats.columns)):
        raise ValueError(f"hitting stats missing fields: {missing}")
    fielding = (
        fielding_usage.filter(
            (pl.col("level_group") == "MLB")
            & pl.col("position_abbreviation").is_in(list(POSITION_ORDER))
        )
        .with_columns(
            pl.col("position_abbreviation").replace_strict(
                POSITION_ORDER, return_dtype=pl.Int64
            ).alias("position_order")
        )
        .sort(
            ["season", "team_id", "player_id", "games_started", "games_played",
             "fielding_outs", "position_order"],
            descending=[False, False, False, True, True, True, False],
        )
        .unique(["season", "team_id", "player_id"], keep="first", maintain_order=True)
        .select("season", "team_id", "player_id", "position_abbreviation")
    )
    hitting = (
        hitting_stats.filter(
            (pl.col("sport_id") == 1)
            & (pl.col("stat_group") == "hitting")
            & (pl.col("plate_appearances") > 0)
        )
        .group_by("season", "team_id", "player_id")
        .agg(pl.col("plate_appearances").sum().cast(pl.Float64).alias("plate_appearances"))
    )
    attributed = hitting.join(
        fielding, on=["season", "team_id", "player_id"], how="left", validate="1:1"
    ).with_columns(
        pl.col("position_abbreviation").map_elements(
            position_group, return_dtype=pl.String, skip_nulls=False
        ).alias("position_group")
    )
    totals = attributed.group_by("season", "team_id").agg(
        pl.col("plate_appearances").sum().alias("team_pa")
    )
    grouped = attributed.group_by("season", "team_id", "position_group").agg(
        pl.col("plate_appearances").sum().alias("position_group_pa")
    )
    universe = totals.select("season", "team_id").join(
        pl.DataFrame({"position_group": POSITION_GROUPS}), how="cross"
    )
    return (
        universe.join(grouped, on=["season", "team_id", "position_group"], how="left")
        .join(totals, on=["season", "team_id"], how="left", validate="m:1")
        .with_columns(pl.col("position_group_pa").fill_null(0.0))
        .with_columns(
            (pl.col("position_group_pa") / pl.col("team_pa")).alias("position_group_share")
        )
        .sort("season", "team_id", "position_group")
    )


def estimate_hitter_position_capacity_shares(
    historical_shares: pl.DataFrame, *, development_seasons: tuple[int, ...]
) -> pl.DataFrame:
    """Freeze normalized median group shares using development seasons only."""

    required = {"season", "position_group", "position_group_share"}
    if missing := sorted(required - set(historical_shares.columns)):
        raise ValueError(f"historical position shares missing fields: {missing}")
    development = historical_shares.filter(pl.col("season").is_in(development_seasons))
    if development.is_empty():
        raise ValueError("position-capacity development evidence is empty")
    medians = development.group_by("position_group").agg(
        pl.col("position_group_share").median().alias("raw_median_share"),
        pl.col("position_group_share").quantile(0.1).alias("share_p10"),
        pl.col("position_group_share").quantile(0.9).alias("share_p90"),
        pl.len().alias("team_seasons"),
    )
    if set(medians.get_column("position_group")) != set(POSITION_GROUPS):
        raise ValueError("development evidence does not cover every position group")
    total = float(medians.get_column("raw_median_share").sum())
    if total <= 0:
        raise ValueError("position-capacity median shares have zero total")
    return medians.with_columns(
        (pl.col("raw_median_share") / total).alias("capacity_share")
    ).sort("position_group")


def allocate_hitter_position_capacity(
    current_team_hitter: pl.DataFrame,
    capacity_shares: pl.DataFrame,
    *,
    team_capacity: float,
) -> PositionCapacityAllocation:
    """Scale down over-cap controlled primary-position groups; never scale up."""

    required = {
        "player_id", "season", "organization_id", "primary_position",
        "current_org_expected_mlb_pa",
    }
    if missing := sorted(required - set(current_team_hitter.columns)):
        raise ValueError(f"current team hitter allocation missing fields: {missing}")
    if set(capacity_shares.get_column("position_group")) != set(POSITION_GROUPS):
        raise ValueError("capacity shares do not cover every position group")
    if abs(float(capacity_shares.get_column("capacity_share").sum()) - 1.0) > 1e-12:
        raise ValueError("position capacity shares must sum to one")
    players = current_team_hitter.with_columns(
        pl.col("primary_position").map_elements(
            position_group, return_dtype=pl.String
        ).alias("position_group")
    )
    totals = players.group_by("season", "organization_id", "position_group").agg(
        pl.col("current_org_expected_mlb_pa").sum().alias("raw_group_pa")
    )
    team_keys = players.select("season", "organization_id").unique()
    groups = (
        team_keys.join(capacity_shares.select("position_group", "capacity_share"), how="cross")
        .join(totals, on=["season", "organization_id", "position_group"], how="left")
        .with_columns(pl.col("raw_group_pa").fill_null(0.0))
        .with_columns((pl.col("capacity_share") * team_capacity).alias("group_capacity_pa"))
        .with_columns(
            pl.min_horizontal("raw_group_pa", "group_capacity_pa").alias("allocated_group_pa")
        )
        .with_columns(
            pl.when(pl.col("raw_group_pa") > 0)
            .then(pl.col("allocated_group_pa") / pl.col("raw_group_pa"))
            .otherwise(1.0).alias("position_group_scale"),
            (pl.col("group_capacity_pa") - pl.col("allocated_group_pa"))
            .alias("unassigned_group_pa"),
        )
    )
    group_checks = groups.group_by("season", "organization_id").agg(
        pl.col("group_capacity_pa").sum().alias("capacity_sum"),
        pl.col("raw_group_pa").sum().alias("raw_sum"),
        pl.col("allocated_group_pa").sum().alias("allocated_sum"),
    )
    if group_checks.filter((pl.col("capacity_sum") - team_capacity).abs() > 1e-7).height:
        raise AssertionError("position group capacities do not sum to team capacity")
    if group_checks.filter(pl.col("allocated_sum") > pl.col("raw_sum") + 1e-7).height:
        raise AssertionError("position groups increased team opportunity")
    allocated = players.join(
        groups.select(
            "season", "organization_id", "position_group", "position_group_scale"
        ),
        on=["season", "organization_id", "position_group"], how="left", validate="m:1",
    ).with_columns(
        (pl.col("current_org_expected_mlb_pa") * pl.col("position_group_scale"))
        .alias("position_capped_expected_mlb_pa")
    )
    if allocated.filter(
        pl.col("position_capped_expected_mlb_pa")
        > pl.col("current_org_expected_mlb_pa") + 1e-7
    ).height:
        raise AssertionError("position capacity increased player opportunity")
    return PositionCapacityAllocation(
        players=allocated.sort("season", "organization_id", "player_id"),
        groups=groups.sort("season", "organization_id", "position_group"),
    )


def historical_pitcher_role_shares(pitching_stats: pl.DataFrame) -> pl.DataFrame:
    """Attribute observed MLB team BF to mutually exclusive pitcher roles."""

    required = {
        "season", "stat_group", "sport_id", "team_id", "player_id", "games",
        "starts", "batters_faced",
    }
    if missing := sorted(required - set(pitching_stats.columns)):
        raise ValueError(f"pitching stats missing fields: {missing}")
    pitchers = (
        pitching_stats.filter(
            (pl.col("sport_id") == 1)
            & (pl.col("stat_group") == "pitching")
            & (pl.col("batters_faced") > 0)
        )
        .group_by("season", "team_id", "player_id")
        .agg(
            pl.col("games").sum().cast(pl.Float64).alias("games"),
            pl.col("starts").sum().cast(pl.Float64).alias("starts"),
            pl.col("batters_faced").sum().cast(pl.Float64).alias("batters_faced"),
        )
        .with_columns(
            pl.when(pl.col("starts") <= 0)
            .then(pl.lit("RELIEVER"))
            .when((pl.col("games") <= 0) | (2.0 * pl.col("starts") >= pl.col("games")))
            .then(pl.lit("STARTER"))
            .otherwise(pl.lit("SWINGMAN"))
            .alias("pitcher_role")
        )
    )
    totals = pitchers.group_by("season", "team_id").agg(
        pl.col("batters_faced").sum().alias("team_bf")
    )
    grouped = pitchers.group_by("season", "team_id", "pitcher_role").agg(
        pl.col("batters_faced").sum().alias("role_bf")
    )
    universe = totals.select("season", "team_id").join(
        pl.DataFrame({"pitcher_role": PITCHER_ROLE_GROUPS}), how="cross"
    )
    return (
        universe.join(grouped, on=["season", "team_id", "pitcher_role"], how="left")
        .join(totals, on=["season", "team_id"], how="left", validate="m:1")
        .with_columns(pl.col("role_bf").fill_null(0.0))
        .with_columns((pl.col("role_bf") / pl.col("team_bf")).alias("role_share"))
        .sort("season", "team_id", "pitcher_role")
    )


def estimate_pitcher_role_capacity_shares(
    historical_shares: pl.DataFrame, *, development_seasons: tuple[int, ...]
) -> pl.DataFrame:
    """Freeze normalized median pitcher-role shares on development seasons."""

    required = {"season", "pitcher_role", "role_share"}
    if missing := sorted(required - set(historical_shares.columns)):
        raise ValueError(f"historical pitcher role shares missing fields: {missing}")
    development = historical_shares.filter(pl.col("season").is_in(development_seasons))
    if development.is_empty():
        raise ValueError("pitcher role-capacity development evidence is empty")
    medians = development.group_by("pitcher_role").agg(
        pl.col("role_share").median().alias("raw_median_share"),
        pl.col("role_share").quantile(0.1).alias("share_p10"),
        pl.col("role_share").quantile(0.9).alias("share_p90"),
        pl.len().alias("team_seasons"),
    )
    if set(medians.get_column("pitcher_role")) != set(PITCHER_ROLE_GROUPS):
        raise ValueError("development evidence does not cover every pitcher role")
    total = float(medians.get_column("raw_median_share").sum())
    if total <= 0:
        raise ValueError("pitcher role-capacity median shares have zero total")
    return medians.with_columns(
        (pl.col("raw_median_share") / total).alias("capacity_share")
    ).sort("pitcher_role")


def allocate_pitcher_role_capacity(
    current_team_pitcher: pl.DataFrame,
    capacity_shares: pl.DataFrame,
    *,
    team_capacity: float,
) -> PitcherRoleCapacityAllocation:
    """Fractionally cap controlled BF by uncertain pitcher role; never scale up."""

    required = {
        "player_id", "season", "organization_id", "current_org_expected_mlb_bf",
        *PITCHER_ROLE_PROBABILITIES.values(),
    }
    if missing := sorted(required - set(current_team_pitcher.columns)):
        raise ValueError(f"current team pitcher allocation missing fields: {missing}")
    if current_team_pitcher.group_by("player_id", "season").len().filter(
        pl.col("len") > 1
    ).height:
        raise ValueError("current team pitcher allocation duplicates a player-season")
    if set(capacity_shares.get_column("pitcher_role")) != set(PITCHER_ROLE_GROUPS):
        raise ValueError("capacity shares do not cover every pitcher role")
    if abs(float(capacity_shares.get_column("capacity_share").sum()) - 1.0) > 1e-12:
        raise ValueError("pitcher role capacity shares must sum to one")
    probability_columns = list(PITCHER_ROLE_PROBABILITIES.values())
    invalid = current_team_pitcher.filter(
        pl.any_horizontal(
            *[
                pl.col(column).is_null()
                | ~pl.col(column).is_finite()
                | (pl.col(column) < 0)
                for column in probability_columns
            ]
        )
        | (pl.sum_horizontal(*[pl.col(column) for column in probability_columns]) - 1.0)
        .abs()
        .gt(1e-7)
    )
    if not invalid.is_empty():
        raise ValueError("pitcher role probabilities are invalid or do not sum to one")

    component_frames = []
    for role, probability_column in PITCHER_ROLE_PROBABILITIES.items():
        component_frames.append(
            current_team_pitcher.select(
                "player_id", "season", "organization_id",
                pl.lit(role).alias("pitcher_role"),
                pl.col(probability_column).alias("role_probability"),
                (pl.col("current_org_expected_mlb_bf") * pl.col(probability_column))
                .alias("raw_role_bf"),
            )
        )
    components = pl.concat(component_frames)
    totals = components.group_by("season", "organization_id", "pitcher_role").agg(
        pl.col("raw_role_bf").sum().alias("raw_group_bf")
    )
    team_keys = components.select("season", "organization_id").unique()
    groups = (
        team_keys.join(capacity_shares.select("pitcher_role", "capacity_share"), how="cross")
        .join(totals, on=["season", "organization_id", "pitcher_role"], how="left")
        .with_columns(pl.col("raw_group_bf").fill_null(0.0))
        .with_columns((pl.col("capacity_share") * team_capacity).alias("group_capacity_bf"))
        .with_columns(
            pl.min_horizontal("raw_group_bf", "group_capacity_bf").alias(
                "allocated_group_bf"
            )
        )
        .with_columns(
            pl.when(pl.col("raw_group_bf") > 0)
            .then(pl.col("allocated_group_bf") / pl.col("raw_group_bf"))
            .otherwise(1.0)
            .alias("pitcher_role_scale"),
            (pl.col("group_capacity_bf") - pl.col("allocated_group_bf")).alias(
                "unassigned_group_bf"
            ),
        )
    )
    checks = groups.group_by("season", "organization_id").agg(
        pl.col("group_capacity_bf").sum().alias("capacity_sum"),
        pl.col("raw_group_bf").sum().alias("raw_sum"),
        pl.col("allocated_group_bf").sum().alias("allocated_sum"),
    )
    if checks.filter((pl.col("capacity_sum") - team_capacity).abs() > 1e-7).height:
        raise AssertionError("pitcher role capacities do not sum to team capacity")
    if checks.filter(pl.col("allocated_sum") > pl.col("raw_sum") + 1e-7).height:
        raise AssertionError("pitcher role groups increased team opportunity")
    components = (
        components.join(
            groups.select(
                "season", "organization_id", "pitcher_role", "pitcher_role_scale"
            ),
            on=["season", "organization_id", "pitcher_role"], how="left", validate="m:1",
        )
        .with_columns(
            (pl.col("raw_role_bf") * pl.col("pitcher_role_scale")).alias(
                "allocated_role_bf"
            )
        )
    )
    player_totals = components.group_by("player_id", "season", "organization_id").agg(
        pl.col("allocated_role_bf").sum().alias("role_capped_expected_mlb_bf")
    )
    players = current_team_pitcher.join(
        player_totals, on=["player_id", "season", "organization_id"],
        how="left", validate="1:1",
    )
    if players.filter(
        pl.col("role_capped_expected_mlb_bf")
        > pl.col("current_org_expected_mlb_bf") + 1e-7
    ).height:
        raise AssertionError("pitcher role capacity increased player opportunity")
    return PitcherRoleCapacityAllocation(
        players=players.sort("season", "organization_id", "player_id"),
        components=components.sort("season", "organization_id", "player_id", "pitcher_role"),
        groups=groups.sort("season", "organization_id", "pitcher_role"),
    )


def estimate_hitter_flexibility_edges(
    fielding_usage: pl.DataFrame,
    *,
    development_seasons: tuple[int, ...],
    minimum_player_seasons: int = 30,
) -> pl.DataFrame:
    """Estimate supported primary-to-secondary position-group eligibility."""

    required = {
        "season",
        "level_group",
        "team_id",
        "player_id",
        "position_abbreviation",
        "fielding_outs",
    }
    if missing := sorted(required - set(fielding_usage.columns)):
        raise ValueError(f"hitter flexibility evidence missing fields: {missing}")
    if not development_seasons or minimum_player_seasons < 1:
        raise ValueError("hitter flexibility development settings are invalid")
    usage = (
        fielding_usage.filter(
            pl.col("season").is_in(development_seasons)
            & (pl.col("level_group") == "MLB")
            & pl.col("position_abbreviation").is_in(list(POSITION_ORDER))
            & (pl.col("fielding_outs") > 0)
        )
        .with_columns(
            pl.col("position_abbreviation")
            .map_elements(position_group, return_dtype=pl.String)
            .alias("destination_group")
        )
        .group_by("season", "team_id", "player_id", "destination_group")
        .agg(pl.col("fielding_outs").sum().alias("group_outs"))
    )
    primary = (
        usage.sort(
            ["season", "team_id", "player_id", "group_outs", "destination_group"],
            descending=[False, False, False, True, False],
        )
        .unique(["season", "team_id", "player_id"], keep="first", maintain_order=True)
        .select(
            "season",
            "team_id",
            "player_id",
            pl.col("destination_group").alias("origin_group"),
        )
    )
    support = usage.join(
        primary, on=["season", "team_id", "player_id"], validate="m:1"
    ).group_by("origin_group", "destination_group").agg(
        pl.len().alias("player_seasons"),
        pl.col("group_outs").sum().alias("fielding_outs"),
    )
    universe = pl.DataFrame({"origin_group": POSITION_GROUPS}).join(
        pl.DataFrame({"destination_group": POSITION_GROUPS}), how="cross"
    )
    return (
        universe.join(support, on=["origin_group", "destination_group"], how="left")
        .with_columns(
            pl.col("player_seasons").fill_null(0),
            pl.col("fielding_outs").fill_null(0),
        )
        .with_columns(
            (
                (pl.col("origin_group") == pl.col("destination_group"))
                | (pl.col("destination_group") == "DH_FLEX")
                | (
                    (pl.col("origin_group") != "DH_FLEX")
                    & (pl.col("player_seasons") >= minimum_player_seasons)
                )
            ).alias("eligible")
        )
        .sort("origin_group", "destination_group")
    )


def estimate_pitcher_role_flexibility_edges(
    pitching_stats: pl.DataFrame,
    *,
    development_seasons: tuple[int, ...],
    minimum_players: int = 30,
) -> pl.DataFrame:
    """Estimate supported adjacent-season pitcher-role transitions."""

    required = {
        "season",
        "stat_group",
        "sport_id",
        "player_id",
        "games",
        "starts",
        "batters_faced",
    }
    if missing := sorted(required - set(pitching_stats.columns)):
        raise ValueError(f"pitcher flexibility evidence missing fields: {missing}")
    if not development_seasons or minimum_players < 1:
        raise ValueError("pitcher flexibility development settings are invalid")
    roles = (
        pitching_stats.filter(
            pl.col("season").is_in(development_seasons)
            & (pl.col("sport_id") == 1)
            & (pl.col("stat_group") == "pitching")
            & (pl.col("batters_faced") > 0)
        )
        .group_by("season", "player_id")
        .agg(
            pl.col("games").sum().alias("games"),
            pl.col("starts").sum().alias("starts"),
            pl.col("batters_faced").sum().alias("batters_faced"),
        )
        .with_columns(
            pl.when(pl.col("starts") <= 0)
            .then(pl.lit("RELIEVER"))
            .when((pl.col("games") <= 0) | (2.0 * pl.col("starts") >= pl.col("games")))
            .then(pl.lit("STARTER"))
            .otherwise(pl.lit("SWINGMAN"))
            .alias("origin_group")
        )
    )
    following = roles.select(
        "player_id",
        (pl.col("season") - 1).alias("season"),
        pl.col("origin_group").alias("destination_group"),
    )
    support = roles.join(following, on=["season", "player_id"], how="inner").group_by(
        "origin_group", "destination_group"
    ).agg(pl.col("player_id").n_unique().alias("players"))
    universe = pl.DataFrame({"origin_group": PITCHER_ROLE_GROUPS}).join(
        pl.DataFrame({"destination_group": PITCHER_ROLE_GROUPS}), how="cross"
    )
    return (
        universe.join(support, on=["origin_group", "destination_group"], how="left")
        .with_columns(pl.col("players").fill_null(0))
        .with_columns(
            (
                (pl.col("origin_group") == pl.col("destination_group"))
                | (pl.col("players") >= minimum_players)
            ).alias("eligible")
        )
        .sort("origin_group", "destination_group")
    )


def _flexible_group_solution(
    supplies: dict[str, float],
    capacities: dict[str, float],
    eligible_edges: set[tuple[str, str]],
) -> tuple[dict[str, float], list[dict[str, object]]]:
    edges = sorted(
        (origin, destination)
        for origin, supply in supplies.items()
        for destination in capacities
        if supply > 0 and (origin, destination) in eligible_edges
    )
    if any(
        supply > 0 and not any(origin == edge[0] for edge in edges)
        for origin, supply in supplies.items()
    ):
        raise ValueError("a positive-supply group has no eligible capacity")
    if not edges:
        return {group: 0.0 for group in supplies}, []
    origins = sorted(group for group, supply in supplies.items() if supply > 0)
    destinations = sorted(capacities)
    origin_matrix = np.asarray(
        [[float(edge[0] == origin) for edge in edges] for origin in origins]
    )
    destination_matrix = np.asarray(
        [[float(edge[1] == destination) for edge in edges] for destination in destinations]
    )
    supply_vector = np.asarray([supplies[group] for group in origins], dtype=float)
    capacity_vector = np.asarray([capacities[group] for group in destinations], dtype=float)

    def objective(values: np.ndarray) -> float:
        retained = origin_matrix @ values
        denominators = np.maximum(supply_vector, 1.0)
        return float(np.sum(np.square(retained - supply_vector) / denominators))

    def gradient(values: np.ndarray) -> np.ndarray:
        retained = origin_matrix @ values
        denominators = np.maximum(supply_vector, 1.0)
        return 2.0 * origin_matrix.T @ ((retained - supply_vector) / denominators)

    constraints = (
        LinearConstraint(origin_matrix, np.zeros(len(origins)), supply_vector),
        LinearConstraint(
            destination_matrix, np.zeros(len(destinations)), capacity_vector
        ),
    )
    result = minimize(
        objective,
        np.zeros(len(edges), dtype=float),
        jac=gradient,
        method="SLSQP",
        bounds=[(0.0, None)] * len(edges),
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1_000},
    )
    if not result.success:
        raise RuntimeError(f"flexible capacity optimization failed: {result.message}")
    values = np.maximum(result.x, 0.0)
    retained_vector = origin_matrix @ values
    retained = {group: 0.0 for group in supplies}
    retained.update(
        {group: float(retained_vector[index]) for index, group in enumerate(origins)}
    )
    flows = [
        {
            "origin_group": origin,
            "destination_group": destination,
            "allocated_workload": float(value),
        }
        for (origin, destination), value in zip(edges, values, strict=True)
        if value > 1e-8
    ]
    return retained, flows


def allocate_flexible_group_capacity(
    players: pl.DataFrame,
    capacity_shares: pl.DataFrame,
    flexibility_edges: pl.DataFrame,
    *,
    origin_column: str,
    workload_column: str,
    output_column: str,
    capacity_group_column: str,
    team_capacity: float,
) -> FlexibleCapacityAllocation:
    """Allocate supported group flexibility before proportionally reducing supply."""

    required = {"player_id", "season", "organization_id", origin_column, workload_column}
    if missing := sorted(required - set(players.columns)):
        raise ValueError(f"flexible capacity players missing fields: {missing}")
    if team_capacity <= 0:
        raise ValueError("flexible team capacity must be positive")
    capacity = capacity_shares.select(
        pl.col(capacity_group_column).alias("group"), "capacity_share"
    )
    groups = set(capacity.get_column("group"))
    if abs(float(capacity.get_column("capacity_share").sum()) - 1.0) > 1e-10:
        raise ValueError("flexible capacity shares must sum to one")
    eligible = flexibility_edges.filter(pl.col("eligible")).select(
        "origin_group", "destination_group"
    )
    eligible_set = set(eligible.iter_rows())
    origins = set(players.get_column(origin_column).str.to_uppercase().unique())
    if origins - groups:
        raise ValueError(f"unsupported flexible capacity origins: {sorted(origins - groups)}")

    player_frames = []
    group_rows = []
    flow_rows = []
    for key, team in players.with_columns(
        pl.col(origin_column).str.to_uppercase().alias("_origin_group")
    ).group_by("season", "organization_id", maintain_order=True):
        season, organization_id = int(key[0]), int(key[1])
        supplies = {
            str(row["_origin_group"]): float(row["raw_workload"])
            for row in team.group_by("_origin_group").agg(
                pl.col(workload_column).sum().alias("raw_workload")
            ).iter_rows(named=True)
        }
        all_supplies = {group: supplies.get(group, 0.0) for group in sorted(groups)}
        capacities = {
            str(row["group"]): float(row["capacity_share"]) * team_capacity
            for row in capacity.iter_rows(named=True)
        }
        retained, flows = _flexible_group_solution(
            all_supplies, capacities, eligible_set
        )
        scales = pl.DataFrame(
            {
                "_origin_group": sorted(groups),
                "flexible_group_scale": [
                    (
                        retained[group] / all_supplies[group]
                        if all_supplies[group] > 0
                        else 1.0
                    )
                    for group in sorted(groups)
                ],
            }
        )
        allocated = team.join(scales, on="_origin_group", validate="m:1").with_columns(
            (pl.col(workload_column) * pl.col("flexible_group_scale")).alias(
                output_column
            )
        )
        player_frames.append(allocated.drop("_origin_group"))
        for group in sorted(groups):
            group_rows.append(
                {
                    "season": season,
                    "organization_id": organization_id,
                    "origin_group": group,
                    "raw_workload": all_supplies[group],
                    "allocated_workload": retained[group],
                    "group_scale": (
                        retained[group] / all_supplies[group]
                        if all_supplies[group] > 0
                        else 1.0
                    ),
                }
            )
        for flow in flows:
            flow_rows.append(
                {
                    "season": season,
                    "organization_id": organization_id,
                    **flow,
                }
            )
    allocated_players = pl.concat(player_frames).sort(
        "season", "organization_id", "player_id"
    )
    if allocated_players.filter(
        pl.col(output_column) > pl.col(workload_column) + 1e-6
    ).height:
        raise AssertionError("flexible capacity increased player opportunity")
    return FlexibleCapacityAllocation(
        players=allocated_players,
        groups=pl.DataFrame(group_rows).sort("season", "organization_id", "origin_group"),
        flows=pl.DataFrame(flow_rows).sort(
            "season", "organization_id", "origin_group", "destination_group"
        ),
    )
