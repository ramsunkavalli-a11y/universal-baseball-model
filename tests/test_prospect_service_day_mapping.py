import numpy as np
import polars as pl

from scripts.audit_prospect_service_day_mapping import _predict, _scores


def test_service_mapping_is_finite_bounded_and_monotone() -> None:
    train = pl.DataFrame(
        {
            "player_type": ["hitter"] * 20,
            "first_mlb_season": [True] * 20,
            "workload": np.arange(20, dtype=float),
            "service_days": np.arange(20, dtype=float) * 8,
        }
    )
    test = pl.DataFrame(
        {
            "player_type": ["hitter"] * 4,
            "first_mlb_season": [True] * 4,
            "workload": [-10.0, 5.0, 15.0, 100.0],
        }
    )
    prediction = _predict(train, test)
    assert np.isfinite(prediction).all()
    assert (prediction >= 0).all()
    assert (prediction <= 172).all()
    assert np.diff(prediction).min() >= 0


def test_service_scores_keep_bias_mae_and_rmse_separate() -> None:
    scores = _scores(np.array([0.0, 100.0]), np.array([20.0, 80.0]))
    assert scores == {"bias_days": 0.0, "mae_days": 20.0, "rmse_days": 20.0}
