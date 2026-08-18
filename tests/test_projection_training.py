from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.projection_training import (
    PREDICTED_PROJECTION_DELTA_COLUMNS,
    PROJECTION_DELTA_COLUMNS,
    apply_projection_ilr_delta,
    build_projection_scoring_pair,
    build_projection_training_response,
)
from universal_baseball.projection_validation import PROJECTION_V1_DEVELOPMENT_FOLDS


def _snapshot(player_ids: list[int]) -> pl.DataFrame:
    probability = 1.0 / len(ALL_CORE_BINS)
    return pl.DataFrame(
        [
            {
                "player_id": player_id,
                "core_bin": core_bin,
                "baseline2_latent_probability": probability,
            }
            for player_id in player_ids
            for core_bin in ALL_CORE_BINS
        ]
    )


def _zero_offsets() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "level_group": level,
                "core_bin": core_bin,
                "clr_environment_effect": 0.0,
            }
            for level in ("AAA", "MLB")
            for core_bin in ALL_CORE_BINS
        ]
    )


def _uniform_target(player_id: int = 1) -> tuple[pl.DataFrame, pl.DataFrame]:
    summary = pl.DataFrame(
        {
            "player_id": [player_id],
            "target_season": [2022],
            "target_league_id": [117],
            "target_level_group": ["AAA"],
            "future_core_events": [len(ALL_CORE_BINS)],
        }
    )
    profile = pl.DataFrame(
        [
            {
                "player_id": player_id,
                "target_season": 2022,
                "target_league_id": 117,
                "target_level_group": "AAA",
                "core_bin": core_bin,
                "future_occurrence_count": 1,
            }
            for core_bin in ALL_CORE_BINS
        ]
    )
    return summary, profile


def test_uniform_zero_translation_target_has_zero_ilr_change_from_uniform_b2() -> None:
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[0]
    target_summary, target_profile = _uniform_target()
    built = build_projection_training_response(
        _snapshot([1]),
        target_summary,
        target_profile,
        _zero_offsets(),
        fold=fold,
    )
    assert built.responses.height == 1
    assert built.responses.item(0, "future_core_events") == len(ALL_CORE_BINS)
    for column in PROJECTION_DELTA_COLUMNS:
        assert built.responses.item(0, column) == pytest.approx(0.0, abs=1e-12)
    assert built.metrics["future_level_used_as_predictor"] is False
    assert built.metrics["future_level_used_only_for_target_translation"] is True
    assert built.metrics["2025_accessed"] is False


def test_response_reports_snapshot_players_without_future_target_without_imputation() -> None:
    fold = PROJECTION_V1_DEVELOPMENT_FOLDS[0]
    target_summary, target_profile = _uniform_target(player_id=1)
    built = build_projection_training_response(
        _snapshot([1, 2]),
        target_summary,
        target_profile,
        _zero_offsets(),
        fold=fold,
    )
    assert built.responses.get_column("player_id").to_list() == [1]
    assert built.metrics["snapshot_without_future_core_target_count"] == 1
    assert built.metrics["zero_future_opportunity_imputed"] is False


def test_zero_predicted_ilr_delta_reproduces_frozen_b2_and_pairs_for_scoring() -> None:
    snapshot = _snapshot([1, 2])
    predicted = pl.DataFrame(
        {
            "player_id": [1, 2],
            **{
                column: [0.0, 0.0]
                for column in PREDICTED_PROJECTION_DELTA_COLUMNS
            },
        }
    )
    candidate = apply_projection_ilr_delta(snapshot, predicted)
    pair = build_projection_scoring_pair(snapshot, candidate)
    assert pair.height == 2 * len(ALL_CORE_BINS)
    max_difference = pair.select(
        (pl.col("baseline1_latent_probability") - pl.col("baseline0_latent_probability"))
        .abs()
        .max()
    ).item()
    assert max_difference == pytest.approx(0.0, abs=1e-12)
