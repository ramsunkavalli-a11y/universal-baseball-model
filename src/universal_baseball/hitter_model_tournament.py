"""Model-family adapters for the clean-slate hitter value tournament."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    Fold,
    classification_metrics,
    feature_columns,
    matrix_from_panel,
    regression_metrics,
)


SUPPORTED_ENGINES = (
    "ridge",
    "extra_trees",
    "histgb",
    "xgboost",
    "lightgbm",
    "catboost",
    "ebm",
    "ngboost",
    "gpboost",
)


@dataclass(frozen=True)
class EngineModels:
    classifier: Any
    regressor: Any
    requires_imputation: bool = False
    uses_player_random_effect: bool = False


def _engine_models(
    engine: str, random_state: int, variant: str = "balanced"
) -> EngineModels:
    if variant not in {"smooth", "balanced", "flexible"}:
        raise ValueError(f"unsupported tuning variant: {variant}")
    if engine == "ridge":
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression, Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        return EngineModels(
            classifier=make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                LogisticRegression(C=0.10, max_iter=1_000, random_state=random_state),
            ),
            regressor=make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                Ridge(alpha=20.0),
            ),
        )
    if engine == "extra_trees":
        from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor

        common = {
            "n_estimators": 500,
            "max_features": 0.7,
            "min_samples_leaf": 10,
            "n_jobs": -1,
            "random_state": random_state,
        }
        return EngineModels(
            classifier=ExtraTreesClassifier(**common),
            regressor=ExtraTreesRegressor(**common),
            requires_imputation=True,
        )
    if engine == "histgb":
        from sklearn.ensemble import (
            HistGradientBoostingClassifier,
            HistGradientBoostingRegressor,
        )

        common = {
            "learning_rate": 0.04,
            "max_iter": 350,
            "max_leaf_nodes": 15,
            "max_depth": 5,
            "min_samples_leaf": 60,
            "l2_regularization": 4.0,
            "random_state": random_state,
        }
        return EngineModels(
            classifier=HistGradientBoostingClassifier(**common),
            regressor=HistGradientBoostingRegressor(**common),
        )
    if engine == "xgboost":
        from xgboost import XGBClassifier, XGBRegressor

        complexity = {
            "smooth": {"max_depth": 3, "min_child_weight": 20.0},
            "balanced": {"max_depth": 5, "min_child_weight": 10.0},
            "flexible": {"max_depth": 7, "min_child_weight": 5.0},
        }[variant]
        common = {
            "n_estimators": 400,
            "learning_rate": 0.03,
            "subsample": 0.85,
            "colsample_bytree": 0.70,
            "reg_alpha": 0.25,
            "reg_lambda": 4.0,
            "n_jobs": -1,
            "random_state": random_state,
            **complexity,
        }
        return EngineModels(
            classifier=XGBClassifier(objective="binary:logistic", **common),
            regressor=XGBRegressor(objective="reg:squarederror", **common),
        )
    if engine == "lightgbm":
        from lightgbm import LGBMClassifier, LGBMRegressor

        complexity = {
            "smooth": {"num_leaves": 7, "max_depth": 3, "min_child_samples": 100},
            "balanced": {"num_leaves": 15, "max_depth": 5, "min_child_samples": 60},
            "flexible": {"num_leaves": 31, "max_depth": 7, "min_child_samples": 30},
        }[variant]
        common = {
            "n_estimators": 350,
            "learning_rate": 0.025,
            "subsample": 0.85,
            "colsample_bytree": 0.70,
            "reg_alpha": 0.25,
            "reg_lambda": 4.0,
            "n_jobs": -1,
            "random_state": random_state,
            "verbosity": -1,
            **complexity,
        }
        return EngineModels(
            classifier=LGBMClassifier(objective="binary", **common),
            regressor=LGBMRegressor(objective="regression_l2", **common),
        )
    if engine == "catboost":
        from catboost import CatBoostClassifier, CatBoostRegressor

        complexity = {
            "smooth": {"depth": 4, "l2_leaf_reg": 8.0},
            "balanced": {"depth": 6, "l2_leaf_reg": 5.0},
            "flexible": {"depth": 8, "l2_leaf_reg": 3.0},
        }[variant]
        common = {
            "iterations": 400,
            "learning_rate": 0.03,
            "random_seed": random_state,
            "verbose": False,
            "allow_writing_files": False,
            "thread_count": -1,
            **complexity,
        }
        return EngineModels(
            classifier=CatBoostClassifier(loss_function="Logloss", **common),
            regressor=CatBoostRegressor(loss_function="RMSE", **common),
        )
    if engine == "ebm":
        from interpret.glassbox import (
            ExplainableBoostingClassifier,
            ExplainableBoostingRegressor,
        )

        complexity = {
            "smooth": {"interactions": 0, "min_samples_leaf": 40, "max_leaves": 2},
            "balanced": {
                "interactions": 10,
                "min_samples_leaf": 20,
                "max_leaves": 2,
            },
            "flexible": {
                "interactions": 20,
                "min_samples_leaf": 10,
                "max_leaves": 3,
            },
        }[variant]
        common = {
            "max_bins": 128,
            "max_interaction_bins": 32,
            "outer_bags": 4,
            "max_rounds": 2_000,
            "early_stopping_rounds": 75,
            "n_jobs": -1,
            "random_state": random_state,
            **complexity,
        }
        return EngineModels(
            classifier=ExplainableBoostingClassifier(learning_rate=0.025, **common),
            regressor=ExplainableBoostingRegressor(learning_rate=0.035, **common),
        )
    if engine == "ngboost":
        from ngboost import NGBClassifier, NGBRegressor
        from sklearn.tree import DecisionTreeRegressor

        common = {
            "Base": DecisionTreeRegressor(max_depth=3, min_samples_leaf=20),
            "n_estimators": 400,
            "learning_rate": 0.02,
            "minibatch_frac": 0.8,
            "col_sample": 0.7,
            "verbose": False,
            "random_state": random_state,
        }
        return EngineModels(
            classifier=NGBClassifier(**common),
            regressor=NGBRegressor(**common),
            requires_imputation=True,
        )
    if engine == "gpboost":
        from gpboost import GPBoostClassifier, GPBoostRegressor

        common = {
            "n_estimators": 300,
            "learning_rate": 0.03,
            "num_leaves": 15,
            "max_depth": 5,
            "min_child_samples": 60,
            "colsample_bytree": 0.7,
            "reg_alpha": 0.25,
            "reg_lambda": 4.0,
            "n_jobs": -1,
            "random_state": random_state,
            "verbose": -1,
        }
        return EngineModels(
            classifier=GPBoostClassifier(objective="binary", **common),
            regressor=GPBoostRegressor(objective="regression_l2", **common),
            uses_player_random_effect=True,
        )
    raise ValueError(f"unsupported engine: {engine}")


def make_engine_models(
    engine: str, random_state: int = 417, variant: str = "balanced"
) -> EngineModels:
    """Return the fixed model pair for reuse by adjacent target modules."""
    return _engine_models(engine, random_state, variant)


def _impute(
    x_train: np.ndarray, x_test: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.impute import SimpleImputer

    imputer = SimpleImputer(strategy="median")
    return imputer.fit_transform(x_train), imputer.transform(x_test)


def _fit_standard_two_part(
    models: EngineModels,
    x_train: np.ndarray,
    x_test: np.ndarray,
    active_train: np.ndarray,
    war_train: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if models.requires_imputation:
        x_train, x_test = _impute(x_train, x_test)
    active_rows = active_train == 1
    models.classifier.fit(x_train, active_train)
    probability = models.classifier.predict_proba(x_test)[:, 1]
    models.regressor.fit(x_train[active_rows], war_train[active_rows])
    conditional_war = models.regressor.predict(x_test)
    return probability, conditional_war


def _fit_gpboost_two_part(
    models: EngineModels,
    x_train: np.ndarray,
    x_test: np.ndarray,
    active_train: np.ndarray,
    war_train: np.ndarray,
    train_player_ids: np.ndarray,
    test_player_ids: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    from gpboost import GPModel

    train_groups = train_player_ids.reshape(-1, 1)
    test_groups = test_player_ids.reshape(-1, 1)
    active_rows = active_train == 1
    classifier_gp = GPModel(
        group_data=train_groups,
        likelihood="bernoulli_logit",
    )
    models.classifier.fit(
        x_train,
        active_train,
        gp_model=classifier_gp,
        verbose=False,
    )
    probability_result = models.classifier.predict_proba(
        x_test,
        group_data_pred=test_groups,
    )
    probability = np.asarray(probability_result["response_mean"])
    regressor_gp = GPModel(group_data=train_groups[active_rows], likelihood="gaussian")
    models.regressor.fit(
        x_train[active_rows],
        war_train[active_rows],
        gp_model=regressor_gp,
        verbose=False,
    )
    conditional_result = models.regressor.predict(
        x_test,
        group_data_pred=test_groups,
    )
    conditional_war = np.asarray(conditional_result["response_mean"])
    return probability, conditional_war


def run_engine_fold(
    panel: pl.DataFrame,
    fold: Fold,
    engine: str,
    *,
    random_state: int = 417,
    variant: str = "balanced",
) -> tuple[pl.DataFrame, dict[str, dict[str, float]]]:
    """Run one two-part engine on one expanding historical fold."""
    train = panel.filter(pl.col("origin_year").is_in(fold.train_origins))
    test = panel.filter(pl.col("origin_year") == fold.test_origin)
    columns = feature_columns(panel)
    x_train = matrix_from_panel(train, columns)
    x_test = matrix_from_panel(test, columns)
    active_train = train["target_mlb_active"].to_numpy().astype(np.int8)
    active_test = test["target_mlb_active"].to_numpy().astype(np.int8)
    war_train = train["target_component_war"].to_numpy()
    war_test = test["target_component_war"].to_numpy()
    models = _engine_models(engine, random_state, variant)
    if models.uses_player_random_effect:
        probability, conditional_war = _fit_gpboost_two_part(
            models,
            x_train,
            x_test,
            active_train,
            war_train,
            train["player_id"].to_numpy(),
            test["player_id"].to_numpy(),
        )
    else:
        probability, conditional_war = _fit_standard_two_part(
            models, x_train, x_test, active_train, war_train
        )
    probability = np.clip(np.asarray(probability), 0.0, 1.0)
    conditional_war = np.asarray(conditional_war)
    prediction = probability * conditional_war
    active_test_rows = active_test == 1
    result = pl.DataFrame(
        {
            "engine": [engine] * test.height,
            "origin_year": test["origin_year"],
            "target_season": test["target_season"],
            "player_id": test["player_id"],
            "actual_active": active_test,
            "actual_component_war": war_test,
            "active_probability": probability,
            "predicted_conditional_war": conditional_war,
            "predicted_component_war": prediction,
        }
    )
    metrics = {
        "total_value": regression_metrics(war_test, prediction),
        "active_probability": classification_metrics(active_test, probability),
        "conditional_value_active_players": regression_metrics(
            war_test[active_test_rows], conditional_war[active_test_rows]
        ),
    }
    return result, metrics
