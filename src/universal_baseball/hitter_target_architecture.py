"""Chronology-safe comparisons of hitter value target architectures."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import polars as pl


TARGET_COLUMNS = {
    "target_mlb_pa",
    "target_mlb_active",
    "target_conditional_component_war_per_600",
    "target_component_war",
    "target_season",
}
IDENTIFIER_COLUMNS = {"player_id", "origin_year"}
LEVEL_VALUES = {
    None: -1.0,
    "RK": 0.0,
    "ROOKIE": 0.0,
    "A-": 1.0,
    "A": 2.0,
    "A+": 3.0,
    "AA": 4.0,
    "AAA": 5.0,
    "MLB": 6.0,
}


@dataclass(frozen=True)
class Fold:
    """One expanding-window development fold."""

    test_origin: int
    train_origins: tuple[int, ...]


def expanding_year_folds(
    origins: Iterable[int], *, minimum_train_years: int = 2
) -> list[Fold]:
    """Build expanding chronological folds without crossing the 2026 seal."""
    years = sorted(set(int(year) for year in origins))
    if any(year >= 2025 for year in years):
        raise ValueError("development origins must target seasons before 2026")
    return [
        Fold(test_origin=year, train_origins=tuple(years[:index]))
        for index, year in enumerate(years)
        if index >= minimum_train_years
    ]


def feature_columns(panel: pl.DataFrame) -> list[str]:
    """Return predictors only; identifiers and future outcomes are forbidden."""
    excluded = TARGET_COLUMNS | IDENTIFIER_COLUMNS
    columns = [column for column in panel.columns if column not in excluded]
    leaked = [column for column in columns if column.startswith("target_")]
    if leaked:
        raise ValueError(f"future outcome columns selected as features: {leaked}")
    return columns


def matrix_from_panel(panel: pl.DataFrame, columns: list[str]) -> np.ndarray:
    """Create a numeric matrix, ordinal-encoding only the known level fields."""
    arrays: list[np.ndarray] = []
    for column in columns:
        series = panel[column]
        if series.dtype == pl.String:
            unknown = set(series.drop_nulls().unique().to_list()) - set(LEVEL_VALUES)
            if unknown:
                raise ValueError(f"unknown categorical values in {column}: {unknown}")
            values = np.array(
                [LEVEL_VALUES.get(value, -1.0) for value in series.to_list()],
                dtype=np.float32,
            )
        else:
            values = series.cast(pl.Float32).to_numpy()
        arrays.append(values)
    matrix = np.column_stack(arrays).astype(np.float32, copy=False)
    matrix[~np.isfinite(matrix)] = np.nan
    return matrix


def compose_architecture_predictions(
    *,
    active_probability: np.ndarray,
    conditional_total_war: np.ndarray,
    conditional_pa: np.ndarray,
    conditional_rate_per_600: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compose the two decomposed expected-value estimates."""
    probability = np.clip(active_probability, 0.0, 1.0)
    pa = np.clip(conditional_pa, 0.0, 750.0)
    rate = np.clip(conditional_rate_per_600, -5.0, 10.0)
    return {
        "two_part": probability * conditional_total_war,
        "three_part": probability * pa * rate / 600.0,
    }


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    """Metrics for total next-season value."""
    error = predicted - actual
    return {
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "mae": float(np.mean(np.abs(error))),
        "bias": float(np.mean(error)),
        "actual_mean": float(np.mean(actual)),
        "predicted_mean": float(np.mean(predicted)),
    }


