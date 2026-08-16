from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.season_stats import (
    select_reconciliation_players,
    standardize_armstjc_season_stats,
)


def test_standardize_batting_season_stats_maps_grain_and_outcomes() -> None:
    raw = pl.DataFrame(
        {
            "season": [2026],
            "team_id": [102],
            "team_name": ["Round Rock Express"],
            "team_league_id": [112],
            "team_league": ["PCL"],
            "team_level_id": [11],
            "team_level_abv": ["AAA"],
            "player_id": [672284],
            "player_full_name": ["Example Hitter"],
            "G": [35],
            "batting_PA": [155],
            "batting_AB": [119],
            "batting_BB": [29],
            "batting_HBP": [7],
            "batting_SO": [34],
            "batting_SH": [0],
            "batting_SF": [0],
            "batting_CI": [0],
        }
    )

    standardized, report = standardize_armstjc_season_stats(raw, "batting")

    assert standardized.get_column("league_id").to_list() == [112]
    assert standardized.get_column("player_id").to_list() == [672284]
    assert standardized.get_column("batting_plate_appearances").to_list() == [155]
    assert standardized.get_column("batting_base_on_balls").to_list() == [29]
    assert standardized.get_column("batting_hit_by_pitch").to_list() == [7]
    assert standardized.get_column("batting_strike_outs").to_list() == [34]
    assert "team_league_id" not in standardized.columns
    assert report["rename_count"] > 0


def test_standardize_pitching_season_stats_does_not_invent_missing_sac_bunts() -> None:
    raw = pl.DataFrame(
        {
            "season": [2026],
            "team_id": [999],
            "team_league_id": [130],
            "player_id": [800001],
            "pitching_G": [12],
            "pitching_GS": [4],
            "pitching_BF": [140],
            "pitching_AB": [120],
            "pitching_BB": [10],
            "pitching_HBP": [3],
            "pitching_SO": [31],
            "pitching_SF": [2],
            "pitching_CI": [0],
        }
    )

    standardized, report = standardize_armstjc_season_stats(raw, "pitching")

    assert standardized.get_column("pitching_batters_faced").to_list() == [140]
    assert standardized.get_column("pitching_strike_outs").to_list() == [31]
    assert "pitching_sac_bunts" not in standardized.columns
    assert "pitching_sac_bunts" in report["absent_optional_columns"]


def test_standardize_season_stats_rejects_raw_canonical_collision() -> None:
    raw = pl.DataFrame(
        {
            "season": [2026],
            "team_id": [1],
            "team_league_id": [112],
            "league_id": [113],
            "player_id": [2],
        }
    )

    with pytest.raises(ValueError, match="refusing ambiguous rename"):
        standardize_armstjc_season_stats(raw, "batting")


def test_reconciliation_sampling_sums_multiteam_volume_and_selects_each_league() -> None:
    frame = pl.DataFrame(
        {
            "league_id": [112, 112, 112, 112, 117, 117],
            "player_id": [10, 10, 20, 30, 40, 50],
            "batting_plate_appearances": [110, 100, 205, 150, 99, 101],
        }
    )

    selected = select_reconciliation_players(frame, "batting", per_league=2)

    assert selected == [
        {"league_id": 112, "player_id": 10, "sample_volume": 210},
        {"league_id": 112, "player_id": 20, "sample_volume": 205},
        {"league_id": 117, "player_id": 50, "sample_volume": 101},
        {"league_id": 117, "player_id": 40, "sample_volume": 99},
    ]


def test_reconciliation_sampling_excludes_players_seen_in_multiple_actual_leagues() -> None:
    frame = pl.DataFrame(
        {
            "league_id": [112, 117, 112, 117],
            "player_id": [10, 10, 20, 30],
            "batting_plate_appearances": [300, 200, 150, 140],
        }
    )

    selected = select_reconciliation_players(frame, "batting")

    assert selected == [
        {"league_id": 112, "player_id": 20, "sample_volume": 150},
        {"league_id": 117, "player_id": 30, "sample_volume": 140},
    ]


def test_reconciliation_sampling_accepts_integer_like_decimal_strings() -> None:
    frame = pl.DataFrame(
        {
            "league_id": ["112.0", "112.0", "117.0"],
            "player_id": ["700001.0", "700002.0", "700003.0"],
            "pitching_batters_faced": ["525.0", "200.0", "510.0"],
        }
    )

    assert select_reconciliation_players(frame, "pitching") == [
        {"league_id": 112, "player_id": 700001, "sample_volume": 525},
        {"league_id": 117, "player_id": 700003, "sample_volume": 510},
    ]


def test_reconciliation_sampling_rejects_fractional_identifiers_or_counts() -> None:
    frame = pl.DataFrame(
        {
            "league_id": ["112.0", "112.5", "117.0"],
            "player_id": ["700001.0", "700002.0", "700003.0"],
            "pitching_batters_faced": ["525.5", "600.0", "510.0"],
        }
    )

    assert select_reconciliation_players(frame, "pitching") == [
        {"league_id": 117, "player_id": 700003, "sample_volume": 510}
    ]


def test_reconciliation_sampling_ties_break_on_player_id() -> None:
    frame = pl.DataFrame(
        {
            "league_id": [130, 130],
            "player_id": [900, 800],
            "pitching_batters_faced": [100, 100],
        }
    )

    assert select_reconciliation_players(frame, "pitching") == [
        {"league_id": 130, "player_id": 800, "sample_volume": 100}
    ]


def test_reconciliation_sampling_requires_positive_count() -> None:
    frame = pl.DataFrame(
        {
            "league_id": [130],
            "player_id": [800],
            "pitching_batters_faced": [0],
        }
    )

    assert select_reconciliation_players(frame, "pitching") == []
    with pytest.raises(ValueError, match="per_league"):
        select_reconciliation_players(frame, "pitching", per_league=0)
