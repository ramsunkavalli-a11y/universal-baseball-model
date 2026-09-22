from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.pitcher_contact_value import (
    build_full_mlb_pitcher_value_targets,
    build_pitcher_contact_features,
)


def test_contact_features_reconcile_and_center_on_level_environment() -> None:
    source = pl.DataFrame(
        {
            "season": [2024, 2024],
            "player_id": [1, 2],
            "level_group": ["AAA", "AAA"],
            "batters_faced": [100, 100],
            "strike_outs": [25, 20],
            "base_on_balls": [10, 10],
            "intentional_walks": [1, 1],
            "hit_batters": [2, 2],
            "hits": [20, 30],
            "doubles": [4, 6],
            "triples": [1, 2],
            "home_runs": [3, 5],
        }
    )
    result = build_pitcher_contact_features(source)
    first = result.filter(pl.col("player_id") == 1).row(0, named=True)
    assert first["contact_single_rate"] == pytest.approx(0.12)
    assert first["contact_double_rate"] == pytest.approx(0.04)
    assert first["contact_non_hit_other_rate"] == pytest.approx(0.44)
    weighted_relative = (
        result["relative_contact_single_rate"] * 100
    ).sum()
    assert weighted_relative == pytest.approx(0.0)


def test_full_value_target_values_hit_types_and_centers_league() -> None:
    source = pl.DataFrame(
        {
            "season": [2025, 2025],
            "player_id": [1, 2],
            "pitching_bf": [100, 100],
            "pitching_so": [25, 25],
            "pitching_ubb": [8, 8],
            "pitching_hbp": [2, 2],
            "pitching_hits": [18, 28],
            "pitching_doubles": [3, 7],
            "pitching_triples": [0, 2],
            "pitching_hr": [2, 6],
        }
    )
    result = build_full_mlb_pitcher_value_targets(source)
    strong = result.filter(pl.col("player_id") == 1).row(0, named=True)
    weak = result.filter(pl.col("player_id") == 2).row(0, named=True)
    assert strong["component_war"] > weak["component_war"]
    assert result["pitching_runs_above_average_per_800"].mean() == pytest.approx(0.0)


def test_invalid_hit_breakdown_fails_loudly() -> None:
    source = pl.DataFrame(
        {
            "season": [2025],
            "player_id": [1],
            "pitching_bf": [10],
            "pitching_so": [2],
            "pitching_ubb": [1],
            "pitching_hbp": [0],
            "pitching_hits": [2],
            "pitching_doubles": [2],
            "pitching_triples": [1],
            "pitching_hr": [0],
        }
    )
    with pytest.raises(ValueError, match="hit accounting"):
        build_full_mlb_pitcher_value_targets(source)
