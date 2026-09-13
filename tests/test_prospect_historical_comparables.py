from __future__ import annotations

import polars as pl

from universal_baseball.prospect_historical_comparables import (
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
