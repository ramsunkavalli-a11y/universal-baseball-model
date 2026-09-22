#!/usr/bin/env python3
"""Test explicit role and workload transitions in the clean-slate pitcher model."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_model_tournament import run_pitcher_engine_fold
from universal_baseball.pitcher_role_features import ROLE_FEATURES, add_pitcher_role_features
from universal_baseball.storage import write_canonical_parquet


PANEL_PATH = Path("reports/generated/pitcher-value-panel-v2/tables/modeling-panel.parquet")
OUTPUT_ROOT = Path("reports/generated/pitcher-role-block-v2")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=PANEL_PATH)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--engines", default="ridge,catboost,lightgbm")
    return parser.parse_args()


def _score(panel: pl.DataFrame, engine: str) -> pl.DataFrame:
    folds = expanding_year_folds(
        panel["origin_year"].unique().to_list(), minimum_train_years=8
    )
    return pl.concat(
        [run_pitcher_engine_fold(panel, fold, engine)[0] for fold in folds]
    ).sort("origin_year", "player_id")


def _metrics(frame: pl.DataFrame, column: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_component_war"].to_numpy(), frame[column].to_numpy()
    )


def main() -> int:
    args = _args()
    base_panel = pl.read_parquet(args.panel)
    role_panel = add_pitcher_role_features(base_panel)
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    report: dict[str, Any] = {
        "schema_version": "0.1",
        "status": "pitcher_role_block_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season zero-inclusive defense-independent pitcher component WAR",
        "feature_block": list(ROLE_FEATURES),
        "engines": {},
    }
    for engine in [value.strip() for value in args.engines.split(",") if value.strip()]:
        print(f"starting pitcher role engine {engine}", flush=True)
        base = _score(base_panel, engine)
        role = _score(role_panel, engine)
        comparison = base.select(
            "origin_year",
            "target_season",
            "player_id",
            "actual_component_war",
            pl.col("active_probability").alias("base_active_probability"),
            pl.col("predicted_conditional_war").alias("base_conditional_war"),
            pl.col("predicted_component_war").alias("prediction_base"),
        ).join(
            role.select(
                "origin_year",
                "target_season",
                "player_id",
                pl.col("active_probability").alias("role_active_probability"),
                pl.col("predicted_conditional_war").alias("role_conditional_war"),
                pl.col("predicted_component_war").alias("prediction_role"),
            ),
            on=["origin_year", "target_season", "player_id"],
            validate="1:1",
        ).with_columns(
            (
                pl.col("role_active_probability")
                * pl.col("base_conditional_war")
            ).alias("prediction_role_arrival_only"),
            (
                pl.col("base_active_probability")
                * pl.col("role_conditional_war")
            ).alias("prediction_role_conditional_only"),
        )
        actual = comparison["actual_component_war"].to_numpy()
        ids = comparison["player_id"].to_numpy()
        variants = {
            "base": "prediction_base",
            "role_both_parts": "prediction_role",
            "role_arrival_only": "prediction_role_arrival_only",
            "role_conditional_only": "prediction_role_conditional_only",
        }
        report["engines"][engine] = {
            "pooled": {
                name: _metrics(comparison, column)
                for name, column in variants.items()
            },
            "comparisons": {
                f"{name}_minus_base": paired_cluster_rmse_delta(
                    actual,
                    comparison[column].to_numpy(),
                    comparison["prediction_base"].to_numpy(),
                    ids,
                    bootstrap_samples=5_000,
                )
                for name, column in variants.items()
                if name != "base"
            },
            "folds": [
                {
                    "origin_year": int(key[0]),
                    **{
                        f"{name}_rmse": _metrics(fold, column)["rmse"]
                        for name, column in variants.items()
                    },
                }
                for key, fold in comparison.partition_by("origin_year", as_dict=True).items()
            ],
        }
        write_canonical_parquet(
            comparison,
            table_root / f"{engine}-predictions.parquet",
            table_name=f"pitcher_role_block_v2_{engine}_predictions",
        )
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["engines"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
