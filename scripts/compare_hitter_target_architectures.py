#!/usr/bin/env python3
"""Compare direct, two-part, and three-part next-season hitter value models."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
    run_lightgbm_architecture_fold,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--panel",
        type=Path,
        default=Path(
            "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-target-architecture-v1"),
    )
    return parser.parse_args()


def main() -> None:
    args = _args()
    panel = pl.read_parquet(args.panel)
    folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    predictions: list[pl.DataFrame] = []
    fold_reports: list[dict[str, object]] = []
    aggregate_importance: dict[str, float] = {}
    for fold in folds:
        print(f"fitting architecture fold with origin {fold.test_origin}", flush=True)
        fold_predictions, metrics, importance = run_lightgbm_architecture_fold(
            panel, fold
        )
        predictions.append(fold_predictions)
        fold_reports.append(
            {
                "test_origin": fold.test_origin,
                "target_season": fold.test_origin + 1,
                "train_origins": list(fold.train_origins),
                "test_players": fold_predictions.height,
                "metrics": metrics,
            }
        )
        for feature, value in importance.items():
            aggregate_importance[feature] = aggregate_importance.get(feature, 0.0) + value

    combined = pl.concat(predictions)
    actual = combined["actual_component_war"].to_numpy()
    pooled = {
        architecture: regression_metrics(
            actual, combined[f"prediction_{architecture}"].to_numpy()
        )
        for architecture in ("zero", "train_mean", "direct", "two_part", "three_part")
    }
    pooled["active_probability"] = classification_metrics(
        combined["actual_active"].to_numpy(),
        combined["active_probability"].to_numpy(),
    )
    player_ids = combined["player_id"].to_numpy()
    comparisons = {
        "two_part_minus_direct": paired_cluster_rmse_delta(
            actual,
            combined["prediction_two_part"].to_numpy(),
            combined["prediction_direct"].to_numpy(),
            player_ids,
        ),
        "three_part_minus_direct": paired_cluster_rmse_delta(
            actual,
            combined["prediction_three_part"].to_numpy(),
            combined["prediction_direct"].to_numpy(),
            player_ids,
        ),
        "two_part_minus_three_part": paired_cluster_rmse_delta(
            actual,
            combined["prediction_two_part"].to_numpy(),
            combined["prediction_three_part"].to_numpy(),
            player_ids,
        ),
    }
    segments = {
        "current_mlb": pl.col("current_mlb_pa") > 0,
        "upper_minors": (
            (pl.col("current_mlb_pa") == 0)
            & pl.col("current_highest_level").is_in(["AA", "AAA"])
        ),
        "lower_minors": (
            (pl.col("current_mlb_pa") == 0)
            & ~pl.col("current_highest_level").is_in(["AA", "AAA"])
        ),
        "current_pa_under_100": pl.col("current_pa") < 100,
        "current_pa_100_to_299": pl.col("current_pa").is_between(100, 299),
        "current_pa_300_plus": pl.col("current_pa") >= 300,
    }
    segment_metrics: dict[str, dict[str, object]] = {}
    for name, expression in segments.items():
        segment = combined.filter(expression)
        segment_actual = segment["actual_component_war"].to_numpy()
        segment_metrics[name] = {
            "rows": segment.height,
            "actual_active_rate": float(segment["actual_active"].mean()),
            "architectures": {
                architecture: regression_metrics(
                    segment_actual,
                    segment[f"prediction_{architecture}"].to_numpy(),
                )
                for architecture in ("direct", "two_part", "three_part")
            },
        }
    ranked_importance = sorted(
        aggregate_importance.items(), key=lambda item: item[1], reverse=True
    )
    total_gain = sum(value for _, value in ranked_importance) or 1.0
    report = {
        "schema_version": "0.1",
        "status": "hitter_target_architectures_compared",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "engine": "LightGBM with one fixed conservative configuration",
        "primary_target": "next-season zero-inclusive MLB batting-plus-replacement WAR",
        "architectures": {
            "direct": "one model predicts total next-season value, including zero",
            "two_part": "MLB-active probability times total WAR conditional on being active",
            "three_part": (
                "MLB-active probability times conditional PA times conditional WAR rate"
            ),
        },
        "rate_model_weighting": "square root of target MLB plate appearances",
        "folds": fold_reports,
        "pooled_metrics": pooled,
        "paired_player_cluster_comparisons": comparisons,
        "segment_metrics": segment_metrics,
        "top_direct_model_features": [
            {"feature": feature, "gain_share": value / total_gain}
            for feature, value in ranked_importance[:30]
        ],
        "limitations": [
            "This stage compares target structure, not the final engine tournament.",
            "Value currently includes batting plus replacement only.",
            "Park/opponent-neutral features are not yet added to this clean-slate panel.",
            "The 2025 PBP source is partial and 2026 remains sealed.",
        ],
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        combined,
        tables / "chronological_predictions.parquet",
        table_name="hitter_target_architecture_v1_predictions",
    )
    report["prediction_artifact"] = artifact.as_record()
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report["pooled_metrics"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
