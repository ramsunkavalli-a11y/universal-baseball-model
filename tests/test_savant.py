from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.savant import (
    project_savant_performance_rows,
    read_savant_csv_bytes,
    savant_detail_request_path,
)


def test_request_path_preserves_mature_statcast_search_contract() -> None:
    path = savant_detail_request_path(date(2024, 6, 15), date(2024, 6, 15))
    assert path.startswith("/statcast_search/csv?all=true")
    assert "game_date_gt=2024-06-15" in path
    assert "game_date_lt=2024-06-15" in path
    assert "type=details" in path
    assert "player_type=pitcher" in path


def test_raw_csv_is_read_as_strings_before_explicit_projection() -> None:
    content = (
        "game_date,game_year,game_pk,at_bat_number,pitch_number,game_type,batter,pitcher,stand,p_throws,events,description,des,type,bb_type,hit_location,hc_x,hc_y,home_team,away_team\n"
        "2024-06-15,2024,745001,2,7,R,101,201,R,L,field_out,hit_into_play,Batter flies out.,X,fly_ball,8,80.0,100.0,SF,LAD\n"
    ).encode()
    raw = read_savant_csv_bytes(content)
    assert raw.schema["game_pk"] == pl.String
    projected = project_savant_performance_rows(raw)
    row = projected.to_dicts()[0]
    assert row["game_pk"] == 745001
    assert row["source_at_bat_number"] == 2
    assert row["at_bat_index"] == 1
    assert row["pitch_number"] == 7
    assert row["batter_mlbam_id"] == 101
    assert row["batter_side"] == "R"
    assert row["is_terminal_event"] is True
    assert row["is_plate_appearance_terminal"] is True
    assert row["is_contact"] is True
    assert row["source_bb_type"] == "fly_ball"
    assert row["bb_type"] == "fly_ball"
    assert row["hc_x"] == 80.0


def test_bunt_narrative_restores_canonical_bunt_trajectory() -> None:
    raw = pl.DataFrame(
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
            "events": ["sac_bunt"],
            "description": ["hit_into_play"],
            "des": ["Batter out on a sacrifice bunt to first baseman."],
            "type": ["X"],
            "bb_type": ["ground_ball"],
            "hit_location": ["3"],
            "hc_x": ["125.42"],
            "hc_y": ["190.0"],
            "home_team": ["SF"],
            "away_team": ["LAD"],
        }
    )
    row = project_savant_performance_rows(raw).to_dicts()[0]
    assert row["source_bb_type"] == "ground_ball"
    assert row["bb_type"] == "bunt_grounder"


def test_truncated_pa_is_terminal_source_marker_but_not_true_pa() -> None:
    raw = pl.DataFrame(
        {
            "game_date": ["2024-06-15"],
            "game_year": ["2024"],
            "game_pk": ["745001"],
            "at_bat_number": ["2"],
            "pitch_number": ["3"],
            "game_type": ["R"],
            "batter": ["101"],
            "pitcher": ["201"],
            "stand": ["R"],
            "p_throws": ["L"],
            "events": ["truncated_pa"],
            "description": ["ball"],
            "des": [None],
            "type": ["B"],
            "bb_type": [None],
            "hit_location": [None],
            "hc_x": [None],
            "hc_y": [None],
            "home_team": ["SF"],
            "away_team": ["LAD"],
        },
        schema_overrides={
            "des": pl.String,
            "bb_type": pl.String,
            "hit_location": pl.String,
            "hc_x": pl.String,
            "hc_y": pl.String,
        },
    )
    row = project_savant_performance_rows(raw).to_dicts()[0]
    assert row["is_terminal_event"] is True
    assert row["is_plate_appearance_terminal"] is False


def test_explicit_hit_by_pitch_description_recovers_missing_terminal_event() -> None:
    # 2022-05-28, game 662280, Rodolfo Castro: Savant retained the
    # full pitch sequence and explicit HBP pitch description but omitted only
    # the terminal events label. The source-wide recovery is deliberately
    # limited to that unambiguous description.
    raw = pl.DataFrame(
        {
            "game_date": ["2022-05-28"],
            "game_year": ["2022"],
            "game_pk": ["662280"],
            "at_bat_number": ["69"],
            "pitch_number": ["5"],
            "game_type": ["R"],
            "batter": ["666801"],
            "pitcher": ["661395"],
            "stand": ["S"],
            "p_throws": ["R"],
            "events": [None],
            "description": ["hit_by_pitch"],
            "des": [None],
            "type": ["B"],
            "bb_type": [None],
            "hit_location": [None],
            "hc_x": [None],
            "hc_y": [None],
            "home_team": ["SD"],
            "away_team": ["PIT"],
            "inning_topbot": ["Top"],
        },
        schema_overrides={
            "events": pl.String,
            "des": pl.String,
            "bb_type": pl.String,
            "hit_location": pl.String,
            "hc_x": pl.String,
            "hc_y": pl.String,
        },
    )
    row = project_savant_performance_rows(raw).to_dicts()[0]
    assert row["events"] == "hit_by_pitch"
    assert row["is_terminal_event"] is True
    assert row["is_plate_appearance_terminal"] is True
    assert row["is_contact"] is False


