#!/usr/bin/env python3
"""Test a compact level-path block only for hitters who are not yet in MLB."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_level_path_features import COMPACT_LEVEL_PATH_FEATURES
from universal_baseball.hitter_model_tournament import run_engine_fold
from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    expanding_year_folds,
    feature_columns,
    paired_cluster_rmse_delta,
    regression_metrics,
    run_lightgbm_architecture_fold,
)
from universal_baseball.storage import write_canonical_parquet


KEY = ["origin_year", "target_season", "player_id"]
ENGINES = ("xgboost", "ebm", "ridge")
PANEL_PATH = Path(
    "reports/generated/hitter-level-path-feature-ablation-v2/tables/modeling-panel.parquet"
)
BASELINE_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-level-path-routing-v2")


def _compact_pre_mlb_panel(panel: pl.DataFrame) -> pl.DataFrame:
    missing = sorted(set(COMPACT_LEVEL_PATH_FEATURES) - set(panel.columns))
    if missing:
        raise ValueError(f"missing compact path features: {missing}")
    drop = [
        column
        for column in panel.columns
        if column.startswith("level_path__")
        and column not in COMPACT_LEVEL_PATH_FEATURES
    ]
    return panel.drop(drop).filter(pl.col("lag0__pa_level__MLB") <= 0)


def _run(panel: pl.DataFrame) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    outputs = []
    reports = []
    for fold in expanding_year_folds(panel["origin_year"].unique().to_list()):
        print(f"origin {fold.test_origin}: pre-MLB LightGBM architectures", flush=True)
        architecture, architecture_metrics, _ = run_lightgbm_architecture_fold(
            panel, fold, random_state=417
        )
        members = [
            architecture["prediction_direct"].to_numpy(),
            architecture["prediction_three_part"].to_numpy(),
        ]
        probabilities = [architecture["active_probability"].to_numpy()]
        engine_metrics = {}
        for engine in ENGINES:
            print(f"origin {fold.test_origin}: pre-MLB {engine}", flush=True)
            result, metrics = run_engine_fold(
                panel, fold, engine, random_state=417, variant="balanced"
            )
            members.append(result["predicted_component_war"].to_numpy())
            probabilities.append(result["active_probability"].to_numpy())
            engine_metrics[engine] = metrics
        outputs.append(
            architecture.select(*KEY, "actual_active", "actual_component_war").with_columns(
                pl.Series("minor_path_prediction", np.mean(members, axis=0)),
                pl.Series("minor_path_active_probability", np.mean(probabilities, axis=0)),
            )
        )
        reports.append(
            {
                "test_origin": fold.test_origin,
                "architecture_metrics": architecture_metrics,
                "engine_metrics": engine_metrics,
            }
        )
    return pl.concat(outputs).sort(KEY), reports


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_component_war"].to_numpy(), frame[prediction].to_numpy()
    )


def main() -> int:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    panel = pl.read_parquet(PANEL_PATH)
    minor_panel = _compact_pre_mlb_panel(panel)
    minor_prediction, fold_details = _run(minor_panel)
    baseline = pl.read_parquet(BASELINE_PATH).select(
        *KEY,
        "actual_active",
        "actual_component_war",
        "player_stage",
        pl.col("prediction_candidate_equal_mean").alias("baseline_prediction"),
        pl.col("prediction_candidate_mlb_active_probability").alias(
            "baseline_active_probability"
        ),
    )
    joined = baseline.join(
        minor_prediction.select(
            *KEY, "minor_path_prediction", "minor_path_active_probability"
        ),
        on=KEY,
        how="left",
        validate="1:1",
    ).with_columns(
        pl.when(pl.col("player_stage") == "current_mlb")
        .then(pl.col("baseline_prediction"))
        .otherwise(pl.col("minor_path_prediction"))
        .alias("routed_prediction"),
        pl.when(pl.col("player_stage") == "current_mlb")
        .then(pl.col("baseline_active_probability"))
        .otherwise(pl.col("minor_path_active_probability"))
        .alias("routed_active_probability"),
    )
    if joined.filter(
        pl.col("routed_prediction").is_null()
        | pl.col("routed_active_probability").is_null()
    ).height:
        raise ValueError("pre-MLB routing left missing predictions")

    actual = joined["actual_component_war"].to_numpy()
    baseline_prediction = joined["baseline_prediction"].to_numpy()
    routed_prediction = joined["routed_prediction"].to_numpy()
    paired = paired_cluster_rmse_delta(
        actual,
        routed_prediction,
        baseline_prediction,
        joined["player_id"].to_numpy(),
    )
    actual_active = joined["actual_active"].to_numpy()
    baseline_class = classification_metrics(
        actual_active, joined["baseline_active_probability"].to_numpy()
    )
    routed_class = classification_metrics(
        actual_active, joined["routed_active_probability"].to_numpy()
    )
    folds = {}
    for origin in joined["origin_year"].unique().sort().to_list():
        subset = joined.filter(pl.col("origin_year") == origin)
        folds[str(origin)] = {
            "baseline": _metrics(subset, "baseline_prediction"),
            "routed": _metrics(subset, "routed_prediction"),
        }
    stages = {}
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        subset = joined.filter(pl.col("player_stage") == stage)
        stages[stage] = {
            "rows": subset.height,
            "baseline": _metrics(subset, "baseline_prediction"),
            "routed": _metrics(subset, "routed_prediction"),
        }

    artifact = write_canonical_parquet(
        joined,
        OUTPUT_ROOT / "predictions.parquet",
        table_name="hitter_level_path_routing_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "pre_mlb_level_path_routing_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "design": (
            "Keep the incumbent forecast for current MLB hitters. For hitters with "
            "zero current-season MLB PA, fit the same five model members only on "
            "historical pre-MLB rows and add the compact nonredundant path block."
        ),
        "compact_path_features": list(COMPACT_LEVEL_PATH_FEATURES),
        "base_feature_count": len(
            [column for column in feature_columns(minor_panel) if not column.startswith("level_path__")]
        ),
        "path_feature_count": len(COMPACT_LEVEL_PATH_FEATURES),
        "baseline": _metrics(joined, "baseline_prediction"),
        "routed": _metrics(joined, "routed_prediction"),
        "routed_minus_baseline": paired,
        "active_probability": {
            "baseline": baseline_class,
            "routed": routed_class,
            "brier_delta": routed_class["brier"] - baseline_class["brier"],
            "log_loss_delta": routed_class["log_loss"] - baseline_class["log_loss"],
        },
        "folds": folds,
        "stages": stages,
        "fold_fit_details": fold_details,
        "artifact": artifact.as_record(),
        "decision_note": (
            "This test establishes the value of the complete pre-MLB expert. A "
            "no-path pre-MLB expert is required next if it wins, to isolate how much "
            "of the gain comes from path fields versus stage-specific training."
        ),
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "baseline": report["baseline"],
                "routed": report["routed"],
                "routed_minus_baseline": paired,
                "active_probability": report["active_probability"],
                "folds": folds,
                "stages": stages,
            },
            indent=2,
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
