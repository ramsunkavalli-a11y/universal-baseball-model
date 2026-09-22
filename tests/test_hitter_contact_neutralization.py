from __future__ import annotations

from datetime import date, datetime

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_contact_neutralization import (
    aggregate_neutralized_contact_features,
    attach_neutralized_lags,
    multinomial_metrics,
    player_crossfit_fold,
    prepare_pitcher_terminal_contacts,
)
from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES


def test_player_crossfit_keeps_player_events_together() -> None:
    players = np.array([11, 11, 12, 12, 11, 13], dtype=np.int64)
    folds = player_crossfit_fold(players, folds=3)

    assert len(set(folds[players == 11])) == 1
    assert len(set(folds[players == 12])) == 1
    assert set(folds).issubset({0, 1, 2})


def test_multinomial_metrics_reward_the_better_probability() -> None:
    labels = np.array([0, 1], dtype=np.int8)
    good = np.full((2, len(CONTACT_OUTCOMES)), 0.01, dtype=np.float32)
    bad = good.copy()
    good[0, 0], good[1, 1] = 0.92, 0.92
    bad[0, 0], bad[1, 1] = 0.20, 0.20
    good /= good.sum(axis=1, keepdims=True)
    bad /= bad.sum(axis=1, keepdims=True)

    good_score = multinomial_metrics(labels, good)
    bad_score = multinomial_metrics(labels, bad)

    assert good_score["log_loss"] < bad_score["log_loss"]
    assert good_score["brier"] < bad_score["brier"]


def test_aggregate_neutralized_features_has_complete_cells() -> None:
    events = pl.DataFrame(
        {
            "season": [2024, 2024, 2024],
            "player_id": [1, 1, 2],
            "level": ["aaa", "aaa", "aa"],
            "core_bin": ["PULL_GB", "PULL_GB", "CENTER_LD"],
            "canonical_outcome": ["1B", "OTHER_OUT", "2B"],
        }
    )
    probability = np.full(
        (events.height, len(CONTACT_OUTCOMES)),
        1.0 / len(CONTACT_OUTCOMES),
        dtype=np.float32,
    )

    result = aggregate_neutralized_contact_features(events, probability)

    assert result.height == 2
    assert "neutral_cell__PULL_GB__1B" in result.columns
    assert "neutral_cell__OPPO_OFFB__HR" in result.columns
    assert result.select(pl.exclude("season", "player_id")).null_count().sum_horizontal()[0] == 0


def test_attach_neutralized_lags_rejects_protected_target() -> None:
    panel = pl.DataFrame(
        {
            "origin_year": [2025],
            "target_season": [2026],
            "player_id": [1],
        }
    )
    annual = pl.DataFrame(
        {"season": [2025], "player_id": [1], "neutral_contact_events": [100]}
    )

    with pytest.raises(ValueError, match="protected 2026"):
        attach_neutralized_lags(panel, annual)


def test_prepare_pitcher_contacts_swaps_actor_and_opponent_ids() -> None:
    terminal = pl.DataFrame(
        {
            "season": [2024],
            "level": ["aaa"],
            "game_pk": [1],
            "at_bat_index": [2],
            "terminal_pitch_number": [3],
            "league_id": [11],
            "batter": [101],
            "pitcher": [202],
            "inning": [1],
            "outs_when_up": [0],
            "on_1b": [None],
            "on_2b": [None],
            "on_3b": [None],
            "bat_score": [0],
            "fld_score": [0],
            "inning_top_bot": ["Top"],
            "stand": ["R"],
            "p_throws": ["L"],
            "bb_type": ["ground_ball"],
            "hc_x": [120.0],
            "hc_y": [150.0],
            "terminal_outcome_group": ["1B"],
            "defense_team": ["AAA"],
            "is_batted_ball": [True],
        }
    )
    context = pl.DataFrame(
        {
            "season": [2024],
            "game_pk": [1],
            "game_date": [date(2024, 6, 1)],
            "first_pitch_datetime_utc": [datetime(2024, 6, 1, 19, 0)],
            "day_night": ["night"],
            "venue_id": [10],
            "venue_latitude": [40.0],
            "venue_longitude": [-75.0],
            "turf_type": ["grass"],
            "roof_type": ["open"],
            "left_field_line_ft": [330.0],
            "center_field_ft": [400.0],
            "right_field_line_ft": [330.0],
            "weather_condition": ["clear"],
            "temperature_f": [75.0],
            "wind_mph": [5.0],
            "wind_direction": ["out"],
        }
    )

    result = prepare_pitcher_terminal_contacts(terminal, context)

    assert result["player_id"].item() == 202
    assert result["batter"].item() == 101
