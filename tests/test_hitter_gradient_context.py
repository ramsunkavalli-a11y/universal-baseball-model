from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.hitter_gradient_context import (
    build_hitter_gradient_context_events,
    chronological_context_split,
)


def _pas() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2023, 2024, 2024],
            "game_date": [date(2023, 5, 1), date(2024, 5, 1), date(2024, 5, 1)],
            "game_pk": [10, 20, 20],
            "at_bat_index": [1, 1, 2],
            "league_id": [112, 112, 112],
            "level_group": ["AAA", "AAA", "AAA"],
            "player_id": [1, 1, 2],
            "pitcher_id": [8, 9, 9],
            "batter_side": ["L", "L", "R"],
            "pitcher_hand": ["R", "L", "L"],
            "canonical_outcome": ["2B", "HR", "K"],
            "context_label_ready": [True, True, True],
        }
    )


def _venues() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2023, 2024],
            "game_id": [10, 20],
            "venue_id": [100, 200],
            "away_team_id": [3, 4],
            "home_team_id": [5, 6],
            "venue_context_eligible": [True, True],
        }
    )


def test_context_joins_park_hand_platoon_and_terminal_contact_result() -> None:
    contacts = pl.DataFrame(
        {
            "season": [2023, 2024],
            "game_pk": [10, 20],
            "at_bat_index": [1, 1],
            "contact_bin": ["OPPO_LD", "PULL_OFFB"],
            "core_profile_eligible": [True, True],
        }
    )
    result = build_hitter_gradient_context_events(_pas(), _venues(), contacts)
    homer = result.filter(
        (pl.col("season") == 2024) & (pl.col("at_bat_index") == 1)
    ).to_dicts()[0]
    strikeout = result.filter(pl.col("canonical_outcome") == "K").to_dicts()[0]
    assert homer["park_batter_side_cell"] == "200:L"
    assert homer["platoon_cell"] == "L:L"
    assert homer["observed_contact_result_cell"] == "PULL_OFFB:HR"
    assert homer["contact_context_ready"] is True
    assert strikeout["pa_context_ready"] is True
    assert strikeout["is_contact_outcome"] is False
    assert strikeout["contact_context_ready"] is False


def test_all_pitch_contact_table_cannot_attach_contact_to_strikeout() -> None:
    contacts = pl.DataFrame(
        {
            "season": [2024],
            "game_pk": [20],
            "at_bat_index": [2],
            "contact_bin": ["IFFB"],
            "core_profile_eligible": [True],
        }
    )
    with pytest.raises(ValueError, match="non-contact or unmatched PA"):
        build_hitter_gradient_context_events(_pas(), _venues(), contacts)


def test_chronological_split_uses_only_prior_seasons_and_seals_2026() -> None:
    events = build_hitter_gradient_context_events(_pas(), _venues())
    split = chronological_context_split(events, evaluation_season=2024)
    assert split.training["season"].unique().to_list() == [2023]
    assert split.evaluation["season"].unique().to_list() == [2024]
    with pytest.raises(ValueError, match="is protected"):
        chronological_context_split(events, evaluation_season=2026)


def test_input_containing_protected_rows_fails_before_split() -> None:
    events = build_hitter_gradient_context_events(_pas(), _venues()).vstack(
        build_hitter_gradient_context_events(_pas(), _venues()).head(1).with_columns(
            pl.lit(2026, dtype=pl.Int64).alias("season")
        )
    )
    with pytest.raises(ValueError, match="contains protected season"):
        chronological_context_split(events, evaluation_season=2024)