def test_nonterminal_ball_description_is_not_promoted_to_event() -> None:
    raw = pl.DataFrame(
        {
            "game_date": ["2022-05-28"],
            "game_year": ["2022"],
            "game_pk": ["662280"],
            "at_bat_number": ["69"],
            "pitch_number": ["4"],
            "game_type": ["R"],
            "batter": ["666801"],
            "pitcher": ["661395"],
            "stand": ["S"],
            "p_throws": ["R"],
            "events": [None],
            "description": ["blocked_ball"],
            "des": [None],
            "type": ["B"],
            "bb_type": [None],
            "hit_location": [None],
            "hc_x": [None],
            "hc_y": [None],
            "home_team": ["SD"],
            "away_team": ["PIT"],
            "inning_topbot": ["Top"],
        },
        schema_overrides={
            "events": pl.String,
            "des": pl.String,
            "bb_type": pl.String,
            "hit_location": pl.String,
            "hc_x": pl.String,
            "hc_y": pl.String,
        },
    )
    row = project_savant_performance_rows(raw).to_dicts()[0]
    assert row["events"] is None
    assert row["is_terminal_event"] is False
    assert row["is_plate_appearance_terminal"] is False


def test_unknown_terminal_event_fails_loudly() -> None:
    raw = pl.DataFrame(
        {
            "game_date": ["2024-06-15"],
            "game_year": ["2024"],
            "game_pk": ["745001"],
            "at_bat_number": ["2"],
            "pitch_number": ["3"],
            "game_type": ["R"],
            "batter": ["101"],
            "pitcher": ["201"],
            "stand": ["R"],
            "p_throws": ["L"],
            "events": ["future_new_event"],
            "description": ["ball"],
            "des": [None],
            "type": ["B"],
            "bb_type": [None],
            "hit_location": [None],
            "hc_x": [None],
            "hc_y": [None],
            "home_team": ["SF"],
            "away_team": ["LAD"],
        },
        schema_overrides={
            "des": pl.String,
            "bb_type": pl.String,
            "hit_location": pl.String,
            "hc_x": pl.String,
            "hc_y": pl.String,
        },
    )
    with pytest.raises(ValueError, match="unknown terminal event"):
        project_savant_performance_rows(raw)


def test_hitdata_can_preserve_contact_when_pitch_code_is_not_x() -> None:
    raw = pl.DataFrame(
        {
            "game_date": ["2024-06-15"],
            "game_year": ["2024"],
            "game_pk": ["745001"],
            "at_bat_number": ["2"],
            "pitch_number": ["7"],
            "game_type": ["R"],
            "batter": ["101"],
            "pitcher": ["201"],
            "stand": ["R"],
            "p_throws": ["L"],
            "events": ["field_out"],
            "description": ["hit_into_play"],
            "des": ["Batter grounds out."],
            "type": ["S"],
            "bb_type": ["ground_ball"],
            "hit_location": ["6"],
            "hc_x": ["125.42"],
            "hc_y": ["100.0"],
            "home_team": ["SF"],
            "away_team": ["LAD"],
        }
    )
    row = project_savant_performance_rows(raw).to_dicts()[0]
    assert row["is_contact"] is True


def test_savant_at_bat_number_must_be_positive_one_based() -> None:
    raw = pl.DataFrame(
        {
            "game_date": ["2024-06-15"],
            "game_year": ["2024"],
            "game_pk": ["745001"],
            "at_bat_number": ["0"],
            "pitch_number": ["1"],
            "game_type": ["R"],
            "batter": ["101"],
            "pitcher": ["201"],
            "stand": ["R"],
            "p_throws": ["L"],
            "events": [None],
            "description": ["called_strike"],
            "des": [None],
            "type": ["S"],
            "bb_type": [None],
            "hit_location": [None],
            "hc_x": [None],
            "hc_y": [None],
            "home_team": ["SF"],
            "away_team": ["LAD"],
        },
        schema_overrides={
            "events": pl.String,
            "des": pl.String,
            "bb_type": pl.String,
            "hit_location": pl.String,
            "hc_x": pl.String,
            "hc_y": pl.String,
        },
    )
    assert project_savant_performance_rows(raw).is_empty()


def test_non_regular_season_rows_are_structurally_filtered() -> None:
    raw = pl.DataFrame(
        {
            "game_date": ["2024-03-15"],
            "game_year": ["2024"],
            "game_pk": ["1"],
            "at_bat_number": ["1"],
            "pitch_number": ["1"],
            "game_type": ["S"],
            "batter": ["101"],
            "pitcher": ["201"],
            "stand": ["R"],
            "p_throws": ["L"],
            "events": [None],
            "description": ["called_strike"],
            "des": [None],
            "type": ["S"],
            "bb_type": [None],
            "hit_location": [None],
            "hc_x": [None],
            "hc_y": [None],
            "home_team": ["SF"],
            "away_team": ["LAD"],
        },
        schema_overrides={
            "events": pl.String,
            "des": pl.String,
            "bb_type": pl.String,
            "hit_location": pl.String,
            "hc_x": pl.String,
            "hc_y": pl.String,
        },
    )
    assert project_savant_performance_rows(raw).is_empty()
    assert project_savant_performance_rows(raw, regular_season_only=False).height == 1
