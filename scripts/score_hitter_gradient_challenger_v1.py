#!/usr/bin/env python3
"""Score fixed regularized and gradient-tree challengers on frozen hitter rows."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES
from universal_baseball.storage import write_canonical_parquet


EVALUATION_ORIGINS = (2022, 2023, 2024)
RIDGE_ALPHA = 300.0
TREE_PARAMETERS = {
    "learning_rate": 0.04,
    "max_iter": 150,
    "max_leaf_nodes": 15,
    "max_depth": 3,
    "min_samples_leaf": 50,
    "l2_regularization": 10.0,
    "random_state": 1729,
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(
            "reports/generated/hitter-gradient-dataset-v1/tables/modeling-rows.parquet"
        ),
    )
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-gradient-challenger-v1"),
    )
    return parser.parse_args()


def _feature_columns(frame: pl.DataFrame) -> list[str]:
    exact = {
        "contacts__feature",
        "log_contacts",
        "age",
        "relative_age",
        "age_centered_sq",
        "relative_age_sq",
        "age_missing",
        "materialized_contacts",
        "opponent_context_known_rate",
        "venue_known_rate",
        "contact_share_vs_lhp",
        "contact_share_vs_rhp",
        "park_factor_known_rate",
        "mean_park_factor_reliability",
        "mean_park_training_seasons",
    }
    prefixes = (
        "overall__",
        "share__",
        "contact_result__",
        "contact_count__",
        "mean__",
        "park_effect__",
    )
    columns = [
        name
        for name, dtype in frame.schema.items()
        if (name in exact or name.startswith(prefixes))
        and dtype.is_numeric()
        and not name.startswith("target__")
    ]
    if len(columns) < 120:
        raise ValueError(f"unexpectedly small feature set: {len(columns)}")
    return columns


def _design(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    columns: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    train = training.select(columns).to_numpy().astype(float)
    score = evaluation.select(columns).to_numpy().astype(float)
    medians = np.nanmedian(train, axis=0)
    medians[~np.isfinite(medians)] = 0.0
    train = np.where(np.isfinite(train), train, medians)
    score = np.where(np.isfinite(score), score, medians)
    means = train.mean(axis=0)
    scales = train.std(axis=0)
    scales[scales < 1e-12] = 1.0
    train = (train - means) / scales
    score = (score - means) / scales

    levels = sorted(str(value) for value in training["source_level"].unique())
    train_level = np.column_stack(
        [training["source_level"].to_numpy() == value for value in levels]
    ).astype(float)
    score_level = np.column_stack(
        [evaluation["source_level"].to_numpy() == value for value in levels]
    ).astype(float)
    return np.column_stack([train, train_level]), np.column_stack([score, score_level])


def _probabilities(frame: pl.DataFrame, prefix: str) -> np.ndarray:
    return frame.select(*(f"{prefix}{value}" for value in CONTACT_OUTCOMES)).to_numpy()


def _normalize(values: np.ndarray) -> np.ndarray:
    result = np.clip(values, 1e-6, None)
    return result / result.sum(axis=1, keepdims=True)


def _metrics(actual: np.ndarray, prediction: np.ndarray, weight: np.ndarray) -> dict[str, float]:
    prediction = _normalize(prediction)
    return {
        "rate_rmse": float(np.sqrt(np.mean((prediction - actual) ** 2))),
        "multinomial_log_loss": float(
            -np.sum(weight[:, None] * actual * np.log(prediction)) / weight.sum()
        ),
        "multinomial_brier": float(
            np.sum(weight * np.sum((prediction - actual) ** 2, axis=1)) / weight.sum()
        ),
    }


def _delta(candidate: dict[str, float], baseline: dict[str, float]) -> dict[str, float]:
    return {name: candidate[name] - baseline[name] for name in baseline}


def _fit_fold(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    columns: list[str],
) -> dict[str, np.ndarray]:
    x_train, x_score = _design(training, evaluation, columns)
    actual_train = _probabilities(training, "target__overall__")
    base_train = _probabilities(training, "contact_only__overall__")
    base_score = _probabilities(evaluation, "contact_only__overall__")
    residual = actual_train - base_train
    weights = training["target_contacts"].to_numpy().astype(float)

    ridge = Ridge(alpha=RIDGE_ALPHA).fit(x_train, residual, sample_weight=weights)
    ridge_prediction = _normalize(base_score + ridge.predict(x_score))
    tree_columns = []
    for outcome_index in range(len(CONTACT_OUTCOMES)):
        model = HistGradientBoostingRegressor(**TREE_PARAMETERS).fit(
            x_train,
            residual[:, outcome_index],
            sample_weight=weights,
        )
        tree_columns.append(model.predict(x_score))
    tree_prediction = _normalize(base_score + np.column_stack(tree_columns))
    return {"contact_only": base_score, "ridge": ridge_prediction, "gradient_tree": tree_prediction}


def _stratum(frame: pl.DataFrame) -> np.ndarray:
    rank = {"rk": 0, "a-": 1, "a": 2, "a+": 3, "aa": 4, "aaa": 5, "MLB": 6}
    source = np.asarray([rank.get(str(value), -1) for value in frame["source_level"]])
    target = np.asarray([rank.get(str(value), -1) for value in frame["target_source_level"]])
    return np.where(target > source, "advanced", np.where(target < source, "demoted", "same_level"))


def main() -> int:
    args = _args()
    if args.as_of_date.year < 2025:
        raise ValueError("as-of date predates the final development target")
    frame = pl.read_parquet(args.dataset)
    if frame.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 rows are not allowed")
    columns = _feature_columns(frame)
    prediction_rows: list[pl.DataFrame] = []
    fold_rows = []
    for origin in EVALUATION_ORIGINS:
        training = frame.filter(pl.col("origin_year") < origin)
        evaluation = frame.filter(pl.col("origin_year") == origin)
        if training.is_empty() or evaluation.is_empty():
            raise ValueError(f"fold {origin} lacks training or evaluation rows")
        predictions = _fit_fold(training, evaluation, columns)
        actual = _probabilities(evaluation, "target__overall__")
        weight = evaluation["target_contacts"].to_numpy().astype(float)
        baseline_metrics = _metrics(actual, predictions["contact_only"], weight)
        for model_name, prediction in predictions.items():
            metrics = _metrics(actual, prediction, weight)
            fold_rows.append(
                {
                    "origin_year": origin,
                    "model": model_name,
                    "players": evaluation.height,
                    **metrics,
                    **{f"{key}_vs_contact_only": value for key, value in _delta(metrics, baseline_metrics).items()},
                }
            )
        output = evaluation.select(
            "origin_year",
            "target_season",
            "player_id",
            "source_level",
            "target_source_level",
            "contacts",
            "target_contacts",
        ).with_columns(pl.Series("transition", _stratum(evaluation)))
        for model_name, prediction in predictions.items():
            output = output.with_columns(
                *(pl.Series(f"{model_name}__{outcome}", prediction[:, index]) for index, outcome in enumerate(CONTACT_OUTCOMES))
            )
        output = output.with_columns(
            *(evaluation[f"target__overall__{outcome}"].alias(f"actual__{outcome}") for outcome in CONTACT_OUTCOMES)
        )
        prediction_rows.append(output)

    predictions = pl.concat(prediction_rows, how="vertical_relaxed")
    actual = predictions.select(*(f"actual__{value}" for value in CONTACT_OUTCOMES)).to_numpy()
    weight = predictions["target_contacts"].to_numpy().astype(float)
    pooled: dict[str, dict[str, float]] = {}
    for model_name in ("contact_only", "ridge", "gradient_tree"):
        candidate = predictions.select(
            *(f"{model_name}__{value}" for value in CONTACT_OUTCOMES)
        ).to_numpy()
        pooled[model_name] = _metrics(actual, candidate, weight)
    deltas = {
        name: _delta(metrics, pooled["contact_only"])
        for name, metrics in pooled.items()
        if name != "contact_only"
    }
    slices = []
    for transition in ("advanced", "same_level", "demoted"):
        selected = predictions.filter(pl.col("transition") == transition)
        if selected.is_empty():
            continue
        y = selected.select(*(f"actual__{value}" for value in CONTACT_OUTCOMES)).to_numpy()
        w = selected["target_contacts"].to_numpy().astype(float)
        base = _metrics(
            y,
            selected.select(*(f"contact_only__{value}" for value in CONTACT_OUTCOMES)).to_numpy(),
            w,
        )
        for model_name in ("ridge", "gradient_tree"):
            metric = _metrics(
                y,
                selected.select(*(f"{model_name}__{value}" for value in CONTACT_OUTCOMES)).to_numpy(),
                w,
            )
            slices.append(
                {"transition": transition, "model": model_name, "players": selected.height, **metric, **{f"{key}_vs_contact_only": value for key, value in _delta(metric, base).items()}}
            )

    args.output_root.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "predictions": write_canonical_parquet(
            predictions,
            args.output_root / "predictions.parquet",
            table_name="hitter_gradient_challenger_v1_predictions",
        ).as_record(),
        "fold_metrics": write_canonical_parquet(
            pl.DataFrame(fold_rows),
            args.output_root / "fold-metrics.parquet",
            table_name="hitter_gradient_challenger_v1_fold_metrics",
        ).as_record(),
        "transition_metrics": write_canonical_parquet(
            pl.DataFrame(slices),
            args.output_root / "transition-metrics.parquet",
            table_name="hitter_gradient_challenger_v1_transition_metrics",
        ).as_record(),
    }
    winner = min(pooled, key=lambda name: pooled[name]["rate_rmse"])
    report = {
        "schema_version": "1.0",
        "status": "hitter_gradient_challenger_v1_scored",
        "as_of_date": args.as_of_date.isoformat(),
        "protected_2026_outcomes_used": False,
        "evaluation_origins": list(EVALUATION_ORIGINS),
        "evaluated_players": predictions.height,
        "feature_count": len(columns),
        "models": {
            "contact_only": "frozen incumbent",
            "ridge": {"residual_on_incumbent": True, "alpha": RIDGE_ALPHA},
            "gradient_tree": {"residual_on_incumbent": True, **TREE_PARAMETERS},
        },
        "pooled_metrics": pooled,
        "challenger_vs_contact_only": deltas,
        "fold_metrics": fold_rows,
        "transition_metrics": slices,
        "best_rate_rmse_model": winner,
        "development_signal_gate": {
            "rule": "challenger must improve pooled RMSE, log loss, and Brier score",
            "passed": bool(
                winner != "contact_only"
                and deltas[winner]["rate_rmse"] < 0
                and deltas[winner]["multinomial_log_loss"] < 0
                and deltas[winner]["multinomial_brier"] < 0
            ),
        },
        "production_promotion_gate": {
            "passed": False,
            "reason": (
                "paired player bootstrap and predeclared feature-family ablations "
                "remain; advancing-player RMSE is slightly worse"
            ),
        },
        "artifacts": artifacts,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
