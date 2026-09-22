#!/usr/bin/env python3
"""Test dated ball-environment features on next-season translated hitting."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_ball_environment import add_ball_environment_history
from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    matrix_from_panel,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


ENGINES = ("lightgbm", "xgboost", "ebm", "ridge")
KEY = ["origin_year", "target_season", "player_id"]
TARGET = "target_translated_woba"
MINIMUM_TARGET_PA = 30
PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
TARGET_PATH = Path(
    "reports/generated/hitter-future-translated-performance-v2/tables/"
    "future-translated-targets.parquet"
)
BASE_PREDICTION_PATH = Path(
    "reports/generated/hitter-future-translated-performance-v2/tables/"
    "predictions.parquet"
)
BALL_FEATURE_PATH = Path(
    "reports/generated/hitter-ball-environment-v1/tables/player-season-features.parquet"
)
BALL_REPORT_PATH = Path("reports/generated/hitter-ball-environment-v1/report.json")
OUTPUT_ROOT = Path("reports/generated/hitter-ball-environment-projection-v1")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--feature-scope",
        choices=("coverage", "raw", "corrected", "full"),
        default="full",
    )
    parser.add_argument("--output-root", type=Path, default=None)
    return parser.parse_args()


def _scope_ball_features(panel: pl.DataFrame, scope: str) -> pl.DataFrame:
    ball_columns = [column for column in panel.columns if "__ball__" in column]
    if scope == "full":
        return panel
    keep_suffixes = ("__available",)
    if scope == "raw":
        keep_suffixes = (
            "__available",
            "__ball_air_contacts",
            "__ball_raw_air_hr_rate",
        )
    elif scope == "corrected":
        keep_suffixes = (
            "__available",
            "__ball_air_contacts",
            "__ball_neutralized_air_hr_rate",
            "__ball_mean_regime_log_odds",
            "__ball_mean_probability_effect",
            "__ball_positive_environment_share",
        )
    return panel.drop(
        column
        for column in ball_columns
        if not any(column.endswith(suffix) for suffix in keep_suffixes)
    )


def _predictor_columns(panel: pl.DataFrame) -> list[str]:
    return [
        column
        for column in panel.columns
        if column not in {"origin_year", "target_season", "player_id"}
        and not column.startswith("target_")
    ]


def _fit_regressor(
    engine: str,
    x_train: np.ndarray,
    y_train: np.ndarray,
    weights: np.ndarray,
    x_test: np.ndarray,
) -> np.ndarray:
    models = make_engine_models(engine, random_state=417, variant="balanced")
    model = models.regressor
    if models.requires_imputation:
        from sklearn.impute import SimpleImputer

        imputer = SimpleImputer(strategy="median")
        x_train = imputer.fit_transform(x_train)
        x_test = imputer.transform(x_test)
    if engine == "ridge":
        model.fit(x_train, y_train, ridge__sample_weight=weights)
    else:
        model.fit(x_train, y_train, sample_weight=weights)
    return np.asarray(model.predict(x_test), dtype=np.float64)


def _run_ball_variant(
    panel: pl.DataFrame,
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    columns = _predictor_columns(panel)
    outputs: list[pl.DataFrame] = []
    reports: list[dict[str, object]] = []
    for fold in expanding_year_folds(panel["origin_year"].unique().to_list()):
        train = panel.filter(pl.col("origin_year").is_in(fold.train_origins))
        test = panel.filter(pl.col("origin_year") == fold.test_origin)
        x_train = matrix_from_panel(train, columns)
        x_test = matrix_from_panel(test, columns)
        y_train = train[TARGET].to_numpy()
        weights = np.sqrt(train["target_affiliated_pa"].to_numpy())
        engine_predictions: dict[str, np.ndarray] = {}
        for engine in ENGINES:
            print(f"ball origin {fold.test_origin}: {engine}", flush=True)
            engine_predictions[engine] = _fit_regressor(
                engine, x_train, y_train, weights, x_test
            )
        ensemble = np.mean(np.column_stack(list(engine_predictions.values())), axis=1)
        outputs.append(
            test.select(
                *KEY, TARGET, "target_affiliated_pa", "target_primary_level_rank"
            ).with_columns(
                *[
                    pl.Series(f"prediction__{engine}", prediction)
                    for engine, prediction in engine_predictions.items()
                ],
                pl.Series("prediction__ball", ensemble),
            )
        )
        reports.append(
            {
                "test_origin": fold.test_origin,
                "train_origins": list(fold.train_origins),
                "train_rows": train.height,
                "test_rows": test.height,
                "feature_count": len(columns),
            }
        )
    return pl.concat(outputs).sort(KEY), reports


def _weighted_metrics(
    actual: np.ndarray, prediction: np.ndarray, pa: np.ndarray
) -> dict[str, float]:
    error = prediction - actual
    return {
        "pa_weighted_rmse": float(np.sqrt(np.average(np.square(error), weights=pa))),
        "pa_weighted_mae": float(np.average(np.abs(error), weights=pa)),
        "pa_weighted_bias": float(np.average(error, weights=pa)),
    }


def _metrics(frame: pl.DataFrame, column: str) -> dict[str, float]:
    actual = frame[TARGET].to_numpy()
    prediction = frame[column].to_numpy()
    return {
        **regression_metrics(actual, prediction),
        **_weighted_metrics(
            actual, prediction, frame["target_affiliated_pa"].to_numpy()
        ),
    }


def main() -> int:
    args = _args()
    output_root = args.output_root or (
        OUTPUT_ROOT
        if args.feature_scope == "full"
        else Path(
            f"reports/generated/hitter-ball-environment-{args.feature_scope}-ablation-v1"
        )
    )
    panel = pl.read_parquet(PANEL_PATH)
    targets = pl.read_parquet(TARGET_PATH)
    annual = pl.read_parquet(BALL_FEATURE_PATH)
    augmented = (
        _scope_ball_features(
            add_ball_environment_history(panel, annual), args.feature_scope
        )
        .join(targets, on=KEY, how="inner", validate="1:1")
        .filter(pl.col("target_affiliated_pa") >= MINIMUM_TARGET_PA)
    )
    ball_prediction, fold_reports = _run_ball_variant(augmented)
    baseline = (
        pl.read_parquet(BASE_PREDICTION_PATH)
        .select(*KEY, pl.col("prediction__base"))
        .join(
            ball_prediction,
            on=KEY,
            how="inner",
            validate="1:1",
        )
        .sort(KEY)
    )
    if baseline.height != ball_prediction.height:
        raise ValueError("ball and baseline prediction populations differ")
    actual = baseline[TARGET].to_numpy()
    paired = paired_cluster_rmse_delta(
        actual,
        baseline["prediction__ball"].to_numpy(),
        baseline["prediction__base"].to_numpy(),
        baseline["player_id"].to_numpy(),
    )
    folds = {}
    for origin in baseline["origin_year"].unique().sort().to_list():
        subset = baseline.filter(pl.col("origin_year") == origin)
        folds[str(origin)] = {
            "base": _metrics(subset, "prediction__base"),
            "ball": _metrics(subset, "prediction__ball"),
        }
    coverage = {}
    for origin in augmented["origin_year"].unique().sort().to_list():
        subset = augmented.filter(pl.col("origin_year") == origin)
        coverage[str(origin)] = {
            f"lag{lag}": float(subset[f"lag{lag}__ball__available"].mean())
            for lag in (0, 1, 2)
        }
    engine_metrics = {
        engine: _metrics(baseline, f"prediction__{engine}") for engine in ENGINES
    }
    output_root.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        baseline,
        output_root / "predictions.parquet",
        table_name=(
            f"hitter_ball_environment_{args.feature_scope}_projection_v1_predictions"
        ),
    )
    report = {
        "schema_version": "0.1",
        "status": "ball_environment_projection_ablation_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "question": (
            "Do cross-fitted dated ball-environment exposure and neutralized air-HR "
            "features improve next-season hitting quality on the common MLB scale?"
        ),
        "feature_scope": args.feature_scope,
        "population": {
            "rows": baseline.height,
            "players": baseline["player_id"].n_unique(),
            "minimum_next_season_affiliated_pa": MINIMUM_TARGET_PA,
        },
        "base_feature_count": len(_predictor_columns(panel)),
        "ball_feature_count": len(_predictor_columns(augmented))
        - len(_predictor_columns(panel)),
        "base": _metrics(baseline, "prediction__base"),
        "ball": _metrics(baseline, "prediction__ball"),
        "ball_minus_base": paired,
        "folds": folds,
        "ball_engine_metrics": engine_metrics,
        "fit_folds": fold_reports,
        "coverage": coverage,
        "decision_rule": (
            "Do not alter the frozen 2026 forecast. Retain for future projection use "
            "only if the pooled RMSE improves, the uncertainty interval supports "
            "real benefit, and fold behavior is acceptably stable."
        ),
        "sources": {
            "panel": {"path": str(PANEL_PATH), "sha256": sha256_file(PANEL_PATH)},
            "targets": {
                "path": str(TARGET_PATH),
                "sha256": sha256_file(TARGET_PATH),
            },
            "baseline_predictions": {
                "path": str(BASE_PREDICTION_PATH),
                "sha256": sha256_file(BASE_PREDICTION_PATH),
            },
            "ball_features": {
                "path": str(BALL_FEATURE_PATH),
                "sha256": sha256_file(BALL_FEATURE_PATH),
            },
            "ball_report": {
                "path": str(BALL_REPORT_PATH),
                "sha256": sha256_file(BALL_REPORT_PATH),
            },
        },
        "artifact": artifact.as_record(),
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "base": report["base"],
                "ball": report["ball"],
                "ball_minus_base": report["ball_minus_base"],
                "folds": report["folds"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
