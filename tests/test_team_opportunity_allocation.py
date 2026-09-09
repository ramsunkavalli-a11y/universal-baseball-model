import polars as pl
import pytest

from universal_baseball.team_opportunity_allocation import (
    allocate_hitter_position_capacity,
    allocate_current_organization_opportunity,
    estimate_hitter_position_capacity_shares,
    historical_hitter_position_shares,
)


def _paths(column: str, values: list[float]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1, 2, 3], "season": [2027] * 3,
            column: values, "is_controlled_season": [True, True, False],
        }
    )


def _ownership() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1, 2, 3], "control_year": [2027] * 3,
            "organization_id": [10, 10, 10],
        }
    )


def test_team_capacity_scales_down_only_and_closes_with_unassigned_share() -> None:
    result = allocate_current_organization_opportunity(
        _paths("expected_mlb_pa", [70.0, 50.0, 90.0]),
        _paths("expected_mlb_bf", [30.0, 20.0, 90.0]),
        _ownership(), team_capacity=100.0, expected_organizations=1,
    )
    assert result.hitter.get_column("current_org_expected_mlb_pa").sum() == 100.0
    assert result.pitcher.get_column("current_org_expected_mlb_bf").sum() == 50.0
    assert result.teams.item(0, "unassigned_hitter_workload") == 0.0
    assert result.teams.item(0, "unassigned_pitcher_workload") == 50.0
    assert result.teams.item(0, "hitter_closure_residual") == 0.0
    assert result.teams.item(0, "pitcher_closure_residual") == 0.0
    assert 3 not in result.hitter.get_column("player_id").to_list()


def test_team_allocation_rejects_duplicate_player_season() -> None:
    hitter = pl.concat([
        _paths("expected_mlb_pa", [10.0, 20.0, 30.0]),
        _paths("expected_mlb_pa", [10.0, 20.0, 30.0]).head(1),
    ])
    with pytest.raises(ValueError, match="duplicate"):
        allocate_current_organization_opportunity(
            hitter, _paths("expected_mlb_bf", [10.0, 20.0, 30.0]),
            _ownership(), team_capacity=100.0, expected_organizations=1,
        )


def test_team_allocation_rejects_negative_workload() -> None:
    with pytest.raises(ValueError, match="invalid workload"):
        allocate_current_organization_opportunity(
            _paths("expected_mlb_pa", [-1.0, 20.0, 30.0]),
            _paths("expected_mlb_bf", [10.0, 20.0, 30.0]),
            _ownership(), team_capacity=100.0, expected_organizations=1,
        )


def test_historical_position_capacity_keeps_missing_fielding_in_flex() -> None:
    fielding = pl.DataFrame(
        {
            "season": [2021, 2021], "level_group": ["MLB", "MLB"],
            "team_id": [10, 10], "player_id": [1, 1],
            "position_abbreviation": ["C", "1B"], "games_started": [5, 5],
            "games_played": [6, 6], "fielding_outs": [100, 90],
        }
    )
    hitting = pl.DataFrame(
        {
            "season": [2021, 2021], "stat_group": ["hitting", "hitting"],
            "sport_id": [1, 1], "team_id": [10, 10], "player_id": [1, 2],
            "plate_appearances": [60, 40],
        }
    )
    shares = historical_hitter_position_shares(fielding, hitting)
    lookup = dict(shares.select("position_group", "position_group_pa").iter_rows())
    assert lookup["CATCHER"] == 60.0
    assert lookup["DH_FLEX"] == 40.0


def test_position_capacity_normalizes_medians_and_never_scales_up() -> None:
    history = pl.DataFrame(
        {
            "season": [2021] * 5, "team_id": [10] * 5,
            "position_group": [
                "CATCHER", "MIDDLE_INFIELD", "CORNER_INFIELD", "OUTFIELD", "DH_FLEX"
            ],
            "position_group_share": [0.1, 0.2, 0.2, 0.4, 0.1],
        }
    )
    capacity = estimate_hitter_position_capacity_shares(
        history, development_seasons=(2021,)
    )
    current = pl.DataFrame(
        {
            "player_id": [1, 2], "season": [2027, 2027],
            "organization_id": [10, 10], "primary_position": ["C", "SS"],
            "current_org_expected_mlb_pa": [20.0, 10.0],
        }
    )
    result = allocate_hitter_position_capacity(
        current, capacity, team_capacity=100.0
    )
    catcher = result.players.filter(pl.col("player_id") == 1)
    middle = result.players.filter(pl.col("player_id") == 2)
    assert abs(catcher.item(0, "position_capped_expected_mlb_pa") - 10.0) < 1e-12
    assert abs(middle.item(0, "position_capped_expected_mlb_pa") - 10.0) < 1e-12
    assert abs(capacity.get_column("capacity_share").sum() - 1.0) < 1e-12
    assert abs(result.groups.get_column("group_capacity_pa").sum() - 100.0) < 1e-12
