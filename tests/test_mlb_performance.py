from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.mlb_performance import (
    assign_savant_actual_league,
    summarize_savant_contacts,
    summarize_savant_terminal_outcomes,
)
from universal_baseball.mlb_season_stats import MlbTeamLeague


def _teams():
    return [
        MlbTeamLeague(1, "NYY", 103, "American League"),
        MlbTeamLeague(2, "LAD", 104, "National League"),
    ]


def _savant() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_year": [2024, 2024, 2024, 2024],
            "game_pk": [1, 1, 2, 2],
            "at_bat_index": [0, 1, 0, 1],
            "pitch_number": [3, 4, 2, 5],
            "batting_team": ["NYY", "NYY", "LAD", "LAD"],
            "batter_mlbam_id": [101, 101, 101, 202],
            "events": ["strikeout", "walk", "field_out", "hit_by_pitch"],
            "is_plate_appearance_terminal": [True, True, True, True],
            "is_contact": [False, False, True, False],
        }
    )


def test_actual_league_assignment_follows_batting_team() -> None:
    result = assign_savant_actual_league(_savant(), _teams())
    assert result.get_column("league_id").to_list() == [103, 103, 104, 104]
    assert result.get_column("batting_team_authority_abbreviation").to_list() == [
        "NYY",
        "NYY",
        "LAD",
        "LAD",
    ]


def test_season_scoped_savant_team_alias_maps_to_authority_abbreviation() -> None:
    teams = [MlbTeamLeague(133, "OAK", 103, "American League")]
    savant = _savant().head(1).with_columns(pl.lit("ATH").alias("batting_team"))
    result = assign_savant_actual_league(savant, teams)
    assert result.get_column("batting_team").to_list() == ["ATH"]
    assert result.get_column("batting_team_authority_abbreviation").to_list() == ["OAK"]
    assert result.get_column("league_id").to_list() == [103]


def test_savant_alias_does_not_apply_outside_certified_season() -> None:
    teams = [MlbTeamLeague(133, "OAK", 103, "American League")]
    savant = (
        _savant()
        .head(1)
        .with_columns(
            pl.lit(2023).alias("game_year"),
            pl.lit("ATH").alias("batting_team"),
        )
    )
    with pytest.raises(ValueError, match="absent from MLB authority"):
        assign_savant_actual_league(savant, teams)


def test_unknown_batting_team_is_hard_error() -> None:
    with pytest.raises(ValueError, match="absent from MLB authority"):
        assign_savant_actual_league(
            _savant().with_columns(
                pl.when(pl.col("game_pk") == 2)
                .then(pl.lit("XXX"))
                .otherwise(pl.col("batting_team"))
                .alias("batting_team")
            ),
            _teams(),
        )


def test_missing_batting_team_is_hard_error() -> None:
    with pytest.raises(ValueError, match="without resolvable batting team"):
        assign_savant_actual_league(
            _savant().with_columns(
                pl.when(pl.col("game_pk") == 2)
                .then(pl.lit(None, dtype=pl.String))
                .otherwise(pl.col("batting_team"))
                .alias("batting_team")
            ),
            _teams(),
        )


def test_terminal_outcomes_keep_cross_league_player_as_two_rows() -> None:
    assigned = assign_savant_actual_league(_savant(), _teams())
    result = summarize_savant_terminal_outcomes(assigned)
    player = result.filter(pl.col("player_id") == 101).sort("league_id")
    assert player.height == 2
    assert player.get_column("savant_plate_appearances").to_list() == [2, 1]
    assert player.get_column("savant_strike_outs").to_list() == [1, 0]
    assert player.get_column("savant_base_on_balls").to_list() == [1, 0]


def test_contact_summary_keeps_actual_league_grain() -> None:
    assigned = assign_savant_actual_league(_savant(), _teams())
    result = summarize_savant_contacts(assigned)
    assert result.to_dicts() == [
        {
            "season": 2024,
            "league_id": 104,
            "player_id": 101,
            "savant_contact_count": 1,
        }
    ]
