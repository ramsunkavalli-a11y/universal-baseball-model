#!/usr/bin/env python3
"""Limited nested chronological tuning for hitter model finalists."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from time import perf_counter

import polars as pl

from universal_baseball.hitter_model_tournament import run_engine_fold
from universal_baseball.hitter_target_architecture import (
    Fold,
    classification_metrics,
    expanding_year_folds,
    regression_metrics,
)
from universal_baseball.storage import write_canonical_parquet


FINALISTS = ("ebm", "lightgbm", "xgboost", "catboost")
VARIANTS = ("smooth", "balanced", "flexible")


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
        default=Path("reports/generated/hitter-model-finalist-tuning-v2"),
    )
    parser.add_argument("--engines", default=",".join(FINALISTS))
    return parser.parse_args()


def _pooled_metrics(predictions: pl.DataFrame) -> dict[str, object]:
    actual = predictions["actual_component_war"].to_numpy()
    active = predictions["actual_active"].to_numpy()
    active_rows = active == 1
    return {
        "total_value": regression_metrics(
            actual, predictions["predicted_component_war"].to_numpy()
        ),
        "active_probability": classification_metrics(
            active, predictions["active_probability"].to_numpy()
        ),
        "conditional_value_active_players": regression_metrics(
            actual[active_rows],
            predictions["predicted_conditional_war"].to_numpy()[active_rows],
        ),
    }


def main() -> None:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "tables").mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(args.output_root / ".matplotlib"))
    engines = [engine.strip() for engine in args.engines.split(",") if engine.strip()]
    unknown = set(engines) - set(FINALISTS)
    if unknown:
        raise ValueError(f"not a finalist: {sorted(unknown)}")
    panel = pl.read_parquet(args.panel)
    outer_folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    for engine in engines:
        engine_started = perf_counter()
        predictions: list[pl.DataFrame] = []
        fold_reports: list[dict[str, object]] = []
        print(f"starting nested tuning for {engine}", flush=True)
        for outer in outer_folds:
            inner_test = outer.train_origins[-1]
            inner = Fold(
                test_origin=inner_test,
                train_origins=outer.train_origins[:-1],
            )
            candidate_metrics: dict[str, dict[str, float]] = {}
            for variant in VARIANTS:
                print(
                    f"  outer {outer.test_origin}: validating {variant} on {inner_test}",
                    flush=True,
                )
                _, metrics = run_engine_fold(panel, inner, engine, variant=variant)
                candidate_metrics[variant] = metrics["total_value"]
            selected = min(
                VARIANTS, key=lambda variant: candidate_metrics[variant]["rmse"]
            )
            print(
                f"  outer {outer.test_origin}: refitting selected {selected}",
                flush=True,
            )
            fold_predictions, outer_metrics = run_engine_fold(
                panel, outer, engine, variant=selected
            )
            fold_predictions = fold_predictions.with_columns(
                pl.lit(selected).alias("selected_variant")
            )
            predictions.append(fold_predictions)
            fold_reports.append(
                {
                    "outer_test_origin": outer.test_origin,
                    "outer_train_origins": list(outer.train_origins),
                    "inner_test_origin": inner_test,
                    "inner_train_origins": list(inner.train_origins),
                    "inner_candidate_total_value_metrics": candidate_metrics,
                    "selected_variant": selected,
                    "outer_metrics": outer_metrics,
                }
            )
        combined = pl.concat(predictions)
        artifact = write_canonical_parquet(
            combined,
            args.output_root / "tables" / f"{engine}-predictions.parquet",
            table_name=f"hitter_model_finalist_tuning_v2_{engine}_predictions",
        )
        report = {
            "schema_version": "0.1",
            "status": "nested_tuning_complete",
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "protected_2026_outcomes_used": False,
            "engine": engine,
            "variants": list(VARIANTS),
            "selection_rule": (
                "lowest total-value RMSE on the latest strictly earlier origin"
            ),
            "pooled_metrics": _pooled_metrics(combined),
            "folds": fold_reports,
            "elapsed_seconds": perf_counter() - engine_started,
            "artifact": artifact.as_record(),
        }
        (args.output_root / f"{engine}-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(json.dumps({engine: report["pooled_metrics"]}, indent=2))


if __name__ == "__main__":
    main()
