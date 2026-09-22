#!/usr/bin/env python3
"""Compare pitcher direct, two-part, and workload/rate value architectures."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_target_architecture import (
    run_pitcher_architecture_fold,
)
from universal_baseball.storage import write_canonical_parquet


ENGINES = ("ridge", "catboost", "ebm", "lightgbm")


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
        default=Path("reports/generated/pitcher-target-architectures-v2"),
    )
    parser.add_argument("--engines", default=",".join(ENGINES))
    parser.add_argument("--minimum-train-years", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = _args()
    panel = pl.read_parquet(args.panel)
    folds = expanding_year_folds(
        panel["origin_year"].unique().to_list(),
        minimum_train_years=args.minimum_train_years,
    )
    engines = [engine.strip() for engine in args.engines.split(",") if engine.strip()]
    args.output_root.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "schema_version": "0.1",
        "status": "architecture_comparison_in_progress",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "fold_origins": [fold.test_origin for fold in folds],
        "engines": {},
    }
    for engine in engines:
        print(f"starting architecture engine {engine}", flush=True)
        pieces = []
        fold_reports = []
        for fold in folds:
            print(f"  fitting origin {fold.test_origin}", flush=True)
            predictions, metrics = run_pitcher_architecture_fold(panel, fold, engine)
            pieces.append(predictions)
            fold_reports.append({"test_origin": fold.test_origin, "metrics": metrics})
        combined = pl.concat(pieces)
        actual = combined["actual_component_war"].to_numpy()
        pooled = {
            architecture: regression_metrics(
                actual, combined[f"prediction_{architecture}"].to_numpy()
            )
            for architecture in ("direct", "two_part", "three_part")
        }
        comparisons = {
            f"{architecture}_minus_two_part": paired_cluster_rmse_delta(
                actual,
                combined[f"prediction_{architecture}"].to_numpy(),
                combined["prediction_two_part"].to_numpy(),
                combined["player_id"].to_numpy(),
                bootstrap_samples=5_000,
            )
            for architecture in ("direct", "three_part")
        }
        artifact = write_canonical_parquet(
            combined,
            args.output_root / f"{engine}-predictions.parquet",
            table_name=f"pitcher_target_architecture_v2_{engine}",
        ).as_record()
        report["engines"][engine] = {
            "pooled_metrics": pooled,
            "comparisons": comparisons,
            "folds": fold_reports,
            "artifact": artifact,
        }
        (args.output_root / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    report["status"] = "architecture_comparison_complete"
    report["generated_at_utc"] = datetime.now(UTC).isoformat()
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                engine: details["pooled_metrics"]
                for engine, details in report["engines"].items()
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
