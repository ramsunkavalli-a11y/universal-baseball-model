#!/usr/bin/env python3
"""Screen model families on identical clean-slate pitcher value folds."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import traceback

import numpy as np
import polars as pl

from universal_baseball.hitter_model_tournament import SUPPORTED_ENGINES
from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_model_tournament import run_pitcher_engine_fold
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        type=Path,
        default=Path(
            "reports/generated/pitcher-value-panel-v2/tables/modeling-panel.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-model-engine-tournament-v2"),
    )
    parser.add_argument(
        "--engines",
        default=",".join(SUPPORTED_ENGINES),
        help="comma-separated engine names",
    )
    parser.add_argument(
        "--minimum-train-years",
        type=int,
        default=8,
        help="number of earlier origin seasons required before an outer test",
    )
    return parser.parse_args()


def _pooled_metrics(predictions: pl.DataFrame) -> dict[str, object]:
    actual = predictions["actual_component_war"].to_numpy()
    probability = predictions["active_probability"].to_numpy()
    active = predictions["actual_active"].to_numpy()
    active_rows = active == 1
    return {
        "total_value": regression_metrics(
            actual, predictions["predicted_component_war"].to_numpy()
        ),
        "active_probability": classification_metrics(active, probability),
        "conditional_value_active_players": regression_metrics(
            actual[active_rows],
            predictions["predicted_conditional_war"].to_numpy()[active_rows],
        ),
        "zero_benchmark": regression_metrics(actual, np.zeros(predictions.height)),
        "fold_train_mean_benchmark": regression_metrics(
            actual, predictions["prediction_train_mean"].to_numpy()
        ),
    }


def main() -> int:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(args.output_root / ".matplotlib"))
    panel = pl.read_parquet(args.panel)
    folds = expanding_year_folds(
        panel["origin_year"].unique().to_list(),
        minimum_train_years=args.minimum_train_years,
    )
    engines = [engine.strip() for engine in args.engines.split(",") if engine.strip()]
    unknown = set(engines) - set(SUPPORTED_ENGINES)
    if unknown:
        raise ValueError(f"unsupported engines: {sorted(unknown)}")
    report: dict[str, object] = {
        "schema_version": "0.1",
        "status": "screening_in_progress",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "architecture": "two-part: P(MLB active) times conditional pitcher component WAR",
        "panel_rows": panel.height,
        "fold_origins": [fold.test_origin for fold in folds],
        "engines": {},
        "notes": [
            "All engines receive the same features and expanding chronological folds.",
            "The scored population includes pitchers with zero target-season MLB value.",
            "This first screen excludes process, detailed contact, park, and matchup blocks.",
        ],
    }
    report_path = args.output_root / "report.json"
    tables = args.output_root / "tables"
    tables.mkdir(exist_ok=True)
    engine_predictions: dict[str, pl.DataFrame] = {}
    for engine in engines:
        print(f"starting engine {engine}", flush=True)
        try:
            predictions: list[pl.DataFrame] = []
            fold_metrics: list[dict[str, object]] = []
            for fold in folds:
                print(f"  fitting origin {fold.test_origin}", flush=True)
                fold_predictions, metrics = run_pitcher_engine_fold(
                    panel, fold, engine
                )
                train_mean = float(
                    panel.filter(pl.col("origin_year").is_in(fold.train_origins))[
                        "target_component_war"
                    ].mean()
                )
                fold_predictions = fold_predictions.with_columns(
                    pl.lit(train_mean).alias("prediction_train_mean")
                )
                predictions.append(fold_predictions)
                fold_metrics.append(
                    {"test_origin": fold.test_origin, "metrics": metrics}
                )
            combined = pl.concat(predictions)
            engine_predictions[engine] = combined
            artifact = write_canonical_parquet(
                combined,
                tables / f"{engine}-predictions.parquet",
                table_name=f"pitcher_model_tournament_v2_{engine}_predictions",
            )
            report["engines"][engine] = {
                "status": "completed",
                "pooled_metrics": _pooled_metrics(combined),
                "folds": fold_metrics,
                "artifact": artifact.as_record(),
            }
        except Exception as exc:  # noqa: BLE001 - preserve failures and continue
            report["engines"][engine] = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
            print(f"engine {engine} failed: {type(exc).__name__}: {exc}", flush=True)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    completed = {
        engine: details
        for engine, details in report["engines"].items()
        if details["status"] == "completed"
    }
    if completed:
        leader = min(
            completed,
            key=lambda name: completed[name]["pooled_metrics"]["total_value"]["rmse"],
        )
        reference = engine_predictions[leader]
        comparisons = {}
        for engine, predictions in engine_predictions.items():
            if engine == leader:
                continue
            comparisons[f"{engine}_minus_{leader}"] = paired_cluster_rmse_delta(
                predictions["actual_component_war"].to_numpy(),
                predictions["predicted_component_war"].to_numpy(),
                reference["predicted_component_war"].to_numpy(),
                predictions["player_id"].to_numpy(),
                bootstrap_samples=5_000,
            )
        report["leading_engine"] = leader
        report["paired_player_cluster_comparisons"] = comparisons
    report["status"] = "screening_complete"
    report["generated_at_utc"] = datetime.now(UTC).isoformat()
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = {
        engine: details.get("pooled_metrics", details.get("error"))
        for engine, details in report["engines"].items()
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
