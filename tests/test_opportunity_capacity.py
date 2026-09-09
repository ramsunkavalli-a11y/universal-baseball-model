import polars as pl

from universal_baseball.opportunity_capacity import (
    audit_projected_workload_capacity,
    historical_mlb_workload_pools,
)


def test_historical_pool_requires_pa_bf_identity() -> None:
    stats = pl.DataFrame(
        {
            "season": [2024, 2024], "stat_group": ["hitting", "pitching"],
            "sport_id": [1, 1], "plate_appearances": [100, 0],
            "batters_faced": [0, 100],
        }
    )
    result = historical_mlb_workload_pools(stats)
    assert result.item(0, "pa_minus_bf") == 0


def test_projection_audit_exposes_capacity_and_two_sided_gap() -> None:
    hitter = pl.DataFrame({"season": [2027, 2027], "expected_mlb_pa": [40.0, 50.0]})
    pitcher = pl.DataFrame({"season": [2027], "expected_mlb_bf": [80.0]})
    result = audit_projected_workload_capacity(
        hitter, pitcher, reference_league_workload=100.0
    )
    assert result.item(0, "hitter_capacity_not_exceeded")
    assert result.item(0, "hitter_pitcher_gap") == 10.0
    assert not result.item(0, "closed_system_identity_passed")
    assert result.item(0, "symmetric_shared_pool") == 85.0
    assert result.item(0, "research_hitter_scale") == 85.0 / 90.0
    assert result.item(0, "research_pitcher_scale") == 85.0 / 80.0
