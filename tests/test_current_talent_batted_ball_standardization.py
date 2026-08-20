from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_standardization import (
    fit_batted_ball_feature_standardization,
    standardize_batted_ball_quality_features,
)


def _features() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "tracked_bbe_eligible": [True, True, False],
            "recency_weighted_mean_exit_velocity": [90.0, 100.0, 200.0],
            "recency_weighted_sweet_spot_share": [0.20, 0.40, 0.99],
        }
    )


def test_fit_uses_only_eligible_training_players() -> None:
    fitted = fit_batted_ball_feature_standardization(_features())

    assert fitted.fitted_player_count == 2
    assert fitted.mean_exit_velocity == pytest.approx(95.0)
    assert fitted.scale_exit_velocity == pytest.approx(5.0)
    assert fitted.mean_sweet_spot_share == pytest.approx(0.30)
    assert fitted.scale_sweet_spot_share == pytest.approx(0.10)


def test_standardization_reuses_training_parameters_on_evaluation_rows() -> None:
    fitted = fit_batted_ball_feature_standardization(_features())
    evaluation = pl.DataFrame(
        {
            "player_id": [10, 11],
            "tracked_bbe_eligible": [True, False],
            "recency_weighted_mean_exit_velocity": [105.0, 95.0],
            "recency_weighted_sweet_spot_share": [0.50, 0.30],
        }
    )

    observed = standardize_batted_ball_quality_features(evaluation, fitted)
    eligible = observed.filter(pl.col("player_id") == 10).row(0, named=True)
    ineligible = observed.filter(pl.col("player_id") == 11).row(0, named=True)

    assert eligible["z_mean_exit_velocity"] == pytest.approx(2.0)
    assert eligible["z_sweet_spot_share"] == pytest.approx(2.0)
    assert ineligible["z_mean_exit_velocity"] is None
    assert ineligible["z_sweet_spot_share"] is None


def test_chronological_snapshot_grain_preserves_as_of_date() -> None:
    training = pl.DataFrame(
        {
            "as_of_date": [date(2021, 7, 15), date(2022, 7, 15), date(2021, 7, 15)],
            "player_id": [1, 1, 2],
            "tracked_bbe_eligible": [True, True, True],
            "recency_weighted_mean_exit_velocity": [90.0, 94.0, 100.0],
            "recency_weighted_sweet_spot_share": [0.20, 0.30, 0.40],
        }
    )

    fitted = fit_batted_ball_feature_standardization(training)
    observed = standardize_batted_ball_quality_features(training, fitted)

    assert fitted.fitted_player_count == 3
    assert observed.select("as_of_date", "player_id").rows() == [
        (date(2021, 7, 15), 1),
        (date(2021, 7, 15), 2),
        (date(2022, 7, 15), 1),
    ]


def test_fit_rejects_zero_variance_feature() -> None:
    features = pl.DataFrame(
        {
            "player_id": [1, 2],
            "tracked_bbe_eligible": [True, True],
            "recency_weighted_mean_exit_velocity": [95.0, 95.0],
            "recency_weighted_sweet_spot_share": [0.20, 0.40],
        }
    )

    with pytest.raises(ValueError, match="zero variance"):
        fit_batted_ball_feature_standardization(features)


def test_fit_rejects_too_few_eligible_training_players() -> None:
    features = _features().with_columns(
        pl.when(pl.col("player_id") == 2)
        .then(False)
        .otherwise(pl.col("tracked_bbe_eligible"))
        .alias("tracked_bbe_eligible")
    )

    with pytest.raises(ValueError, match="at least two eligible"):
        fit_batted_ball_feature_standardization(features)
