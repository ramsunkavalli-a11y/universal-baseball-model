from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_contact_neutralization import (
    aggregate_neutralized_contact_features,
    attach_neutralized_lags,
    multinomial_metrics,
    player_crossfit_fold,
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
