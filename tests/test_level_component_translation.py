from __future__ import annotations

import math

import polars as pl
import pytest

from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
    score_component_profiles,
    translate_component_probabilities_to_mlb,
)


def _source() -> pl.DataFrame:
    rows = []
    for player_id, lower_good in ((1, 70), (2, 60), (3, 80)):
        rows.extend(
            [
                {"season": 2024, "player_id": player_id, "level_group": "AA", "events": 100, "good": lower_good, "other": 100 - lower_good},
                {"season": 2024, "player_id": player_id, "level_group": "AAA", "events": 100, "good": lower_good - 10, "other": 110 - lower_good},
                {"season": 2024, "player_id": player_id, "level_group": "MLB", "events": 100, "good": lower_good - 20, "other": 120 - lower_good},
            ]
        )
    return pl.DataFrame(rows)


def test_same_season_graph_translation_is_connected_and_mlb_anchored() -> None:
    fit = fit_same_season_component_translation(
        _source(), exposure_column="events", component_columns=("good", "other"),
        completed_seasons=(2024,), minimum_level_exposure=30,
    )
    assert fit.metrics["eligible_pairs"] == 9
    assert fit.metrics["connected_levels"] == ["AA", "AAA", "MLB"]
    mlb = fit.offsets.filter(pl.col("level_group") == "MLB")
    assert mlb.get_column("clr_environment_effect").abs().max() == 0.0
    aa_good = fit.offsets.filter(
        (pl.col("level_group") == "AA") & (pl.col("component") == "good")
    ).item(0, "clr_environment_effect")
    assert aa_good > 0


def test_translation_preserves_probability_and_removes_lower_level_boost() -> None:
    fit = fit_same_season_component_translation(
        _source(), exposure_column="events", component_columns=("good", "other"),
        completed_seasons=(2024,), minimum_level_exposure=30,
    )
    translated = translate_component_probabilities_to_mlb(
        {"good": 0.7, "other": 0.3}, level_group="AA", offsets=fit.offsets
    )
    assert math.isclose(sum(translated.values()), 1.0)
    assert translated["good"] < 0.7


def test_translation_fails_when_observed_level_graph_does_not_reach_mlb() -> None:
    with pytest.raises(ValueError, match="disconnected"):
        fit_same_season_component_translation(
            _source().filter(pl.col("level_group") != "MLB"),
            exposure_column="events", component_columns=("good", "other"),
            completed_seasons=(2024,), minimum_level_exposure=30,
        )


def test_translated_profiles_cover_no_history_players_with_population_prior() -> None:
    fit = fit_same_season_component_translation(
        _source(), exposure_column="events", component_columns=("good", "other"),
        completed_seasons=(2024,), minimum_level_exposure=30,
    )
    history = _source().with_columns(pl.lit(2026).alias("season"))
    reference = pl.DataFrame(
        [{"season": 2025, "player_id": 99, "level_group": "MLB", "events": 100, "good": 50, "other": 50}]
    )
    profiles = build_translated_affiliated_profiles(
        pl.DataFrame({"player_id": [1, 100]}),
        pl.concat([history, reference], how="vertical_relaxed"), fit.offsets,
        exposure_column="events", component_columns=("good", "other"),
        current_season=2026, reference_season=2025, regression_exposure=100.0,
    )
    assert profiles.height == 2
    assert profiles.filter(pl.col("player_id") == 1).item(0, "weighted_affiliated_exposure") > 0
    assert profiles.filter(pl.col("player_id") == 100).item(0, "weighted_affiliated_exposure") == 0
    probability_sums = profiles.select(
        pl.col("p_good") + pl.col("p_other")
    ).to_series()
    assert (probability_sums - 1.0).abs().max() < 1e-12


def test_component_profile_scorer_reports_proper_scores() -> None:
    predictions = pl.DataFrame(
        {"player_id": [1, 2], "p_good": [0.7, 0.4], "p_other": [0.3, 0.6]}
    )
    targets = pl.DataFrame(
        {"player_id": [1, 2], "events": [10, 20], "good": [7, 8], "other": [3, 12]}
    )
    score = score_component_profiles(
        predictions, targets, exposure_column="events",
        component_columns=("good", "other"),
    )
    assert score["players"] == 2
    assert score["target_exposure"] == 30
    assert float(score["component_log_loss"]) > 0
    assert float(score["component_brier_score"]) >= 0
