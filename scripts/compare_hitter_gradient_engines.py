#!/usr/bin/env python3
"""Compare sklearn histogram boosting, XGBoost, and LightGBM fairly."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
from lightgbm import LGBMRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from xgboost import XGBRegressor

from audit_hitter_gradient_ablation import _design, _families
from score_hitter_gradient_challenger_v1 import _metrics, _normalize, _probabilities
from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES
from universal_baseball.projection_bootstrap import paired_player_cluster_bootstrap
from universal_baseball.storage import sha256_file, write_canonical_parquet


OUTER_ORIGINS = (2022, 2023, 2024)
BOOTSTRAP_REPETITIONS = 5000
CONFIGS: dict[str, dict[str, dict[str, Any]]] = {
    "sklearn_hist_gradient_boosting": {
        "compact": {
            "learning_rate": 0.03,
            "max_iter": 200,
            "max_leaf_nodes": 7,
            "max_depth": 3,
            "min_samples_leaf": 75,
            "l2_regularization": 20.0,
            "random_state": 1729,
        },
        "balanced": {
            "learning_rate": 0.04,
            "max_iter": 150,
            "max_leaf_nodes": 15,
            "max_depth": 3,
            "min_samples_leaf": 50,
            "l2_regularization": 10.0,
            "random_state": 1729,
        },
        "broad": {
            "learning_rate": 0.025,
            "max_iter": 240,
            "max_leaf_nodes": 31,
            "max_depth": 4,
            "min_samples_leaf": 40,
            "l2_regularization": 20.0,
            "random_state": 1729,
        },
    },
    "xgboost": {
        "compact": {
            "learning_rate": 0.03,
            "n_estimators": 200,
            "max_depth": 2,
            "min_child_weight": 20.0,
            "reg_lambda": 20.0,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "random_state": 1729,
        },
        "balanced": {
            "learning_rate": 0.04,
            "n_estimators": 150,
            "max_depth": 3,
            "min_child_weight": 10.0,
            "reg_lambda": 10.0,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "random_state": 1729,
        },
        "broad": {
            "learning_rate": 0.025,
            "n_estimators": 240,
            "max_depth": 4,
            "min_child_weight": 10.0,
            "reg_lambda": 20.0,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "random_state": 1729,
        },
    },
    "lightgbm": {
        "compact": {
            "learning_rate": 0.03,
            "n_estimators": 200,
            "num_leaves": 7,
            "max_depth": 3,
            "min_child_samples": 75,
            "reg_lambda": 20.0,
            "random_state": 1729,
        },
        "balanced": {
            "learning_rate": 0.04,
            "n_estimators": 150,
            "num_leaves": 15,
            "max_depth": 3,
            "min_child_samples": 50,
            "reg_lambda": 10.0,
            "random_state": 1729,
        },
        "broad": {
            "learning_rate": 0.025,
            "n_estimators": 240,
            "num_leaves": 31,
            "max_depth": 4,
            "min_child_samples": 40,
            "reg_lambda": 20.0,
            "random_state": 1729,
        },
    },
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
        "--frozen-forecast",
        type=Path,
        default=Path(
            "model_artifacts/hitter-gradient-2026-confirmation-forecast-2026-09-19/"
            "forecast-2026.parquet"
        ),
    )
    parser.add_argument(
        "--confirmation-contract",
        type=Path,
        default=Path("docs/hitter-gradient-2026-confirmation-contract.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-gradient-engine-comparison-v1"),
    )
    return parser.parse_args()


def _model(engine: str, parameters: dict[str, Any]):
    if engine == "sklearn_hist_gradient_boosting":
        return HistGradientBoostingRegressor(**parameters)
    if engine == "xgboost":
        return XGBRegressor(
            objective="reg:squarederror",
            tree_method="hist",
            n_jobs=4,
            verbosity=0,
            **parameters,
        )
    if engine == "lightgbm":
        return LGBMRegressor(
            objective="regression",
            n_jobs=4,
            verbosity=-1,
            deterministic=True,
            force_col_wise=True,
            **parameters,
        )
    raise ValueError(f"unknown engine: {engine}")


def _fit_predict(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    columns: list[str],
    *,
    engine: str,
    parameters: dict[str, Any],
) -> np.ndarray:
    x_train, x_score = _design(training, evaluation, columns)
    actual = _probabilities(training, "target__overall__")
    base_train = _probabilities(training, "contact_only__overall__")
    base_score = _probabilities(evaluation, "contact_only__overall__")
    residual = actual - base_train
    weights = training["target_contacts"].to_numpy().astype(float)
    correction = []
    for index in range(len(CONTACT_OUTCOMES)):
        fitted = _model(engine, parameters).fit(
            x_train, residual[:, index], sample_weight=weights
        )
        correction.append(fitted.predict(x_score))
    return _normalize(base_score + np.column_stack(correction))


def _inner_splits(frame: pl.DataFrame) -> list[tuple[pl.DataFrame, pl.DataFrame, int]]:
    origins = sorted(int(value) for value in frame["origin_year"].unique())
    return [
        (
            frame.filter(pl.col("origin_year") < origin),
            frame.filter(pl.col("origin_year") == origin),
            origin,
        )
        for origin in origins[1:]
    ]


def _select_config(
    training: pl.DataFrame,
    columns: list[str],
    engine: str,
) -> tuple[str, list[dict[str, object]]]:
    splits = _inner_splits(training)
    if not splits:
        return "balanced", [
            {
                "config": "balanced",
                "status": "no_prior_inner_fold_use_predeclared_default",
            }
        ]
    records = []
    for config, parameters in CONFIGS[engine].items():
        frames = []
        predictions = []
        for fit, evaluation, _ in splits:
            frames.append(evaluation)
            predictions.append(
                _fit_predict(
                    fit,
                    evaluation,
                    columns,
                    engine=engine,
                    parameters=parameters,
                )
            )
        combined = pl.concat(frames, how="vertical_relaxed")
        actual = _probabilities(combined, "target__overall__")
        weights = combined["target_contacts"].to_numpy().astype(float)
        metrics = _metrics(actual, np.vstack(predictions), weights)
        records.append(
            {
                "config": config,
                "inner_origins": [origin for _, _, origin in splits],
                **metrics,
            }
        )
    selected = min(
        records,
        key=lambda row: (
            float(row["rate_rmse"]),
            float(row["multinomial_log_loss"]),
            str(row["config"]),
        ),
    )
    return str(selected["config"]), records


def main() -> int:
    args = _args()
    contract = json.loads(args.confirmation_contract.read_text(encoding="utf-8"))
    frozen_before = sha256_file(args.frozen_forecast)
    if frozen_before != contract["forecast_sha256"]:
        raise RuntimeError("protected 2026 forecast differs from its locked hash")
    frame = pl.read_parquet(args.dataset)
    if frame.filter(pl.col("target_season") >= 2026).height:
        raise RuntimeError("engine comparison must not contain a 2026 target")
    columns = _families(frame)["plus_park"]
    output_frames = []
    fold_records = []
    tuning_records = []
    for origin in OUTER_ORIGINS:
        training = frame.filter(pl.col("origin_year") < origin)
        evaluation = frame.filter(pl.col("origin_year") == origin)
        actual = _probabilities(evaluation, "target__overall__")
        baseline = _probabilities(evaluation, "contact_only__overall__")
        weights = evaluation["target_contacts"].to_numpy().astype(float)
        base_metrics = _metrics(actual, baseline, weights)
        predictions = {}
        for engine in CONFIGS:
            selected, tuning = _select_config(training, columns, engine)
            tuning_records.append(
                {
                    "outer_origin": origin,
                    "engine": engine,
                    "selected_config": selected,
                    "candidates": tuning,
                }
            )
            prediction = _fit_predict(
                training,
                evaluation,
                columns,
                engine=engine,
                parameters=CONFIGS[engine][selected],
            )
            predictions[engine] = prediction
            metrics = _metrics(actual, prediction, weights)
            fold_records.append(
                {
                    "origin_year": origin,
                    "engine": engine,
                    "selected_config": selected,
                    "players": evaluation.height,
                    **metrics,
                    **{
                        f"{name}_vs_contact_only": metrics[name] - base_metrics[name]
                        for name in base_metrics
                    },
                }
            )
        output = evaluation.select(
            "origin_year", "player_id", "source_level", "target_source_level", "target_contacts"
        ).with_columns(
            *(
                pl.Series(f"actual__{outcome}", actual[:, index])
                for index, outcome in enumerate(CONTACT_OUTCOMES)
            ),
            *(
                pl.Series(f"contact_only__{outcome}", baseline[:, index])
                for index, outcome in enumerate(CONTACT_OUTCOMES)
            ),
        )
        for engine, prediction in predictions.items():
            output = output.with_columns(
                *(
                    pl.Series(f"{engine}__{outcome}", prediction[:, index])
                    for index, outcome in enumerate(CONTACT_OUTCOMES)
                )
            )
        output_frames.append(output)
        print(f"completed outer origin {origin}", flush=True)

    predictions = pl.concat(output_frames, how="vertical_relaxed")
    actual = predictions.select(
        *(f"actual__{value}" for value in CONTACT_OUTCOMES)
    ).to_numpy()
    weights = predictions["target_contacts"].to_numpy().astype(float)
    players = predictions["player_id"].to_numpy()
    names = ["contact_only", *CONFIGS]
    matrices = {
        name: predictions.select(
            *(f"{name}__{value}" for value in CONTACT_OUTCOMES)
        ).to_numpy()
        for name in names
    }
    pooled = {name: _metrics(actual, value, weights) for name, value in matrices.items()}
    comparisons = {}
    for engine in CONFIGS:
        references = ["contact_only"]
        if engine != "sklearn_hist_gradient_boosting":
            references.append("sklearn_hist_gradient_boosting")
        for reference in references:
            key = f"{engine}_vs_{reference}"
            comparisons[key] = {
                "point_delta": {
                    metric: pooled[engine][metric] - pooled[reference][metric]
                    for metric in pooled[engine]
                },
                "paired_player_bootstrap": paired_player_cluster_bootstrap(
                    player_ids=players,
                    actual=actual,
                    baseline=matrices[reference],
                    candidate=matrices[engine],
                    weights=weights,
                    repetitions=BOOTSTRAP_REPETITIONS,
                    seed=1729,
                ),
            }
    frozen_after = sha256_file(args.frozen_forecast)
    if frozen_after != frozen_before:
        raise RuntimeError("protected 2026 forecast changed during comparison")
    winner = min(
        CONFIGS,
        key=lambda name: (
            pooled[name]["rate_rmse"], pooled[name]["multinomial_log_loss"]
        ),
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "predictions": write_canonical_parquet(
            predictions,
            args.output_root / "predictions.parquet",
            table_name="hitter_gradient_engine_comparison_predictions",
        ).as_record(),
        "fold_metrics": write_canonical_parquet(
            pl.DataFrame(fold_records),
            args.output_root / "fold-metrics.parquet",
            table_name="hitter_gradient_engine_comparison_fold_metrics",
        ).as_record(),
    }
    report = {
        "schema_version": "1.0",
        "status": "three_engine_nested_chronological_comparison_complete",
        "as_of_date": args.as_of_date.isoformat(),
        "protected_2026_outcomes_used": False,
        "protected_2026_forecast_sha256_before": frozen_before,
        "protected_2026_forecast_sha256_after": frozen_after,
        "feature_family": "plus_park",
        "feature_count": len(columns),
        "outer_origins": list(OUTER_ORIGINS),
        "evaluated_players": predictions.height,
        "versions": {
            "sklearn": "1.7.2",
            "xgboost": "3.4.1",
            "lightgbm": "4.7.0",
        },
        "selection_rule": (
            "lowest pooled inner chronological RMSE; log loss then config name tie-break"
        ),
        "no_inner_fold_policy": "predeclared balanced configuration",
        "parameter_grid": CONFIGS,
        "tuning": tuning_records,
        "fold_metrics": fold_records,
        "pooled_metrics": pooled,
        "comparisons": comparisons,
        "best_development_engine": winner,
        "artifacts": artifacts,
        "decision_boundary": (
            "development evidence only; frozen 2026 forecast is unchanged and remains "
            "the protected confirmation candidate"
        ),
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "winner": winner,
        "pooled_metrics": pooled,
        "comparisons": comparisons,
        "frozen_2026_unchanged": frozen_before == frozen_after,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
