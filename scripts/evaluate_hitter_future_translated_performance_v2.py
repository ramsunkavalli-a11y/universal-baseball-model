#!/usr/bin/env python3
"""Test level-path features on following-year hitting at every affiliated level."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_future_translated_performance import (
    build_future_translated_targets,
    build_hitter_component_counts,
)
from universal_baseball.hitter_level_path_features import (
    COMPACT_LEVEL_PATH_FEATURES,
    add_level_path_features,
)
from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    matrix_from_panel,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


ORIGINS = (2015, 2016, 2017, 2018, 2021, 2022, 2023, 2024)
ENGINES = ("lightgbm", "xgboost", "ebm", "ridge")
KEY = ["origin_year", "target_season", "player_id"]
TARGET = "target_translated_woba"
MINIMUM_TARGET_PA = 30
GENERATED_ROOT = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
LEVEL_PATH_PATH = Path(
    "reports/generated/hitter-level-path-feature-ablation-v2/tables/level-path-features.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-future-translated-performance-v2")


def _load_stats(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    specifications = (
        (
            root
            / "affiliated-skill-source-2003-2007/tables/affiliated_hitting_components.parquet",
            range(2003, 2008),
        ),
        (
            root
            / "affiliated-skill-source-2008-2017/tables/affiliated_hitting_components.parquet",
            range(2008, 2018),
        ),
        (
            root
            / "affiliated-skill-source-2018-2022/tables/affiliated_hitting_components.parquet",
            (2018, 2019),
        ),
        (
            root
            / "phase2-arrival-skill-source/tables/affiliated_hitting_components.parquet",
            (2021, 2022, 2023, 2024, 2025),
        ),
    )
    frames = [
        pl.read_parquet(path).filter(pl.col("season").is_in(list(years)))
        for path, years in specifications
    ]
    return pl.concat(frames, how="vertical_relaxed"), [
        path for path, _ in specifications
    ]


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


def _run_variant(
    panel: pl.DataFrame, *, label: str
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    columns = _predictor_columns(panel)
    outputs: list[pl.DataFrame] = []
    fold_reports: list[dict[str, object]] = []
    for fold in expanding_year_folds(panel["origin_year"].unique().to_list()):
        train = panel.filter(pl.col("origin_year").is_in(fold.train_origins))
        test = panel.filter(pl.col("origin_year") == fold.test_origin)
        x_train = matrix_from_panel(train, columns)
        x_test = matrix_from_panel(test, columns)
        y_train = train[TARGET].to_numpy()
        weights = np.sqrt(train["target_affiliated_pa"].to_numpy())
        engine_predictions: dict[str, np.ndarray] = {}
        for engine in ENGINES:
            print(f"{label} origin {fold.test_origin}: {engine}", flush=True)
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
                pl.Series("prediction__ensemble", ensemble),
            )
        )
        fold_reports.append(
            {
                "test_origin": fold.test_origin,
                "train_origins": list(fold.train_origins),
                "train_rows": train.height,
                "test_rows": test.height,
                "feature_count": len(columns),
            }
        )
    return pl.concat(outputs).sort(KEY), fold_reports


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


def _subgroups(frame: pl.DataFrame) -> dict[str, object]:
    expressions = {
        "current_mlb": pl.col("level_path__primary_level_rank") == 6,
        "upper_minors": pl.col("level_path__primary_level_rank").is_in([4, 5]),
        "lower_minors": pl.col("level_path__primary_level_rank") <= 3,
        "rookie_level": pl.col("level_path__primary_level_rank") == 0,
        "rookie_same_primary_repeat": (
            (pl.col("level_path__primary_level_rank") == 0)
            & (pl.col("level_path__same_primary_as_prior") == 1)
        ),
        "rookie_third_or_later": (
            (pl.col("level_path__primary_level_rank") == 0)
            & (pl.col("level_path__third_or_later_at_primary") == 1)
        ),
        "same_primary_repeat": pl.col("level_path__same_primary_as_prior") == 1,
        "third_or_later_at_level": pl.col("level_path__third_or_later_at_primary") == 1,
        "returned_after_partial_promotion": pl.col(
            "level_path__returned_after_partial_promotion"
        )
        == 1,
        "advanced_next_year": pl.col("target_primary_level_rank")
        > pl.col("level_path__primary_level_rank"),
        "same_level_next_year": pl.col("target_primary_level_rank")
        == pl.col("level_path__primary_level_rank"),
        "moved_down_next_year": pl.col("target_primary_level_rank")
        < pl.col("level_path__primary_level_rank"),
    }
    result: dict[str, object] = {}
    for label, expression in expressions.items():
        subset = frame.filter(expression)
        if subset.is_empty():
            continue
        result[label] = {
            "rows": subset.height,
            "players": subset["player_id"].n_unique(),
            "actual_mean": float(subset[TARGET].mean()),
            "base_predicted_mean": float(subset["prediction__base"].mean()),
            "path_predicted_mean": float(subset["prediction__path"].mean()),
            "base": _metrics(subset, "prediction__base"),
            "path": _metrics(subset, "prediction__path"),
        }
    return result


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    table_root = OUTPUT_ROOT / "tables"
    table_root.mkdir(exist_ok=True)
    stats, stat_paths = _load_stats(GENERATED_ROOT)
    components = build_hitter_component_counts(stats)
    built = build_future_translated_targets(components, origins=ORIGINS)
    base = (
        pl.read_parquet(PANEL_PATH)
        .join(built.targets, on=KEY, how="inner", validate="1:1")
        .filter(pl.col("target_affiliated_pa") >= MINIMUM_TARGET_PA)
    )
    level_path = pl.read_parquet(LEVEL_PATH_PATH)
    full_path = add_level_path_features(pl.read_parquet(PANEL_PATH), level_path)
    path = (
        full_path.drop(
            column
            for column in full_path.columns
            if column.startswith("level_path__")
            and column not in COMPACT_LEVEL_PATH_FEATURES
        )
        .join(built.targets, on=KEY, how="inner", validate="1:1")
        .filter(pl.col("target_affiliated_pa") >= MINIMUM_TARGET_PA)
    )
    if not base.select(KEY).equals(path.select(KEY)):
        raise ValueError("base and path target populations do not align")

    target_artifact = write_canonical_parquet(
        built.targets,
        table_root / "future-translated-targets.parquet",
        table_name="hitter_future_translated_performance_v2_targets",
    )
    offset_artifact = write_canonical_parquet(
        built.translation_offsets,
        table_root / "translation-offsets.parquet",
        table_name="hitter_future_translated_performance_v2_offsets",
    )
    base_prediction, base_folds = _run_variant(base, label="base")
    path_prediction, path_folds = _run_variant(path, label="path")
    comparison = (
        base_prediction.select(
            *KEY,
            TARGET,
            "target_affiliated_pa",
            "target_primary_level_rank",
            pl.col("prediction__ensemble").alias("prediction__base"),
        )
        .join(
            path_prediction.select(
                *KEY, pl.col("prediction__ensemble").alias("prediction__path")
            ),
            on=KEY,
            validate="1:1",
        )
        .join(
            level_path.select(
                pl.col("season").alias("origin_year"),
                "player_id",
                "level_path__primary_level_rank",
                "level_path__same_primary_as_prior",
                "level_path__third_or_later_at_primary",
                "level_path__returned_after_partial_promotion",
            ),
            on=["origin_year", "player_id"],
            how="left",
            validate="1:1",
        )
    )
    actual = comparison[TARGET].to_numpy()
    paired = paired_cluster_rmse_delta(
        actual,
        comparison["prediction__path"].to_numpy(),
        comparison["prediction__base"].to_numpy(),
        comparison["player_id"].to_numpy(),
    )
    folds = {}
    for origin in comparison["origin_year"].unique().sort().to_list():
        subset = comparison.filter(pl.col("origin_year") == origin)
        folds[str(origin)] = {
            "base": _metrics(subset, "prediction__base"),
            "path": _metrics(subset, "prediction__path"),
        }
    engine_metrics = {
        variant: {
            engine: _metrics(frame, f"prediction__{engine}") for engine in ENGINES
        }
        for variant, frame in {
            "base": base_prediction,
            "path": path_prediction,
        }.items()
    }
    prediction_artifact = write_canonical_parquet(
        comparison,
        table_root / "predictions.parquet",
        table_name="hitter_future_translated_performance_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "future_all_level_translated_hitting_evaluation_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "question": (
            "After translating the level actually played next season onto one MLB "
            "component scale, do prior level tenure and movement features improve "
            "the forecast of next-season hitting quality?"
        ),
        "target": (
            "following-season seven-component batting profile translated from each "
            "actual affiliated level to the MLB scale using offsets fitted only "
            "through the forecast origin, summarized as neutral-weight wOBA"
        ),
        "target_condition": f"at least {MINIMUM_TARGET_PA} affiliated PA next season",
        "rows": comparison.height,
        "players": comparison["player_id"].n_unique(),
        "origins": list(ORIGINS),
        "base_feature_count": len(_predictor_columns(base)),
        "path_feature_count": len(COMPACT_LEVEL_PATH_FEATURES),
        "base": _metrics(comparison, "prediction__base"),
        "path": _metrics(comparison, "prediction__path"),
        "path_minus_base": paired,
        "folds": folds,
        "subgroups": _subgroups(comparison),
        "engine_metrics": engine_metrics,
        "fit_folds": {"base": base_folds, "path": path_folds},
        "translation_folds": list(built.fold_metrics),
        "decision_rule": (
            "Use this result to decide whether level path belongs in conditional "
            "hitting quality. Do not alter the frozen 2026 forecast."
        ),
        "sources": [
            {"path": str(path_value), "sha256": sha256_file(path_value)}
            for path_value in [*stat_paths, PANEL_PATH, LEVEL_PATH_PATH]
        ],
        "artifacts": {
            "targets": target_artifact.as_record(),
            "translation_offsets": offset_artifact.as_record(),
            "predictions": prediction_artifact.as_record(),
        },
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "base": report["base"],
                "path": report["path"],
                "path_minus_base": paired,
                "folds": folds,
                "subgroups": report["subgroups"],
                "engine_metrics": engine_metrics,
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
