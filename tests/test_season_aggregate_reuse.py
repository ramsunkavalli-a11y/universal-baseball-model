from __future__ import annotations

import polars as pl

from universal_baseball.season_stats import (
    standardize_armstjc_season_stats,
    with_batting_pa_residual,
)


def test_certified_batting_auxiliary_fields_are_standardized() -> None:
    raw = pl.DataFrame(
        {
            "season": [2024],
            "team_id": [452],
            "team_league_id": [113],
            "player_id": [670190],
            "batting_PA": [247],
            "batting_AB": [212],
            "batting_BB": [29],
            "batting_HBP": [4],
            "batting_SH": [1],
            "batting_SF": [0],
            "batting_CI": [0],
            "batting_GO": [60],
            "batting_AO": [55],
            "batting_pitches_faced": [900],
        }
    )

    result, _ = standardize_armstjc_season_stats(raw, "batting")

    assert result.get_column("batting_ground_outs").to_list() == [60]
    assert result.get_column("batting_air_outs").to_list() == [55]
    assert result.get_column("batting_pitches_seen").to_list() == [900]


def test_certified_pitching_auxiliary_fields_are_standardized() -> None:
    raw = pl.DataFrame(
        {
            "season": [2024],
            "team_id": [1],
            "team_league_id": [109],
            "player_id": [2],
            "pitching_BF": [500],
            "pitching_GO": [120],
            "pitching_AO": [100],
            "pitching_PI": [1800],
        }
    )

    result, _ = standardize_armstjc_season_stats(raw, "pitching")

    assert result.get_column("pitching_ground_outs").to_list() == [120]
    assert result.get_column("pitching_air_outs").to_list() == [100]
    assert result.get_column("pitching_pitches_thrown").to_list() == [1800]


def test_batting_pa_residual_preserves_rare_unexplained_pa() -> None:
    frame = pl.DataFrame(
        {
            "batting_plate_appearances": [247, 100],
            "batting_at_bats": [212, 80],
            "batting_base_on_balls": [29, 15],
            "batting_hit_by_pitch": [4, 2],
            "batting_sac_bunts": [1, 1],
            "batting_sac_flies": [0, 2],
            "batting_catchers_interference_reached": [0, 0],
        }
    )

    result = with_batting_pa_residual(frame)

    assert result.get_column("batting_other_plate_appearances").to_list() == [1, 0]


def test_batting_pa_residual_is_not_clamped_when_source_is_inconsistent() -> None:
    frame = pl.DataFrame(
        {
            "batting_plate_appearances": [9],
            "batting_at_bats": [10],
            "batting_base_on_balls": [0],
            "batting_hit_by_pitch": [0],
            "batting_sac_bunts": [0],
            "batting_sac_flies": [0],
            "batting_catchers_interference_reached": [0],
        }
    )

    result = with_batting_pa_residual(frame)

    assert result.get_column("batting_other_plate_appearances").to_list() == [-1]
