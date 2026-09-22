from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.park_factor_comparison import (
    compare_park_indexes,
    component_probability_indexes,
    unhalve_full_park_index,
)


def test_fangraphs_half_season_index_is_unhalved_around_100() -> None:
    assert unhalve_full_park_index(105) == 110
    assert unhalve_full_park_index(96) == 92


def test_clr_effects_become_renormalized_component_indexes() -> None:
    factors = pl.DataFrame(
        {
            "venue_id": [1, 1, 2, 2],
            "component": ["hit", "out", "hit", "out"],
            "park_clr_effect": [0.2, -0.2, 0.0, 0.0],
        }
    )
    result = component_probability_indexes(
        factors,
        reference_probabilities={"hit": 0.25, "out": 0.75},
        outcome_weights={"hit": 1.0, "out": 0.0},
    )
    friendly = result.filter(pl.col("venue_id") == 1).to_dicts()[0]
    neutral = result.filter(pl.col("venue_id") == 2).to_dicts()[0]
    assert friendly["ubm_hit_index"] > 100
    assert friendly["ubm_out_index"] < 100
    assert friendly["ubm_weighted_index"] == pytest.approx(
        friendly["ubm_hit_index"]
    )
    assert neutral["ubm_hit_index"] == pytest.approx(100)


def test_comparison_keeps_rank_and_magnitude_separate() -> None:
    overlap = pl.DataFrame(
        {
            "ubm": [95.0, 100.0, 105.0],
            "external": [80.0, 100.0, 120.0],
        }
    )
    result = compare_park_indexes(
        overlap, ubm_column="ubm", external_column="external"
    )
    assert result["spearman"] == pytest.approx(1.0)
    assert result["sign_agreement"] == pytest.approx(1.0)
    assert result["external_standard_deviation"] > result["ubm_standard_deviation"]
