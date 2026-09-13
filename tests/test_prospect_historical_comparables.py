from __future__ import annotations

import polars as pl

from universal_baseball.prospect_historical_comparables import (
    primary_exact_level,
    score_hitter_comparables,
)


def test_comparables_use_same_method_and_keep_zero_outcomes() -> None:
    reference = pl.DataFrame({
        "player_id": list(range(30)),
        "age_years": [24.0] * 30,
        "primary_level_tier": ["A_OR_BELOW"] * 30,
        "current_milb_workload": [200.0] * 30,
        "production_rate_1": [0.1] * 30,
        "production_rate_2": [0.25] * 30,
        "production_rate_3": [0.01] * 30,
        "production_rate_4": [0.04] * 30,
        "later_component_war": [0.0] * 29 + [3.0],
        "later_mlb_workload": [0.0] * 29 + [500.0],
    })
    target = reference.head(1).drop("later_component_war", "later_mlb_workload")

    result = score_hitter_comparables(reference, target, comparable_count=25).row(
        0, named=True
    )

    assert result["historical_comparable_players"] == 25
    assert 0.0 <= result["historical_arrival_rate_4y"] <= 0.04
    assert 0.0 <= result["historical_positive_component_war_4y"] <= 0.12
    assert result["historical_arrivals_4y"] in (0, 1)
    assert result["historical_expectation_identity_error"] < 1e-12


def test_comparables_separate_arrival_conditional_talent_and_expectation() -> None:
    reference = pl.DataFrame({
        "player_id": list(range(30)),
        "age_years": [20.0] * 30,
        "primary_level_tier": ["A_OR_BELOW"] * 30,
        "primary_level_group": ["SINGLE_A"] * 30,
        "current_milb_workload": [300.0] * 30,
        "production_rate_1": [0.1] * 30,
        "production_rate_2": [0.25] * 30,
        "production_rate_3": [0.01] * 30,
        "production_rate_4": [0.04] * 30,
        "later_component_war": [0.0] * 20 + [2.0] * 10,
        "later_mlb_workload": [0.0] * 20 + [1200.0] * 10,
    })
    target = reference.head(1).drop("later_component_war", "later_mlb_workload")

    result = score_hitter_comparables(reference, target, comparable_count=30).row(
        0, named=True
    )

    assert result["historical_comparable_level"] == "SINGLE_A"
    assert result["historical_arrival_rate_4y"] == 1 / 3
    assert result["historical_conditional_component_war_4y"] == 2.0
    assert result["historical_component_war_4y"] == 2 / 3
    assert result["historical_conditional_component_war_per_600"] == 1.0
    assert result["historical_expectation_identity_error"] < 1e-12


def test_primary_exact_level_ignores_brief_promotion() -> None:
    skill = pl.DataFrame({
        "player_id": [7, 7, 8, 8],
        "season": [2026, 2026, 2026, 2026],
        "level_group": ["HIGH_A", "AA", "SINGLE_A", "HIGH_A"],
        "plate_appearances": [289, 6, 100, 100],
    })

    result = primary_exact_level(
        skill, season=2026, exposure="plate_appearances"
    ).sort("player_id")

    assert result["primary_level_group"].to_list() == ["HIGH_A", "HIGH_A"]
    assert abs(result["primary_exact_level_workload_share"][0] - 289 / 295) < 1e-12