def classification_metrics(actual: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    """Proper scoring rules for next-season MLB arrival/return."""
    clipped = np.clip(probability, 1e-6, 1.0 - 1e-6)
    return {
        "brier": float(np.mean(np.square(clipped - actual))),
        "log_loss": float(
            -np.mean(actual * np.log(clipped) + (1.0 - actual) * np.log(1.0 - clipped))
        ),
        "actual_rate": float(np.mean(actual)),
        "predicted_rate": float(np.mean(clipped)),
    }


def paired_cluster_rmse_delta(
    actual: np.ndarray,
    challenger: np.ndarray,
    reference: np.ndarray,
    clusters: np.ndarray,
    *,
    bootstrap_samples: int = 2_000,
    random_state: int = 417,
) -> dict[str, float]:
    """Player-clustered interval for challenger RMSE minus reference RMSE."""
    labels, inverse = np.unique(clusters, return_inverse=True)
    challenger_sse = np.bincount(inverse, weights=np.square(challenger - actual))
    reference_sse = np.bincount(inverse, weights=np.square(reference - actual))
    counts = np.bincount(inverse)
    rng = np.random.default_rng(random_state)
    deltas = np.empty(bootstrap_samples, dtype=np.float64)
    for index in range(bootstrap_samples):
        sampled = rng.integers(0, labels.size, size=labels.size)
        denominator = counts[sampled].sum()
        challenger_rmse = np.sqrt(challenger_sse[sampled].sum() / denominator)
        reference_rmse = np.sqrt(reference_sse[sampled].sum() / denominator)
        deltas[index] = challenger_rmse - reference_rmse
    point = regression_metrics(actual, challenger)["rmse"] - regression_metrics(
        actual, reference
    )["rmse"]
    return {
        "rmse_delta": point,
        "ci95_low": float(np.quantile(deltas, 0.025)),
        "ci95_high": float(np.quantile(deltas, 0.975)),
        "player_clusters": int(labels.size),
        "bootstrap_samples": bootstrap_samples,
    }


def _lgbm_classifier(random_state: int) -> Any:
    from lightgbm import LGBMClassifier

    return LGBMClassifier(
        objective="binary",
        n_estimators=350,
        learning_rate=0.025,
        num_leaves=15,
        max_depth=5,
        min_child_samples=60,
        subsample=0.85,
        colsample_bytree=0.70,
        reg_alpha=0.25,
        reg_lambda=4.0,
        random_state=random_state,
        n_jobs=-1,
        verbosity=-1,
    )


def _lgbm_regressor(random_state: int) -> Any:
    from lightgbm import LGBMRegressor

    return LGBMRegressor(
        objective="regression_l2",
        n_estimators=350,
        learning_rate=0.025,
        num_leaves=15,
        max_depth=5,
        min_child_samples=60,
        subsample=0.85,
        colsample_bytree=0.70,
        reg_alpha=0.25,
        reg_lambda=4.0,
        random_state=random_state,
        n_jobs=-1,
        verbosity=-1,
    )


def run_lightgbm_architecture_fold(
    panel: pl.DataFrame,
    fold: Fold,
    *,
    random_state: int = 417,
) -> tuple[pl.DataFrame, dict[str, dict[str, float]], dict[str, float]]:
    """Fit direct, two-part, and three-part models on one time fold."""
    train = panel.filter(pl.col("origin_year").is_in(fold.train_origins))
    test = panel.filter(pl.col("origin_year") == fold.test_origin)
    if train.is_empty() or test.is_empty():
        raise ValueError(f"empty train or test set for origin {fold.test_origin}")

    columns = feature_columns(panel)
    x_train = matrix_from_panel(train, columns)
    x_test = matrix_from_panel(test, columns)
    active_train = train["target_mlb_active"].to_numpy().astype(np.int8)
    active_test = test["target_mlb_active"].to_numpy().astype(np.int8)
    war_train = train["target_component_war"].to_numpy()
    war_test = test["target_component_war"].to_numpy()
    active_rows = active_train == 1

    classifier = _lgbm_classifier(random_state)
    classifier.fit(x_train, active_train)
    active_probability = classifier.predict_proba(x_test)[:, 1]

    direct_model = _lgbm_regressor(random_state + 1)
    direct_model.fit(x_train, war_train)
    direct_prediction = direct_model.predict(x_test)

    total_model = _lgbm_regressor(random_state + 2)
    total_model.fit(x_train[active_rows], war_train[active_rows])
    conditional_total = total_model.predict(x_test)

    pa_train = train["target_mlb_pa"].to_numpy()
    pa_model = _lgbm_regressor(random_state + 3)
    pa_model.fit(x_train[active_rows], pa_train[active_rows])
    conditional_pa = pa_model.predict(x_test)

    rate_train = train["target_conditional_component_war_per_600"].to_numpy()
    rate_model = _lgbm_regressor(random_state + 4)
    rate_model.fit(
        x_train[active_rows],
        rate_train[active_rows],
        sample_weight=np.sqrt(np.maximum(pa_train[active_rows], 1.0)),
    )
    conditional_rate = rate_model.predict(x_test)
    composed = compose_architecture_predictions(
        active_probability=active_probability,
        conditional_total_war=conditional_total,
        conditional_pa=conditional_pa,
        conditional_rate_per_600=conditional_rate,
    )

    train_mean = float(np.mean(war_train))
    predictions = pl.DataFrame(
        {
            "origin_year": test["origin_year"],
            "target_season": test["target_season"],
            "player_id": test["player_id"],
            "actual_active": active_test,
            "actual_pa": test["target_mlb_pa"],
            "actual_component_war": war_test,
            "current_highest_level": test["lag0__highest_level"],
            "current_pa": test["lag0__plate_appearances"],
            "current_mlb_pa": test["lag0__pa_level__MLB"],
            "current_contact_events": test["lag0__contact_events"],
            "current_age": test["lag0__age"],
            "active_probability": active_probability,
            "predicted_conditional_total_war": conditional_total,
            "predicted_conditional_pa": conditional_pa,
            "predicted_conditional_rate_per_600": conditional_rate,
            "prediction_zero": np.zeros(test.height),
            "prediction_train_mean": np.full(test.height, train_mean),
            "prediction_direct": direct_prediction,
            "prediction_two_part": composed["two_part"],
            "prediction_three_part": composed["three_part"],
        }
    )
    metrics = {
        "zero": regression_metrics(war_test, np.zeros(test.height)),
        "train_mean": regression_metrics(war_test, np.full(test.height, train_mean)),
        "direct": regression_metrics(war_test, direct_prediction),
        "two_part": regression_metrics(war_test, composed["two_part"]),
        "three_part": regression_metrics(war_test, composed["three_part"]),
        "active_probability": classification_metrics(active_test, active_probability),
    }
    importance = {
        name: float(value)
        for name, value in zip(
            columns,
            direct_model.booster_.feature_importance(importance_type="gain"),
            strict=True,
        )
    }
    return predictions, metrics, importance
