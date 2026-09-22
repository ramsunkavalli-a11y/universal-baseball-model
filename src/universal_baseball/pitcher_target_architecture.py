"""Direct, two-part, and three-part pitcher value target architectures."""

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


def run_pitcher_architecture_fold(
    panel: pl.DataFrame,
    fold: Fold,
    engine: str,
    *,
    random_state: int = 417,
) -> tuple[pl.DataFrame, dict[str, dict[str, float]]]:
    """Compare direct, two-part, and workload/rate pitcher value estimates."""

    generic = to_generic_two_part_panel(panel)
    train = generic.filter(pl.col("origin_year").is_in(fold.train_origins))
    test = generic.filter(pl.col("origin_year") == fold.test_origin)
    columns = feature_columns(generic)
    x_train = matrix_from_panel(train, columns)
    x_test = matrix_from_panel(test, columns)
    active_train = train["target_mlb_active"].to_numpy().astype(np.int8)
    active_test = test["target_mlb_active"].to_numpy().astype(np.int8)
    war_train = train["target_component_war"].to_numpy()
    war_test = test["target_component_war"].to_numpy()
    bf_train = train["target_mlb_pa"].to_numpy()
    rate_train = train["target_conditional_component_war_per_600"].to_numpy()
    active_rows = active_train == 1

    models = make_engine_models(engine, random_state)
    if models.uses_player_random_effect:
        raise ValueError("GPBoost architecture comparison requires grouped target models")
    if models.requires_imputation:
        from sklearn.impute import SimpleImputer

        imputer = SimpleImputer(strategy="median")
        x_train = imputer.fit_transform(x_train)
        x_test = imputer.transform(x_test)

    models.classifier.fit(x_train, active_train)
    probability = np.clip(models.classifier.predict_proba(x_test)[:, 1], 0.0, 1.0)

    direct_model = _fresh_regressor(engine, random_state + 1)
    conditional_model = models.regressor
    bf_model = _fresh_regressor(engine, random_state + 3)
    rate_model = _fresh_regressor(engine, random_state + 4)
    direct_model.fit(x_train, war_train)
    conditional_model.fit(x_train[active_rows], war_train[active_rows])
    bf_model.fit(x_train[active_rows], bf_train[active_rows])
    rate_model.fit(x_train[active_rows], rate_train[active_rows])

    direct = np.asarray(direct_model.predict(x_test))
    conditional = np.asarray(conditional_model.predict(x_test))
    bf = np.clip(np.asarray(bf_model.predict(x_test)), 0.0, 1_500.0)
    rate = np.clip(np.asarray(rate_model.predict(x_test)), -10.0, 15.0)
    two_part = probability * conditional
    three_part = probability * bf * rate / 800.0
    predictions = pl.DataFrame(
        {
            "engine": [engine] * test.height,
            "origin_year": test["origin_year"],
            "target_season": test["target_season"],
            "player_id": test["player_id"],
            "actual_active": active_test,
            "actual_bf": test["target_mlb_pa"],
            "actual_component_war": war_test,
            "active_probability": probability,
            "predicted_conditional_war": conditional,
            "predicted_conditional_bf": bf,
            "predicted_conditional_rate_per_800": rate,
            "prediction_direct": direct,
            "prediction_two_part": two_part,
            "prediction_three_part": three_part,
        }
    )
    metrics = {
        "direct": regression_metrics(war_test, direct),
        "two_part": regression_metrics(war_test, two_part),
        "three_part": regression_metrics(war_test, three_part),
        "active_probability": classification_metrics(active_test, probability),
    }
    return predictions, metrics
