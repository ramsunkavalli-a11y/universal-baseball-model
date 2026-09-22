#!/usr/bin/env python3
"""Test chronology-learned weights against the fixed equal hitter ensemble."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy.optimize import minimize

from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import write_canonical_parquet


INPUT_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-ensemble-weighting-v2")
MEMBERS = (
    "direct_lightgbm",
    "three_part_lightgbm",
    "two_part_xgboost",
    "two_part_ebm",
    "two_part_ridge",
)
MEMBER_COLUMNS = tuple(f"prediction_member__{name}" for name in MEMBERS)


def _convex_weights(matrix: np.ndarray, actual: np.ndarray) -> np.ndarray:
    """Fit nonnegative weights summing to one on prior out-of-fold forecasts."""
    count = matrix.shape[1]
    initial = np.full(count, 1.0 / count)
    result = minimize(
        lambda weights: np.mean(np.square(matrix @ weights - actual)),
        initial,
        method="SLSQP",
        bounds=[(0.0, 1.0)] * count,
        constraints={"type": "eq", "fun": lambda weights: weights.sum() - 1.0},
        options={"maxiter": 1_000, "ftol": 1e-12},
    )
    if not result.success:
        raise RuntimeError(f"convex weight fit failed: {result.message}")
    return np.asarray(result.x, dtype=np.float64)


def _inverse_mse_weights(matrix: np.ndarray, actual: np.ndarray) -> np.ndarray:
    mse = np.mean(np.square(matrix - actual[:, None]), axis=0)
    raw = 1.0 / np.maximum(mse, 1e-12)
    return raw / raw.sum()


def _weights_record(weights: np.ndarray) -> dict[str, float]:
    return {name: float(value) for name, value in zip(MEMBERS, weights, strict=True)}


def main() -> None:
    frame = pl.read_parquet(INPUT_PATH).sort(
        ["origin_year", "target_season", "player_id"]
    )
    origins = sorted(frame["origin_year"].unique().to_list())
    scored_origins = origins[1:]
    prediction_frames: list[pl.DataFrame] = []
    weight_history: dict[str, object] = {}
    equal_weights = np.full(len(MEMBERS), 1.0 / len(MEMBERS))

    for origin in scored_origins:
        train = frame.filter(pl.col("origin_year") < origin)
        test = frame.filter(pl.col("origin_year") == origin)
        x_train = train.select(MEMBER_COLUMNS).to_numpy()
        y_train = train["actual_component_war"].to_numpy()
        x_test = test.select(MEMBER_COLUMNS).to_numpy()
        global_convex = _convex_weights(x_train, y_train)
        inverse_mse = _inverse_mse_weights(x_train, y_train)

        stage_prediction = np.empty(test.height, dtype=np.float64)
        stage_weights: dict[str, object] = {}
        test_stages = test["player_stage"].to_numpy()
        for stage in ("current_mlb", "upper_minors", "lower_minors"):
            train_stage = train.filter(pl.col("player_stage") == stage)
            weights = _convex_weights(
                train_stage.select(MEMBER_COLUMNS).to_numpy(),
                train_stage["actual_component_war"].to_numpy(),
            )
            mask = test_stages == stage
            stage_prediction[mask] = x_test[mask] @ weights
            stage_weights[stage] = {
                "training_rows": train_stage.height,
                "weights": _weights_record(weights),
            }

        prediction_frames.append(
            test.select(
                "origin_year",
                "target_season",
                "player_id",
                "player_stage",
                "actual_component_war",
            ).with_columns(
                pl.Series("prediction_equal", x_test @ equal_weights),
                pl.Series("prediction_inverse_mse", x_test @ inverse_mse),
                pl.Series("prediction_global_convex", x_test @ global_convex),
                pl.Series("prediction_stage_convex", stage_prediction),
            )
        )
        weight_history[str(origin)] = {
            "training_origins": [year for year in origins if year < origin],
            "global_convex": _weights_record(global_convex),
            "inverse_mse": _weights_record(inverse_mse),
            "stage_convex": stage_weights,
        }

    predictions = pl.concat(prediction_frames).sort(
        ["origin_year", "target_season", "player_id"]
    )
    actual = predictions["actual_component_war"].to_numpy()
    player_ids = predictions["player_id"].to_numpy()
    methods = ("equal", "inverse_mse", "global_convex", "stage_convex")
    pooled = {
        method: regression_metrics(
            actual, predictions[f"prediction_{method}"].to_numpy()
        )
        for method in methods
    }
    comparisons = {
        f"{method}_minus_equal": paired_cluster_rmse_delta(
            actual,
            predictions[f"prediction_{method}"].to_numpy(),
            predictions["prediction_equal"].to_numpy(),
            player_ids,
        )
        for method in methods
        if method != "equal"
    }
    folds = {}
    for origin in scored_origins:
        fold = predictions.filter(pl.col("origin_year") == origin)
        fold_actual = fold["actual_component_war"].to_numpy()
        folds[str(origin)] = {
            method: regression_metrics(
                fold_actual, fold[f"prediction_{method}"].to_numpy()
            )
            for method in methods
        }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        predictions,
        OUTPUT_ROOT / "predictions.parquet",
        table_name="hitter_ensemble_weighting_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "chronological_ensemble_weighting_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "first_origin_excluded": origins[0],
        "exclusion_reason": "no earlier out-of-fold forecasts exist for learning weights",
        "scored_origins": scored_origins,
        "members": list(MEMBERS),
        "methods": {
            "equal": "fixed one-fifth weight per member",
            "inverse_mse": "weights from inverse MSE on all earlier out-of-fold seasons",
            "global_convex": "nonnegative sum-to-one weights fit on earlier out-of-fold seasons",
            "stage_convex": "separate convex weights by forecast-time player stage",
        },
        "pooled_metrics": pooled,
        "paired_player_cluster_comparisons": comparisons,
        "fold_metrics": folds,
        "weight_history": weight_history,
        "decision_rule": (
            "replace equal weights only for a player-clustered RMSE improvement with "
            "no material recent-fold reversal"
        ),
        "artifact": artifact.as_record(),
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
