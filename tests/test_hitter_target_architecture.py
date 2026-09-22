import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    compose_architecture_predictions,
    expanding_year_folds,
    feature_columns,
    matrix_from_panel,
    paired_cluster_rmse_delta,
    regression_metrics,
)


def test_expanding_folds_are_chronological_and_seal_2026() -> None:
    folds = expanding_year_folds([2015, 2016, 2017, 2018, 2021])
    assert folds[0].test_origin == 2017
    assert folds[0].train_origins == (2015, 2016)
    assert folds[-1].train_origins == (2015, 2016, 2017, 2018)
    with pytest.raises(ValueError, match="before 2026"):
        expanding_year_folds([2023, 2024, 2025])


def test_features_exclude_future_outcomes_and_encode_levels() -> None:
    panel = pl.DataFrame(
        {
            "origin_year": [2023, 2024],
            "player_id": [1, 2],
            "lag0__highest_level": ["AA", None],
            "lag0__rate": [0.2, None],
            "target_component_war": [0.0, 1.0],
            "target_mlb_active": [0, 1],
            "target_mlb_pa": [0, 500],
            "target_conditional_component_war_per_600": [0.0, 1.2],
            "target_season": [2024, 2025],
        }
    )
    columns = feature_columns(panel)
    assert columns == ["lag0__highest_level", "lag0__rate"]
    matrix = matrix_from_panel(panel, columns)
    assert matrix[0, 0] == 4.0
    assert matrix[1, 0] == -1.0
    assert np.isnan(matrix[1, 1])


def test_architecture_composition_and_metrics() -> None:
    composed = compose_architecture_predictions(
        active_probability=np.array([0.5, 1.2]),
        conditional_total_war=np.array([2.0, -1.0]),
        conditional_pa=np.array([600.0, 900.0]),
        conditional_rate_per_600=np.array([2.0, 20.0]),
    )
    assert composed["two_part"].tolist() == [1.0, -1.0]
    assert composed["three_part"].tolist() == [1.0, 12.5]
    assert regression_metrics(np.array([0.0]), np.array([1.0]))["rmse"] == 1.0
    scores = classification_metrics(np.array([0, 1]), np.array([0.0, 1.0]))
    assert scores["brier"] < 1e-10


def test_paired_cluster_interval_reports_challenger_improvement() -> None:
    actual = np.array([0.0, 1.0, 0.0, 2.0])
    challenger = np.array([0.0, 1.0, 0.0, 2.0])
    reference = np.array([1.0, 0.0, 1.0, 1.0])
    result = paired_cluster_rmse_delta(
        actual,
        challenger,
        reference,
        np.array([1, 1, 2, 2]),
        bootstrap_samples=100,
    )
    assert result["rmse_delta"] == -1.0
    assert result["ci95_high"] < 0.0
