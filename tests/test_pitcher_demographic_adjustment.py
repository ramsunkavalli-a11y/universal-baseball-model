from __future__ import annotations

import polars as pl

from universal_baseball.pitcher_demographic_adjustment import (
    COMPONENTS,
    apply_pitcher_demographic_adjustment,
    build_pitcher_age_level_features,
)


def test_build_age_relative_features_uses_latest_dominant_level() -> None:
    history = pl.DataFrame(
        {
            "season": [2024, 2024, 2024, 2024, 2023],
            "player_id": [1, 2, 3, 1, 1],
            "level_group": ["AA", "AA", "AA", "AAA", "SINGLE_A"],
            "reported_age": [20.0, 23.0, 26.0, 20.0, 19.0],
            "batters_faced": [100, 100, 100, 20, 200],
        }
    )
    demographics = pl.DataFrame(
        {"player_id": [1, 2, 3], "pitch_hand": ["L", "R", "R"]}
    )
    result = build_pitcher_age_level_features(
        history, demographics, pl.DataFrame({"player_id": [1, 2, 3]}),
        current_season=2024,
    )
    first = result.filter(pl.col("player_id") == 1).row(0, named=True)
    assert first["level_group"] == "AA"
    assert first["age_relative"] == -1.0
    assert first["left_handed"] == 1.0
    assert first["age_x_left"] == -1.0


def test_component_adjustment_is_coherent_and_bounded_to_evidence() -> None:
    profiles = pl.DataFrame(
        {
            "player_id": [1, 2],
            "weighted_affiliated_exposure": [100.0, 0.0],
            "affiliated_reliability": [0.2, 0.0],
            "p_so": [0.25, 0.25],
            "p_ubb": [0.08, 0.08],
            "p_hbp": [0.01, 0.01],
            "p_hr": [0.03, 0.03],
            "p_other": [0.63, 0.63],
        }
    )
    features = pl.DataFrame(
        {
            "player_id": [1, 2],
            "age_relative": [-1.0, -1.0],
            "left_handed": [0.0, 0.0],
            "age_x_left": [0.0, 0.0],
            "age_level_feature_available": [True, True],
        }
    )
    result = apply_pitcher_demographic_adjustment(profiles, features)
    first = result.filter(pl.col("player_id") == 1).row(0, named=True)
    second = result.filter(pl.col("player_id") == 2).row(0, named=True)
    assert first["pitcher_demographic_adjustment_applied"]
    assert first["p_so"] > 0.25
    assert not second["pitcher_demographic_adjustment_applied"]
    assert second["p_so"] == 0.25
    assert abs(sum(float(first[f"p_{value}"]) for value in COMPONENTS) - 1.0) < 1e-12


def test_missing_age_level_feature_leaves_profile_unchanged() -> None:
    profiles = pl.DataFrame(
        {
            "player_id": [1],
            "weighted_affiliated_exposure": [100.0],
            "p_so": [0.25], "p_ubb": [0.08], "p_hbp": [0.01],
            "p_hr": [0.03], "p_other": [0.63],
        }
    )
    features = pl.DataFrame(
        {
            "player_id": [1], "age_relative": [0.0], "left_handed": [1.0],
            "age_x_left": [0.0], "age_level_feature_available": [False],
        }
    )
    result = apply_pitcher_demographic_adjustment(profiles, features)
    assert result.item(0, "p_so") == 0.25
    assert not result.item(0, "pitcher_demographic_adjustment_applied")
