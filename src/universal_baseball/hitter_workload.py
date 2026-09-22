"""Chronology-safe next-season MLB plate-appearance models for hitters."""

from __future__ import annotations

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


def run_workload_fold(
    panel: pl.DataFrame,
    fold: Fold,
    engine: str,
    *,
    include_direct: bool = False,
    random_state: int = 417,
) -> tuple[pl.DataFrame, dict[str, object]]:
    """Fit one hurdle workload model and an optional direct workload model."""
    train = panel.filter(pl.col("origin_year").is_in(fold.train_origins))
    test = panel.filter(pl.col("origin_year") == fold.test_origin)
    columns = feature_columns(panel)
    x_train = matrix_from_panel(train, columns)
    x_test = matrix_from_panel(test, columns)
    active_train = train["target_mlb_active"].to_numpy().astype(np.int8)
    active_test = test["target_mlb_active"].to_numpy().astype(np.int8)
    pa_train = train["target_mlb_pa"].to_numpy()
    pa_test = test["target_mlb_pa"].to_numpy()
    active_rows = active_train == 1

    models = make_engine_models(engine, random_state)
    models.classifier.fit(x_train, active_train)
    probability = np.clip(models.classifier.predict_proba(x_test)[:, 1], 0.0, 1.0)
    models.regressor.fit(x_train[active_rows], pa_train[active_rows])
    conditional_pa = np.clip(models.regressor.predict(x_test), 0.0, 750.0)
    hurdle_pa = probability * conditional_pa

    result = pl.DataFrame(
        {
            "engine": [engine] * test.height,
            "origin_year": test["origin_year"],
            "target_season": test["target_season"],
            "player_id": test["player_id"],
            "actual_active": active_test,
            "actual_pa": pa_test,
            "active_probability": probability,
            "predicted_conditional_pa": conditional_pa,
            "predicted_hurdle_pa": hurdle_pa,
        }
    )
    metrics: dict[str, object] = {
        "hurdle_pa": regression_metrics(pa_test, hurdle_pa),
        "active_probability": classification_metrics(active_test, probability),
        "conditional_pa_active_players": regression_metrics(
            pa_test[active_test == 1], conditional_pa[active_test == 1]
        ),
    }
    if include_direct:
        direct = make_engine_models(engine, random_state + 10).regressor
        direct.fit(x_train, pa_train)
        direct_pa = np.clip(direct.predict(x_test), 0.0, 750.0)
        result = result.with_columns(pl.Series("predicted_direct_pa", direct_pa))
        metrics["direct_pa"] = regression_metrics(pa_test, direct_pa)
    return result, metrics
