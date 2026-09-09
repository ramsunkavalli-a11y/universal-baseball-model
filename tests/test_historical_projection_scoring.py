import polars as pl
import pytest

from universal_baseball.historical_projection_scoring import (
    score_historical_workload_projection,
    workload_comparator_metrics,
)


def test_score_retains_zero_outcomes_and_compares_prior_workload() -> None:
    projections = pl.DataFrame(
        {
            "player_id": [1, 2],
            "probability": [0.8, 0.2],
            "expected": [80.0, 20.0],
        }
    )
    outcomes = pl.DataFrame({"player_id": [1], "observed": [100]})
    prior = pl.DataFrame(
        {"player_id": [1, 2], "prior_mlb_workload": [60, 30]}
    )

    scored, metrics = score_historical_workload_projection(
        projections,
        outcomes,
        prior,
        predicted_workload_column="expected",
        participation_probability_column="probability",
        observed_workload_column="observed",
    )

    assert scored.get_column("observed").to_list() == [100.0, 0.0]
    assert metrics["players"] == 2
    assert metrics["observed_total_workload"] == 100.0
    assert metrics["workload_mae"] == 20.0
    assert metrics["prior_carry_forward_mae"] == 35.0


def test_comparator_scores_exact_common_rows() -> None:
    scored = pl.DataFrame(
        {
            "actual": [100.0, 0.0, 50.0],
            "model": [80.0, 10.0, 60.0],
            "external": [90.0, None, 80.0],
        }
    )

    metrics = workload_comparator_metrics(
        scored,
        observed_column="actual",
        model_column="model",
        comparator_column="external",
    )

    assert metrics["players"] == 2
    assert metrics["model_mae"] == 15.0
    assert metrics["comparator_mae"] == 20.0


def test_score_rejects_invalid_probabilities() -> None:
    projections = pl.DataFrame(
        {"player_id": [1], "probability": [1.2], "expected": [10.0]}
    )
    outcomes = pl.DataFrame({"player_id": [1], "observed": [5]})
    prior = pl.DataFrame({"player_id": [1], "prior_mlb_workload": [5]})

    with pytest.raises(ValueError, match="invalid values"):
        score_historical_workload_projection(
            projections,
            outcomes,
            prior,
            predicted_workload_column="expected",
            participation_probability_column="probability",
            observed_workload_column="observed",
        )
