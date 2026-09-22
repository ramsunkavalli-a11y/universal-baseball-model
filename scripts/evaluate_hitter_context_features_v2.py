#!/usr/bin/env python3
"""Test park/opponent context as an optional feature family in the value model."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_context_features import add_context_history
from universal_baseball.hitter_model_tournament import run_engine_fold
from universal_baseball.hitter_target_architecture import (
    Fold,
    feature_columns,
    paired_cluster_rmse_delta,
    regression_metrics,
    run_lightgbm_architecture_fold,
)
from universal_baseball.storage import write_canonical_parquet


PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
CONTEXT_PATH = Path(
    "reports/generated/hitter-gradient-dataset-v1/tables/"
    "player-season-features.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-context-feature-ablation-v2")
KEY = ["origin_year", "target_season", "player_id"]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lags",
        default="0,1,2",
        help="comma-separated exact season lags to join",
    )
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    return parser.parse_args()


def main() -> None:
    args = _args()
    lags = tuple(int(value) for value in args.lags.split(",") if value.strip())
    panel = pl.read_parquet(PANEL_PATH)
    context = pl.read_parquet(CONTEXT_PATH)
    augmented = add_context_history(panel, context, lags=lags)
    folds = [
        Fold(2023, (2015, 2016, 2017, 2018, 2021, 2022)),
        Fold(2024, (2015, 2016, 2017, 2018, 2021, 2022, 2023)),
    ]
    variants = {engine: {2023: "balanced", 2024: "balanced"} for engine in (
        "xgboost",
        "ebm",
        "ridge",
    )}
    predictions: dict[str, pl.DataFrame] = {}
    engine_reports: dict[str, object] = {}

    architecture_frames: list[pl.DataFrame] = []
    architecture_reports: list[dict[str, object]] = []
    for fold in folds:
        print(
            f"fitting LightGBM architectures with context for origin {fold.test_origin}",
            flush=True,
        )
        result, metrics, _ = run_lightgbm_architecture_fold(augmented, fold)
        architecture_frames.append(result)
        architecture_reports.append(
            {"test_origin": fold.test_origin, "metrics": metrics}
        )
    context_architecture = pl.concat(architecture_frames).sort(KEY)
    for engine, fold_variants in variants.items():
        frames: list[pl.DataFrame] = []
        fold_reports: list[dict[str, object]] = []
        for fold in folds:
            variant = fold_variants[fold.test_origin]
            print(
                f"fitting {engine} with context for origin {fold.test_origin}",
                flush=True,
            )
            result, metrics = run_engine_fold(
                augmented, fold, engine, variant=variant
            )
            frames.append(result)
            fold_reports.append(
                {
                    "test_origin": fold.test_origin,
                    "variant": variant,
                    "metrics": metrics,
                }
            )
        combined = pl.concat(frames).sort(KEY)
        predictions[engine] = combined
        engine_reports[engine] = {"folds": fold_reports}

    baseline_sources = {
        "xgboost": Path(
            "reports/generated/hitter-model-engine-tournament-v2/tables/"
            "xgboost-predictions.parquet"
        ),
        "ebm": Path(
            "reports/generated/hitter-model-engine-tournament-v2/tables/"
            "ebm-predictions.parquet"
        ),
        "ridge": Path(
            "reports/generated/hitter-model-engine-tournament-v2/tables/"
            "ridge-predictions.parquet"
        ),
    }
    baselines = {
        engine: pl.read_parquet(path)
        .filter(pl.col("origin_year").is_in([2023, 2024]))
        .sort(KEY)
        for engine, path in baseline_sources.items()
    }
    baseline_architecture = pl.read_parquet(
        "reports/generated/hitter-target-architecture-v1/tables/"
        "chronological_predictions.parquet"
    ).filter(pl.col("origin_year").is_in([2023, 2024])).sort(KEY)
    reference = baselines["xgboost"]
    actual = reference["actual_component_war"].to_numpy()
    baseline_mean = np.mean(
        np.column_stack(
            [
                baseline_architecture["prediction_direct"].to_numpy(),
                baseline_architecture["prediction_three_part"].to_numpy(),
                *(frame["predicted_component_war"].to_numpy() for frame in baselines.values()),
            ]
        ),
        axis=1,
    )
    context_mean = np.mean(
        np.column_stack(
            [
                context_architecture["prediction_direct"].to_numpy(),
                context_architecture["prediction_three_part"].to_numpy(),
                *(frame["predicted_component_war"].to_numpy() for frame in predictions.values()),
            ]
        ),
        axis=1,
    )
    output = reference.select(KEY + ["actual_component_war"]).with_columns(
        pl.Series("prediction_baseline_ensemble", baseline_mean),
        pl.Series("prediction_context_ensemble", context_mean),
    )
    comparison = paired_cluster_rmse_delta(
        actual,
        context_mean,
        baseline_mean,
        reference["player_id"].to_numpy(),
    )
    per_fold = {}
    for origin in (2023, 2024):
        mask = reference["origin_year"].to_numpy() == origin
        per_fold[str(origin)] = {
            "baseline": regression_metrics(actual[mask], baseline_mean[mask]),
            "with_context": regression_metrics(actual[mask], context_mean[mask]),
        }
    coverage_by_origin = {}
    for origin in sorted(augmented["origin_year"].unique().to_list()):
        origin_frame = augmented.filter(pl.col("origin_year") == origin)
        coverage_by_origin[str(origin)] = {
            f"lag{lag}": float(
                origin_frame[f"lag{lag}__context__available"].mean()
            )
            for lag in lags
        }
    args.output_root.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        output,
        args.output_root / "predictions.parquet",
        table_name="hitter_context_feature_ablation_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "park_opponent_context_feature_ablation_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "base_feature_count": len(feature_columns(panel)),
        "augmented_feature_count": len(feature_columns(augmented)),
        "context_coverage_seasons": sorted(context["season"].unique().to_list()),
        "context_lags": list(lags),
        "context_coverage_by_origin": coverage_by_origin,
        "evaluated_origins": [2023, 2024],
        "candidate_members": [
            "direct_lightgbm",
            "three_part_lightgbm",
            "two_part_xgboost",
            "two_part_ebm",
            "two_part_ridge",
        ],
        "baseline_ensemble": regression_metrics(actual, baseline_mean),
        "context_ensemble": regression_metrics(actual, context_mean),
        "context_minus_baseline": comparison,
        "folds": per_fold,
        "engine_context_results": engine_reports,
        "architecture_context_results": architecture_reports,
        "decision_rule": (
            "retain only if context improves pooled RMSE, does not reverse in either "
            "year, and the player-clustered interval supports a real improvement"
        ),
        "artifact": artifact.as_record(),
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
