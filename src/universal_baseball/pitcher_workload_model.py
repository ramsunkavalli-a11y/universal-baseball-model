"""Chronology-safe next-season pitcher workload modeling."""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.hitter_target_architecture import (
    Fold,
    classification_metrics,
    feature_columns,
    matrix_from_panel,
    regression_metrics,
)
from universal_baseball.pitcher_model_tournament import to_generic_two_part_panel


def _fresh_regressor(engine: str, random_state: int) -> Any:
    return make_engine_models(engine, random_state).regressor


def run_pitcher_workload_fold(
    panel: pl.DataFrame,
    fold: Fold,
    engine: str,
    *,
    random_state: int = 417,
) -> tuple[pl.DataFrame, dict[str, dict[str, float]]]:
    """Fit MLB arrival and conditional BF, then score zero-inclusive expected BF."""

    generic = to_generic_two_part_panel(panel)
    train = generic.filter(pl.col("origin_year").is_in(fold.train_origins))
    test = generic.filter(pl.col("origin_year") == fold.test_origin)
    columns = feature_columns(generic)
    x_train = matrix_from_panel(train, columns)
    x_test = matrix_from_panel(test, columns)
    active_train = train["target_mlb_active"].to_numpy().astype(np.int8)
    active_test = test["target_mlb_active"].to_numpy().astype(np.int8)
    bf_train = train["target_mlb_pa"].to_numpy()
    bf_test = test["target_mlb_pa"].to_numpy()
    active_rows = active_train == 1

    models = make_engine_models(engine, random_state)
    if models.uses_player_random_effect:
        raise ValueError("GPBoost workload comparison requires grouped target models")
    if models.requires_imputation:
        from sklearn.impute import SimpleImputer

        imputer = SimpleImputer(strategy="median")
        x_train = imputer.fit_transform(x_train)
        x_test = imputer.transform(x_test)

    models.classifier.fit(x_train, active_train)
    probability = np.clip(models.classifier.predict_proba(x_test)[:, 1], 0.0, 1.0)
    workload_model = _fresh_regressor(engine, random_state + 1)
    workload_model.fit(x_train[active_rows], bf_train[active_rows])
    conditional_bf = np.clip(
        np.asarray(workload_model.predict(x_test), dtype=np.float64), 0.0, 1_500.0
    )
    expected_bf = probability * conditional_bf

    predictions = pl.DataFrame(
        {
            "engine": [engine] * test.height,
            "origin_year": test["origin_year"],
            "target_season": test["target_season"],
            "player_id": test["player_id"],
            "actual_active": active_test,
            "actual_bf": bf_test,
            "active_probability": probability,
            "predicted_conditional_bf": conditional_bf,
            "predicted_expected_bf": expected_bf,
        }
    )
    active_test_rows = active_test == 1
    metrics = {
        "arrival": classification_metrics(active_test, probability),
        "zero_inclusive_bf": regression_metrics(bf_test, expected_bf),
        "conditional_bf_active_pitchers": regression_metrics(
            bf_test[active_test_rows], conditional_bf[active_test_rows]
        ),
    }
    return predictions, metrics

