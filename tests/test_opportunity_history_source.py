from datetime import date

import polars as pl
import pytest

from universal_baseball.opportunity_history_source import (
    AFFILIATED_SEASON_STAT_SCHEMA,
    HISTORICAL_ROSTER_DETAIL_SCHEMA,
    build_opportunity_snapshots,
    project_affiliated_season_stats_payload,
    project_historical_full_roster_payload,
)


def test_stat_projection_uses_sport_level_and_group_counts() -> None:
    payload = {
        "stats": [
            {
                "totalSplits": 1,
                "splits": [
                    {
                        "player": {"id": 10, "fullName": "Player"},
                        "sport": {"id": 11},
                        "team": {"id": 20},
                        "position": {"code": "1"},
                        "stat": {
                            "age": 24,
                            "gamesPlayed": 12,
                            "gamesStarted": 8,
                            "battersFaced": 250,
                        },
                    }
                ],
            }
        ]
    }
    result = project_affiliated_season_stats_payload(
        payload, season=2023, stat_group="pitching"
    )
    assert result.schema == AFFILIATED_SEASON_STAT_SCHEMA
    assert result.item(0, "level_group") == "AAA"
    assert result.item(0, "batters_faced") == 250


def test_roster_projection_collapses_duplicate_positions() -> None:
    payload = {
        "roster": [
            {"person": {"id": 10, "fullName": "Two Way"}, "position": {"code": "1"}},
            {"person": {"id": 10, "fullName": "Two Way"}, "position": {"code": "Y"}},
        ]
    }
    result = project_historical_full_roster_payload(
        payload, team_id=100, snapshot_date=date(2023, 10, 15)
    )
    assert result.item(0, "position_codes") == "1,Y"
    assert result.item(0, "source_row_count") == 2


def test_snapshot_builder_keeps_inactive_and_two_way_players() -> None:
    roster = pl.DataFrame(
        [
            {"snapshot_date": date(2023, 10, 15), "snapshot_year": 2023, "candidate_organization_id": 100, "player_id": 1, "player_name": "Two Way", "position_codes": "Y", "source_row_count": 1},
            {"snapshot_date": date(2023, 10, 15), "snapshot_year": 2023, "candidate_organization_id": 100, "player_id": 2, "player_name": "Inactive Hitter", "position_codes": "6", "source_row_count": 1},
            {"snapshot_date": date(2023, 10, 15), "snapshot_year": 2023, "candidate_organization_id": 100, "player_id": 3, "player_name": "Pitcher", "position_codes": "1", "source_row_count": 1},
        ],
        schema=HISTORICAL_ROSTER_DETAIL_SCHEMA,
    )
    stats = pl.DataFrame(
        [
            {"season": 2023, "stat_group": "hitting", "player_id": 1, "player_name": "Two Way", "sport_id": 1, "level_group": "MLB", "team_id": 100, "position_code": "Y", "reported_age": 28.0, "plate_appearances": 500, "games": 120, "starts": 0, "batters_faced": 0},
            {"season": 2023, "stat_group": "pitching", "player_id": 1, "player_name": "Two Way", "sport_id": 1, "level_group": "MLB", "team_id": 100, "position_code": "Y", "reported_age": 28.0, "plate_appearances": 0, "games": 20, "starts": 20, "batters_faced": 500},
            {"season": 2023, "stat_group": "pitching", "player_id": 3, "player_name": "Pitcher", "sport_id": 12, "level_group": "AA", "team_id": 101, "position_code": "1", "reported_age": 24.0, "plate_appearances": 0, "games": 30, "starts": 2, "batters_faced": 250},
            {"season": 2023, "stat_group": "hitting", "player_id": 4, "player_name": "Stats Only", "sport_id": 13, "level_group": "HIGH_A", "team_id": 102, "position_code": "6", "reported_age": 21.0, "plate_appearances": 100, "games": 25, "starts": 0, "batters_faced": 0},
        ],
        schema=AFFILIATED_SEASON_STAT_SCHEMA,
    )
    hitters, pitchers = build_opportunity_snapshots(roster, stats)
    assert hitters.get_column("player_id").to_list() == [1, 2, 4]
    assert hitters.filter(pl.col("player_id") == 2).item(0, "as_of_level_group") == "INACTIVE"
    assert pitchers.get_column("player_id").to_list() == [1, 3]
    assert pitchers.filter(pl.col("player_id") == 3).item(0, "as_of_role") == "swingman"


def test_invalid_starts_fail_source_projection() -> None:
    payload = {
        "stats": [
            {
                "splits": [
                    {
                        "player": {"id": 10},
                        "sport": {"id": 1},
                        "stat": {"gamesPlayed": 2, "gamesStarted": 3},
                    }
                ]
            }
        ]
    }
    with pytest.raises(ValueError, match="invalid counts"):
        project_affiliated_season_stats_payload(payload, season=2023, stat_group="pitching")
