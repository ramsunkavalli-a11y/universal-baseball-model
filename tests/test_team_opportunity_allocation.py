import polars as pl
import pytest

from universal_baseball.team_opportunity_allocation import (
    allocate_current_organization_opportunity,
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
