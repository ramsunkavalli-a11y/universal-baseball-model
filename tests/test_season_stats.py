from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.season_stats import standardize_armstjc_season_stats


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
