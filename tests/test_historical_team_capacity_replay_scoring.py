import polars as pl

from scripts.score_historical_team_capacity_replay_2025 import (
    _cluster_bootstrap_delta,
    _metrics,
)


def test_capacity_replay_metrics_keep_bias_and_totals_visible() -> None:
    frame = pl.DataFrame({"prediction": [2.0, 4.0], "actual": [1.0, 2.0]})
    result = _metrics(frame, prediction="prediction", actual="actual")
    assert result["players"] == 2
    assert result["mae"] == 1.5
    assert result["mean_forecast_minus_actual"] == 1.5
    assert result["predicted_total"] == 6.0
    assert result["actual_total"] == 3.0
    assert result["predicted_to_actual_ratio"] == 2.0


def test_cluster_bootstrap_uses_team_clusters_and_negative_means_better() -> None:
    frame = pl.DataFrame(
        {
            "organization_id": [10, 10, 20, 20],
            "actual": [1.0, 2.0, 3.0, 4.0],
            "original": [2.0, 3.0, 4.0, 5.0],
            "challenger": [1.0, 2.0, 3.0, 4.0],
        }
    )
    result = _cluster_bootstrap_delta(
        frame, baseline="original", challenger="challenger", actual="actual",
        repetitions=100, seed=7,
    )
    assert result["clusters"] == 2
    assert result["rmse_delta"]["point"] == -1.0
    assert result["mae_delta"]["point"] == -1.0
    assert result["rmse_delta"]["ci95"] == [-1.0, -1.0]
    assert result["mae_delta"]["ci95"] == [-1.0, -1.0]

