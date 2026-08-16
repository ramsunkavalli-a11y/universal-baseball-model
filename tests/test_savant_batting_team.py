from __future__ import annotations

import polars as pl

from universal_baseball.savant import project_savant_performance_rows


def _raw(topbot: str) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_date": ["2024-06-15"],
            "game_year": ["2024"],
            "game_pk": ["745001"],
            "at_bat_number": ["2"],
            "pitch_number": ["1"],
            "game_type": ["R"],
            "batter": ["101"],
            "pitcher": ["201"],
            "stand": ["R"],
            "p_throws": ["L"],
            "events": ["field_out"],
            "description": ["hit_into_play"],
            "des": ["Batter grounds out."],
            "type": ["X"],
            "bb_type": ["ground_ball"],
            "hit_location": ["6"],
            "hc_x": ["125.42"],
            "hc_y": ["100.0"],
            "inning_topbot": [topbot],
            "home_team": ["SF"],
            "away_team": ["LAD"],
        }
    )


def test_top_half_assigns_away_team_as_batting_team() -> None:
    row = project_savant_performance_rows(_raw("Top")).to_dicts()[0]
    assert row["inning_topbot"] == "Top"
    assert row["batting_team"] == "LAD"


def test_bottom_half_assigns_home_team_as_batting_team() -> None:
    row = project_savant_performance_rows(_raw("Bot")).to_dicts()[0]
    assert row["batting_team"] == "SF"


def test_unknown_half_keeps_batting_team_unresolved() -> None:
    row = project_savant_performance_rows(_raw("Middle")).to_dicts()[0]
    assert row["batting_team"] is None


def test_old_fixture_without_inning_topbot_remains_projectable() -> None:
    raw = _raw("Top").drop("inning_topbot")
    row = project_savant_performance_rows(raw).to_dicts()[0]
    assert row["inning_topbot"] is None
    assert row["batting_team"] is None
