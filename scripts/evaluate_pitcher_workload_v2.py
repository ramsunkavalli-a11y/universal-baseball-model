#!/usr/bin/env python3
"""Evaluate standalone pitcher workload forecasts and role-transition features."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_role_features import add_pitcher_role_features
from universal_baseball.pitcher_workload_model import run_pitcher_workload_fold
from universal_baseball.projection_ensemble import chronological_greedy_equal_ensemble
from universal_baseball.storage import sha256_file, write_canonical_parquet


PANEL_PATH = Path("reports/generated/pitcher-value-panel-v2/tables/modeling-panel.parquet")
OUTPUT_ROOT = Path("reports/generated/pitcher-workload-v2")
ENGINES = ("ridge", "catboost", "lightgbm", "ebm")
ROLE_ENGINES = {"ridge", "catboost", "lightgbm"}
MINIMUM_GAIN_BF = 0.25


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", type=Path, default=PANEL_PATH)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--engines", default=",".join(ENGINES))
    return parser.parse_args()


def _score(panel: pl.DataFrame, engine: str) -> pl.DataFrame:
    folds = expanding_year_folds(
        panel["origin_year"].unique().to_list(), minimum_train_years=8
    )
    return pl.concat(
        [run_pitcher_workload_fold(panel, fold, engine)[0] for fold in folds]
    ).sort("origin_year", "player_id")


def _regression(frame: pl.DataFrame, column: str) -> dict[str, float]:
    return regression_metrics(frame["actual_bf"].to_numpy(), frame[column].to_numpy())


def main() -> int:
    args = _args()
    base_panel = pl.read_parquet(args.panel)
    role_panel = add_pitcher_role_features(base_panel)
    engines = [value.strip() for value in args.engines.split(",") if value.strip()]
    combined: pl.DataFrame | None = None
    member_columns: list[str] = []
    role_candidate_predictions: list[np.ndarray] = []
    engine_reports: dict[str, Any] = {}
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"

    for engine in engines:
        print(f"starting pitcher workload engine {engine}", flush=True)
        base = _score(base_panel, engine)
        report: dict[str, Any] = {"base": _regression(base, "predicted_expected_bf")}
        if engine in ROLE_ENGINES:
            role = _score(role_panel, engine)
            comparison = base.select(
                "origin_year",
                "target_season",
                "player_id",
                "actual_active",
                "actual_bf",
                pl.col("active_probability").alias("base_active_probability"),
                pl.col("predicted_conditional_bf").alias("base_conditional_bf"),
                pl.col("predicted_expected_bf").alias("prediction_base"),
            ).join(
                role.select(
                    "origin_year",
                    "player_id",
                    pl.col("active_probability").alias("role_active_probability"),
                    pl.col("predicted_conditional_bf").alias("role_conditional_bf"),
                    pl.col("predicted_expected_bf").alias("prediction_role"),
                ),
                on=["origin_year", "player_id"],
                validate="1:1",
            )
            report["role"] = _regression(comparison, "prediction_role")
            report["role_minus_base"] = paired_cluster_rmse_delta(
                comparison["actual_bf"].to_numpy(),
                comparison["prediction_role"].to_numpy(),
                comparison["prediction_base"].to_numpy(),
                comparison["player_id"].to_numpy(),
                bootstrap_samples=5_000,
            )
            role_candidate_predictions.append(role["predicted_expected_bf"].to_numpy())
            write_canonical_parquet(
                comparison,
                table_root / f"{engine}-base-role-comparison.parquet",
                table_name=f"pitcher_workload_v2_{engine}_base_role",
            )
        else:
            role_candidate_predictions.append(
                base["predicted_expected_bf"].to_numpy()
            )
        engine_reports[engine] = report
        member = f"prediction__{engine}"
        member_columns.append(member)
        piece = base.select(
            "origin_year",
            "player_id",
            "actual_active",
            "actual_bf",
            pl.col("active_probability").alias(f"probability__{engine}"),
            pl.col("predicted_conditional_bf").alias(f"conditional_bf__{engine}"),
            pl.col("predicted_expected_bf").alias(member),
        )
        if combined is None:
            combined = piece
        else:
            combined = combined.join(
                piece.drop("actual_active", "actual_bf"),
                on=["origin_year", "player_id"],
                validate="1:1",
            )
    if combined is None:
        raise ValueError("no pitcher workload engines requested")

    combined = combined.with_columns(
        pl.Series(
            "prediction_all_equal",
            np.mean([combined[column].to_numpy() for column in member_columns], axis=0),
        ),
        pl.Series(
            "probability_all_equal",
            np.mean(
                [
                    combined[f"probability__{engine}"].to_numpy()
                    for engine in engines
                ],
                axis=0,
            ),
        ),
        pl.Series(
            "conditional_bf_all_equal",
            np.mean(
                [
                    combined[f"conditional_bf__{engine}"].to_numpy()
                    for engine in engines
                ],
                axis=0,
            ),
        ),
        pl.Series(
            "prediction_role_feature_all_equal",
            np.mean(role_candidate_predictions, axis=0),
        ),
    )
    chronology, selections = chronological_greedy_equal_ensemble(
        combined,
        member_columns,
        actual_column="actual_bf",
        minimum_rmse_gain=MINIMUM_GAIN_BF,
    )
    combined = combined.join(
        chronology.select(
            "origin_year",
            "player_id",
            pl.col("prediction_chronology_pruned_equal").alias(
                "prediction_selected_expected_bf"
            ),
        ),
        on=["origin_year", "player_id"],
        validate="1:1",
    )
    panel_benchmarks = base_panel.select(
        "origin_year",
        "player_id",
        pl.col("lag0__bf_level__MLB").alias("prediction_last_mlb_bf"),
    )
    combined = combined.join(
        panel_benchmarks,
        on=["origin_year", "player_id"],
        validate="1:1",
    ).sort("origin_year", "player_id")

    actual = combined["actual_bf"].to_numpy()
    ids = combined["player_id"].to_numpy()
    selected = combined["prediction_selected_expected_bf"].to_numpy()
    metrics = {
        "last_mlb_bf": _regression(combined, "prediction_last_mlb_bf"),
        "all_equal": _regression(combined, "prediction_all_equal"),
        "role_feature_all_equal_challenger": _regression(
            combined, "prediction_role_feature_all_equal"
        ),
        "chronology_pruned_equal": _regression(
            combined, "prediction_selected_expected_bf"
        ),
    }
    comparisons = {
        "selected_minus_last_mlb_bf": paired_cluster_rmse_delta(
            actual,
            selected,
            combined["prediction_last_mlb_bf"].to_numpy(),
            ids,
            bootstrap_samples=5_000,
        ),
        "selected_minus_all_equal": paired_cluster_rmse_delta(
            actual,
            selected,
            combined["prediction_all_equal"].to_numpy(),
            ids,
            bootstrap_samples=5_000,
        ),
        "role_feature_all_equal_minus_selected": paired_cluster_rmse_delta(
            actual,
            combined["prediction_role_feature_all_equal"].to_numpy(),
            selected,
            ids,
            bootstrap_samples=5_000,
        ),
    }
    by_origin = {
        str(origin): {
            name: _regression(combined.filter(pl.col("origin_year") == origin), column)
            for name, column in {
                "last_mlb_bf": "prediction_last_mlb_bf",
                "all_equal": "prediction_all_equal",
                "role_feature_all_equal_challenger": (
                    "prediction_role_feature_all_equal"
                ),
                "chronology_pruned_equal": "prediction_selected_expected_bf",
            }.items()
        }
        for origin in sorted(combined["origin_year"].unique().to_list())
    }

    artifact = write_canonical_parquet(
        combined,
        args.output_root / "predictions.parquet",
        table_name="pitcher_workload_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "pitcher_workload_forecast_evaluated",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season zero-inclusive MLB batters faced",
        "architecture": (
            "MLB arrival probability multiplied by conditional batters faced; "
            "role-transition features are tested separately in Ridge, CatBoost, "
            "and LightGBM"
        ),
        "selected_model": (
            "chronology-pruned equal base-feature ensemble; the role-feature "
            "challenger is not selected"
        ),
        "members": engines,
        "engine_reports": engine_reports,
        "metrics": metrics,
        "comparisons": comparisons,
        "by_origin": by_origin,
        "chronological_selections": selections,
        "artifact": artifact.as_record(),
        "sources": {
            "panel": {"path": str(args.panel), "sha256": sha256_file(args.panel)}
        },
        "limitations": [
            "This workload forecast supports opportunity and team-capacity accounting; it does not replace the better two-part total-value forecast.",
            "The current benchmark carries forward only prior MLB batters faced and is intentionally simple.",
            "Organization depth and team innings limits are not inputs yet.",
            "The final 2026 outcome remains sealed.",
        ],
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
