import numpy as np
import polars as pl
import pytest

from universal_baseball.prospect_workload_validation import (
    build_pitcher_workload_era_scores,
    build_workload_asof_predictions,
    build_workload_holdout_predictions,
    empirical_crps,
    summarize_workload_coverage,
    wilson_interval,
)


def test_wilson_interval_contains_observed_rate() -> None:
    low, high = wilson_interval(8, 10)
    assert low < 0.8 < high
    with pytest.raises(ValueError):
        wilson_interval(2, 1)


def test_holdout_uses_only_earlier_samples_and_pooled_sparse_role() -> None:
    paths = pl.DataFrame(
        {
            "player_id": [1, 2, 3, 4],
            "player_type": ["pitcher"] * 4,
            "debut_year": [2016, 2017, 2018, 2019],
            "outcome_tier_v2": ["fringe"] * 4,
            "career_role": ["starter", "reliever", "starter", "starter"],
            "adjusted_total_workload": [100.0, 300.0, 200.0, 10000.0],
        }
    )
    result = build_workload_holdout_predictions(
        paths, minimum_role_players=2
    )
    first = result.filter(pl.col("player_id") == 3).row(0, named=True)
    assert first["sample_source"] == "pooled"
    assert first["training_players"] == 2
    assert first["predicted_p50"] == pytest.approx(200.0)
    # The later extreme cannot leak into the earlier-cohort median.
    assert result.filter(pl.col("player_id") == 4).item(0, "predicted_p50") == 200.0


def test_coverage_summary_reports_declared_targets() -> None:
    frame = pl.DataFrame(
        {
            "player_type": ["hitter"] * 4,
            "covered_80": [True, True, True, False],
            "covered_50": [True, False, True, False],
            "absolute_median_error": [1.0, 2.0, 3.0, 4.0],
        }
    )
    result = summarize_workload_coverage(frame, ["player_type"]).row(0, named=True)
    assert result["coverage_80"] == 0.75
    assert result["coverage_50"] == 0.5
    assert result["median_absolute_error"] == 2.5


def test_empirical_crps_is_zero_for_perfect_point_distribution() -> None:
    assert empirical_crps(
        samples=np.array([2.0]),
        weights=np.array([1.0]),
        observed=2.0,
    ) == 0.0


def test_pitcher_era_scores_never_use_same_or_later_debut_cohort() -> None:
    paths = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "player_type": ["pitcher"] * 3,
            "debut_year": [2015, 2016, 2017],
            "outcome_tier_v2": ["fringe"] * 3,
            "career_role": ["reliever"] * 3,
            "adjusted_total_workload": [100.0, 200.0, 10000.0],
        }
    )
    result = build_pitcher_workload_era_scores(
        paths, evaluation_years=(2017,), minimum_role_players=1
    )
    assert result["predicted_p50"].max() <= 200.0
    assert result["training_players"].max() == 2


def test_asof_workload_requires_training_window_to_end_before_evaluation() -> None:
    paths = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "player_type": ["hitter"] * 3,
            "debut_year": [2010, 2013, 2018],
            "window_end_year": [2015, 2018, 2023],
            "outcome_tier_v2": ["fringe"] * 3,
            "career_role": ["hitter"] * 3,
            "adjusted_total_workload": [100.0, 10000.0, 100.0],
        }
    )
    result = build_workload_asof_predictions(
        paths, evaluation_years=(2018,), minimum_role_players=1
    ).row(0, named=True)
    assert result["maximum_training_window_end"] == 2015
    assert result["training_players"] == 1
    assert result["predicted_p50"] == 100.0
