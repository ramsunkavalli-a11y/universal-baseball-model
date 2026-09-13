import math

import polars as pl

from universal_baseball.established_hitter_opportunity import (
    MODEL_ID,
    apply_established_hitter_probabilities,
)


def _paths() -> pl.DataFrame:
    return pl.DataFrame({
        "player_id": [1, 2],
        "horizon": [1, 1],
        "mlb_active_probability": [0.5, 0.4],
        "conditional_mlb_pa": [300.0, 200.0],
        "conditional_war_per_600_pa": [3.0, 1.0],
        "expected_mlb_pa": [150.0, 80.0],
        "expected_war": [0.75, 2.0 / 15.0],
        "probability_model_id": ["old", "old"],
        "coverage_tier": ["old", "old"],
    })


def test_established_probability_changes_only_covered_probability_and_derived_values() -> None:
    result = apply_established_hitter_probabilities(
        _paths(),
        pl.DataFrame({
            "player_id": [1], "horizon": [1], "predicted_probability": [0.8]
        }),
    )
    covered = result.filter(pl.col("player_id") == 1)
    assert covered.item(0, "mlb_active_probability") == 0.8
    assert covered.item(0, "conditional_mlb_pa") == 300.0
    assert covered.item(0, "expected_mlb_pa") == 240.0
    assert math.isclose(covered.item(0, "expected_war"), 1.2)
    assert covered.item(0, "probability_model_id") == MODEL_ID
    uncovered = result.filter(pl.col("player_id") == 2)
    assert uncovered.item(0, "mlb_active_probability") == 0.4
    assert uncovered.item(0, "expected_mlb_pa") == 80.0
    assert uncovered.item(0, "probability_model_id") == "old"


def test_established_probability_rejects_invalid_probability() -> None:
    scores = pl.DataFrame({
        "player_id": [1], "horizon": [1], "predicted_probability": [1.1]
    })
    try:
        apply_established_hitter_probabilities(_paths(), scores)
    except ValueError as exc:
        assert "between zero and one" in str(exc)
    else:
        raise AssertionError("invalid probability was accepted")
