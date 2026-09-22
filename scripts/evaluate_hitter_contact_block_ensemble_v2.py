#!/usr/bin/env python3
"""Ablate detailed contact information inside the fixed five-model ensemble."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

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
NEW_PREFIX = "contact_neutral_lag"
ENGINES = ("xgboost", "ebm", "ridge")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        type=Path,
        default=Path(
            "reports/generated/hitter-contact-neutralization-v2/"
            "tables/modeling-panel.parquet"
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path(
            "reports/generated/hitter-model-finalist-tuning-v2/"
            "tables/finalist-ensemble-predictions.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-contact-block-ensemble-v2"),
    )
    parser.add_argument("--variants", default="")
    parser.add_argument("--reuse-existing", action="store_true")
    return parser.parse_args()


def _is_old_contact(column: str) -> bool:
    if not column.startswith(("lag0__", "lag1__", "lag2__")):
        return False
    field = column.split("__", 1)[1]
    return (
        field in {
            "contact_events",
            "log_contact_events",
            "contact_highest_level",
            "contact_feature_available",
        }
        or field.startswith("contacts_level__")
        or field.startswith("contact_cell_rate__")
    )


def _is_compact_shape(column: str) -> bool:
    return column.startswith(NEW_PREFIX) and (
        "__neutral_shape__" in column
        or column.endswith("__neutral_contact_events")
        or column.endswith("__neutral_contact_levels")
        or column.endswith("__available")
    )


def _variants(panel: pl.DataFrame) -> dict[str, pl.DataFrame]:
    old_contact = {column for column in panel.columns if _is_old_contact(column)}
    new_contact = {column for column in panel.columns if column.startswith(NEW_PREFIX)}
    compact_shape = {column for column in new_contact if _is_compact_shape(column)}
    if not old_contact or not compact_shape:
        raise ValueError("expected both original contact cells and compact shape features")

    def select(*, keep_old: bool, keep_shape: bool) -> pl.DataFrame:
        keep = compact_shape if keep_shape else set()
        selected = panel.select(
            column
            for column in panel.columns
            if (
                keep_old
                or column not in old_contact
                or column == "lag0__contact_events"
            )
            and (column not in new_contact or column in keep)
        )
        if not keep_old:
            # The shared architecture runner exposes this field as output metadata.
            # Retain it as a constant so it conveys no contact information to models.
            selected = selected.with_columns(
                pl.lit(0, dtype=pl.UInt32).alias("lag0__contact_events")
            )
        return selected

    return {
        "stats_only": select(keep_old=False, keep_shape=False),
        "shape_replacement": select(keep_old=False, keep_shape=True),
        "current_plus_shape": select(keep_old=True, keep_shape=True),
    }


def _stage_columns(panel: pl.DataFrame) -> pl.DataFrame:
    contact_available = (
        pl.col("lag0__contact_feature_available")
        if "lag0__contact_feature_available" in panel.columns
        else pl.lit(0, dtype=pl.Int8)
    )
    return panel.select(
        "origin_year",
        "player_id",
        pl.col("lag0__highest_level").alias("current_highest_level"),
        pl.col("lag0__pa_level__MLB").alias("current_mlb_pa"),
        contact_available.alias("current_contact_feature_available"),
    )


def _add_stage(predictions: pl.DataFrame, panel: pl.DataFrame) -> pl.DataFrame:
    return predictions.join(
        _stage_columns(panel), on=["origin_year", "player_id"], how="left"
    ).with_columns(
        pl.when(pl.col("current_mlb_pa") > 0)
        .then(pl.lit("current_mlb"))
        .when(pl.col("current_highest_level").is_in(["AA", "AAA"]))
        .then(pl.lit("upper_minors"))
        .otherwise(pl.lit("lower_minors"))
        .alias("player_stage")
    )


def _baseline(path: Path, panel: pl.DataFrame) -> pl.DataFrame:
    baseline = pl.read_parquet(path).select(
        *KEY,
        "actual_active",
        "actual_component_war",
        pl.col("prediction_candidate_equal_mean").alias("ensemble_prediction"),
        pl.col("prediction_candidate_mlb_active_probability").alias(
            "ensemble_active_probability"
        ),
    )
    return _add_stage(baseline, panel)


def _run_variant(panel: pl.DataFrame) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    outputs: list[pl.DataFrame] = []
    fold_records: list[dict[str, object]] = []
    for fold in folds:
        print(f"  origin {fold.test_origin}: LightGBM architectures", flush=True)
        architecture, architecture_metrics, _ = run_lightgbm_architecture_fold(
            panel, fold, random_state=417
        )
        members = [
            architecture["prediction_direct"].to_numpy(),
            architecture["prediction_three_part"].to_numpy(),
        ]
        active_probabilities = [architecture["active_probability"].to_numpy()]
        engine_metrics = {}
        for engine in ENGINES:
            print(f"  origin {fold.test_origin}: {engine}", flush=True)
            result, metrics = run_engine_fold(
                panel, fold, engine, random_state=417, variant="balanced"
            )
            members.append(result["predicted_component_war"].to_numpy())
            active_probabilities.append(result["active_probability"].to_numpy())
            engine_metrics[engine] = metrics
        outputs.append(
            architecture.select(
                *KEY, "actual_active", "actual_component_war"
            ).with_columns(
                pl.Series("ensemble_prediction", np.mean(members, axis=0)),
                pl.Series(
                    "ensemble_active_probability",
                    np.mean(active_probabilities, axis=0),
                ),
            )
        )
        fold_records.append(
            {
                "test_origin": fold.test_origin,
                "architecture_metrics": architecture_metrics,
                "engine_metrics": engine_metrics,
            }
        )
    return _add_stage(pl.concat(outputs), panel), fold_records


def _metrics(predictions: pl.DataFrame) -> dict[str, object]:
    actual = predictions["actual_component_war"].to_numpy()
    predicted = predictions["ensemble_prediction"].to_numpy()
    result: dict[str, object] = {
        "rows": predictions.height,
        "players": predictions["player_id"].n_unique(),
        "total_value": regression_metrics(actual, predicted),
        "active_probability": classification_metrics(
            predictions["actual_active"].to_numpy(),
            predictions["ensemble_active_probability"].to_numpy(),
        ),
        "folds": {},
        "subgroups": {},
    }
    for origin in predictions["origin_year"].unique().sort().to_list():
        subset = predictions.filter(pl.col("origin_year") == origin)
        result["folds"][str(origin)] = regression_metrics(
            subset["actual_component_war"].to_numpy(),
            subset["ensemble_prediction"].to_numpy(),
        )
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        subset = predictions.filter(pl.col("player_stage") == stage)
        result["subgroups"][stage] = {
            "rows": subset.height,
            **regression_metrics(
                subset["actual_component_war"].to_numpy(),
                subset["ensemble_prediction"].to_numpy(),
            ),
        }
    return result


def _align(challenger: pl.DataFrame, reference: pl.DataFrame) -> pl.DataFrame:
    joined = challenger.select(
        *KEY,
        "actual_component_war",
        "actual_active",
        "ensemble_prediction",
        "ensemble_active_probability",
    ).join(
        reference.select(
            *KEY,
            pl.col("actual_component_war").alias("reference_actual"),
            pl.col("ensemble_prediction").alias("reference_prediction"),
            pl.col("ensemble_active_probability").alias(
                "reference_active_probability"
            ),
        ),
        on=KEY,
        how="inner",
    )
    if joined.height != challenger.height or not np.allclose(
        joined["actual_component_war"].to_numpy(),
        joined["reference_actual"].to_numpy(),
    ):
        raise ValueError("challenger and reference predictions do not align")
    return joined


def main() -> int:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(exist_ok=True)
    panel = pl.read_parquet(args.panel)
    variants = _variants(panel)
    if args.variants:
        requested = {item.strip() for item in args.variants.split(",") if item.strip()}
        if unknown := requested - set(variants):
            raise ValueError(f"unknown variants: {sorted(unknown)}")
        variants = {name: frame for name, frame in variants.items() if name in requested}

    baseline = _baseline(args.baseline, panel)
    predictions = {"current_detailed_contact": baseline}
    report: dict[str, object] = {
        "schema_version": "1.0",
        "status": "evaluation_in_progress",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "question": (
            "Do the current 90 contact-result cells improve the fixed five-model "
            "hitter ensemble versus ordinary stats or a compact contact-shape block?"
        ),
        "variants": {
            "current_detailed_contact": {
                "feature_count": len(
                    feature_columns(panel.drop([c for c in panel.columns if c.startswith(NEW_PREFIX)]))
                ),
                "metrics": _metrics(baseline),
                "source": str(args.baseline),
            }
        },
    }
    report_path = args.output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for name, variant in variants.items():
        artifact_path = table_root / f"{name}-predictions.parquet"
        print(f"{name}: {len(feature_columns(variant))} features", flush=True)
        if args.reuse_existing and artifact_path.exists():
            combined = pl.read_parquet(artifact_path)
            fold_details: list[dict[str, object]] = []
        else:
            combined, fold_details = _run_variant(variant)
            write_canonical_parquet(
                combined,
                artifact_path,
                table_name=f"hitter_contact_block_ensemble_v2_{name}",
            )
        predictions[name] = combined
        report["variants"][name] = {
            "feature_count": len(feature_columns(variant)),
            "metrics": _metrics(combined),
            "fold_fit_details": fold_details,
            "artifact": str(artifact_path),
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    comparisons = {}
    baseline_classification = report["variants"]["current_detailed_contact"][
        "metrics"
    ]["active_probability"]
    for name, challenger in predictions.items():
        if name == "current_detailed_contact":
            continue
        aligned = _align(challenger, baseline)
        comparison = paired_cluster_rmse_delta(
            aligned["actual_component_war"].to_numpy(),
            aligned["ensemble_prediction"].to_numpy(),
            aligned["reference_prediction"].to_numpy(),
            aligned["player_id"].to_numpy(),
        )
        challenger_classification = report["variants"][name]["metrics"][
            "active_probability"
        ]
        comparison["brier_delta"] = (
            challenger_classification["brier"] - baseline_classification["brier"]
        )
        comparison["log_loss_delta"] = (
            challenger_classification["log_loss"]
            - baseline_classification["log_loss"]
        )
        comparisons[f"{name}_minus_current_detailed_contact"] = comparison
    report["comparisons"] = comparisons
    report["status"] = "chronological_evaluation_complete"
    report["generated_at_utc"] = datetime.now(UTC).isoformat()
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                name: details["metrics"]["total_value"]["rmse"]
                for name, details in report["variants"].items()
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
