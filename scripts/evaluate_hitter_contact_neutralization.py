#!/usr/bin/env python3
"""Test whether held-out neutralized contact skill improves next-year hitter value."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_model_tournament import run_engine_fold
from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    expanding_year_folds,
    feature_columns,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import write_canonical_parquet


PREFIX = "contact_neutral_lag"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        type=Path,
        default=Path(
            "reports/generated/hitter-contact-neutralization-v1/"
            "tables/modeling-panel.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-contact-neutralization-ablation-v1"),
    )
    parser.add_argument("--variants", default="")
    parser.add_argument("--reuse-existing", action="store_true")
    return parser.parse_args()


def _variants(panel: pl.DataFrame) -> dict[str, pl.DataFrame]:
    added = [column for column in panel.columns if column.startswith(PREFIX)]
    if not added:
        raise ValueError("panel has no neutralized contact features")
    overall = [
        column
        for column in added
        if "__neutral_overall__" in column
        or column.endswith("__neutral_contact_events")
        or column.endswith("__neutral_contact_levels")
        or column.endswith("__available")
    ]
    residual = [column for column in added if "__neutral_shape__" not in column]
    shape = [
        column
        for column in added
        if "__neutral_shape__" in column
        or column.endswith("__neutral_contact_events")
        or column.endswith("__neutral_contact_levels")
        or column.endswith("__available")
    ]

    def select(columns: list[str]) -> pl.DataFrame:
        allowed = set(columns)
        return panel.select(
            column
            for column in panel.columns
            if not column.startswith(PREFIX) or column in allowed
        )

    return {
        "base": panel.drop(added),
        "base_plus_shape": select(shape),
        "base_plus_overall_residual": select(overall),
        "base_plus_all_residuals": select(residual),
        "base_plus_shape_and_all_residuals": panel,
    }


def _metrics(predictions: pl.DataFrame) -> dict[str, object]:
    actual = predictions["actual_component_war"].to_numpy()
    active = predictions["actual_active"].to_numpy()
    active_rows = active == 1
    return {
        "rows": predictions.height,
        "players": predictions["player_id"].n_unique(),
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


def main() -> int:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(exist_ok=True)
    panel = pl.read_parquet(args.panel)
    variants = _variants(panel)
    if args.variants:
        requested = {value.strip() for value in args.variants.split(",") if value.strip()}
        requested.add("base")
        if unknown := requested - set(variants):
            raise ValueError(f"unknown variants: {sorted(unknown)}")
        variants = {name: frame for name, frame in variants.items() if name in requested}
    folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    predictions: dict[str, pl.DataFrame] = {}
    report: dict[str, object] = {
        "schema_version": "1.0",
        "status": "evaluation_in_progress",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "variants": {},
    }
    report_path = args.output_root / "report.json"
    for name, variant in variants.items():
        print(f"lightgbm: {name} ({len(feature_columns(variant))} features)", flush=True)
        artifact_path = table_root / f"{name}-predictions.parquet"
        if args.reuse_existing and artifact_path.exists():
            combined = pl.read_parquet(artifact_path)
            fold_metrics = []
        else:
            fold_predictions: list[pl.DataFrame] = []
            fold_metrics = []
            for fold in folds:
                result, metrics = run_engine_fold(
                    variant, fold, "lightgbm", random_state=417
                )
                fold_predictions.append(result)
                fold_metrics.append({"test_origin": fold.test_origin, "metrics": metrics})
            combined = pl.concat(fold_predictions)
        predictions[name] = combined
        artifact = write_canonical_parquet(
            combined,
            artifact_path,
            table_name=f"hitter_contact_neutralization_{name}_v1",
        )
        report["variants"][name] = {
            "feature_count": len(feature_columns(variant)),
            "pooled_metrics": _metrics(combined),
            "fold_metrics": fold_metrics,
            "artifact": artifact.as_record(),
        }
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    base = predictions["base"]
    comparisons = {}
    for name, challenger in predictions.items():
        if name == "base":
            continue
        comparison = paired_cluster_rmse_delta(
            challenger["actual_component_war"].to_numpy(),
            challenger["predicted_component_war"].to_numpy(),
            base["predicted_component_war"].to_numpy(),
            challenger["player_id"].to_numpy(),
        )
        challenger_classification = classification_metrics(
            challenger["actual_active"].to_numpy(),
            challenger["active_probability"].to_numpy(),
        )
        base_classification = classification_metrics(
            base["actual_active"].to_numpy(), base["active_probability"].to_numpy()
        )
        comparison.update(
            {
                "brier_delta": (
                    challenger_classification["brier"]
                    - base_classification["brier"]
                ),
                "log_loss_delta": (
                    challenger_classification["log_loss"]
                    - base_classification["log_loss"]
                ),
            }
        )
        comparisons[f"{name}_minus_base"] = comparison
    report["comparisons"] = comparisons
    report["status"] = "chronological_evaluation_complete"
    report["generated_at_utc"] = datetime.now(UTC).isoformat()
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                name: details["pooled_metrics"]["total_value"]["rmse"]
                for name, details in report["variants"].items()
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
