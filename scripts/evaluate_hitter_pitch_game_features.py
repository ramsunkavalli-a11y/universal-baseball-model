#!/usr/bin/env python3
"""Chronologically ablate universal pitch-sequence and game-feed hitter features."""

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


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel",
        type=Path,
        default=Path(
            "reports/generated/hitter-pitch-game-features-v1/tables/modeling-panel.parquet"
        ),
    )
    parser.add_argument(
        "--feature-report",
        type=Path,
        default=Path("reports/generated/hitter-pitch-game-features-v1/report.json"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-pitch-game-ablation-v1"),
    )
    parser.add_argument("--engines", default="lightgbm")
    parser.add_argument(
        "--variants",
        default="",
        help="optional comma-separated subset of ablation variants",
    )
    parser.add_argument("--reuse-existing", action="store_true")
    return parser.parse_args()


def _pooled_metrics(predictions: pl.DataFrame) -> dict[str, object]:
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


def _panel_variants(
    panel: pl.DataFrame, feature_report: dict[str, object]
) -> dict[str, pl.DataFrame]:
    blocks = feature_report["feature_blocks"]
    pitch_columns = [column for column in panel.columns if column.startswith("pitch_lag")]
    sequence = set(blocks["sequence"])
    adjusted = set(blocks["opponent_and_umpire_adjusted"])
    environment = set(blocks["game_environment"])
    sequence_volume = {
        column
        for column in sequence
        if column.endswith("_count")
        or column in {"pitch_count", "pa_count", "game_count"}
        or column.startswith("split_pitches_")
    }
    sequence_rates = sequence - sequence_volume

    def suffix(column: str) -> str:
        return column.split("__", maxsplit=1)[1]

    def select(allowed: set[str]) -> pl.DataFrame:
        keep = [
            column
            for column in panel.columns
            if column not in pitch_columns
            or suffix(column) in allowed
            or suffix(column) == "available"
        ]
        return panel.select(keep)

    return {
        "base": panel.drop(pitch_columns),
        "base_plus_sequence": select(sequence),
        "base_plus_sequence_rates": select(sequence_rates),
        "base_plus_sequence_volume": select(sequence_volume),
        "base_plus_sequence_rates_adjusted": select(sequence_rates | adjusted),
        "base_plus_sequence_rates_environment": select(sequence_rates | environment),
        "base_plus_sequence_rates_adjusted_environment": select(
            sequence_rates | adjusted | environment
        ),
        "base_plus_adjusted": select(adjusted),
        "base_plus_sequence_adjusted": select(sequence | adjusted),
        "base_plus_environment": select(environment),
        "base_plus_sequence_environment": select(sequence | environment),
        "base_plus_adjusted_environment": select(adjusted | environment),
        "base_plus_all": panel,
    }


def _subgroup_metrics(predictions: pl.DataFrame) -> dict[str, object]:
    groups = {
        "all": pl.lit(True),
        "current_mlb": pl.col("current_highest_level") == "MLB",
        "current_minors": pl.col("current_highest_level") != "MLB",
        "current_pa_under_200": pl.col("current_pa") < 200,
        "current_pa_200_plus": pl.col("current_pa") >= 200,
        "minor_leaguer_reaches_mlb": (
            (pl.col("current_highest_level") != "MLB")
            & (pl.col("actual_active") == 1)
        ),
        "lag0_pitch_available": pl.col("lag0_pitch_available") == 1,
        "lag0_pitch_unavailable": pl.col("lag0_pitch_available") == 0,
    }
    return {
        name: _pooled_metrics(subset)
        for name, condition in groups.items()
        if not (subset := predictions.filter(condition)).is_empty()
    }


def main() -> int:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    tables = args.output_root / "tables"
    tables.mkdir(exist_ok=True)
    panel = pl.read_parquet(args.panel)
    feature_report = json.loads(args.feature_report.read_text(encoding="utf-8"))
    variants = _panel_variants(panel, feature_report)
    if args.variants:
        requested_variants = {
            value.strip() for value in args.variants.split(",") if value.strip()
        }
        unknown_variants = requested_variants - set(variants)
        if unknown_variants:
            raise ValueError(f"unknown ablation variants: {sorted(unknown_variants)}")
        variants = {
            name: frame for name, frame in variants.items() if name in requested_variants
        }
    if "base" not in variants:
        raise ValueError("ablation selection must include base for paired comparisons")
    folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    engines = [value.strip() for value in args.engines.split(",") if value.strip()]
    context = panel.select(
        "origin_year",
        "player_id",
        pl.col("lag0__highest_level").alias("current_highest_level"),
        pl.col("lag0__plate_appearances").alias("current_pa"),
        pl.col("pitch_lag0__available")
        .fill_null(0)
        .alias("lag0_pitch_available"),
    )
    report: dict[str, object] = {
        "schema_version": "1.0",
        "status": "evaluation_in_progress",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "fold_origins": [fold.test_origin for fold in folds],
        "variants": {
            name: {"feature_count": len(feature_columns(frame))}
            for name, frame in variants.items()
        },
        "engines": {},
    }
    report_path = args.output_root / "report.json"
    predictions_by_engine: dict[str, dict[str, pl.DataFrame]] = {}
    for engine in engines:
        predictions_by_engine[engine] = {}
        report["engines"][engine] = {}
        for variant, variant_panel in variants.items():
            print(f"{engine}: {variant}", flush=True)
            artifact_path = tables / f"{engine}-{variant}-predictions.parquet"
            if args.reuse_existing and artifact_path.exists():
                combined = pl.read_parquet(artifact_path)
                fold_metrics = [
                    {
                        "test_origin": origin,
                        "metrics": _pooled_metrics(
                            combined.filter(pl.col("origin_year") == origin)
                        ),
                    }
                    for origin in sorted(combined["origin_year"].unique().to_list())
                ]
            else:
                fold_predictions = []
                fold_metrics = []
                for fold in folds:
                    predictions, metrics = run_engine_fold(
                        variant_panel, fold, engine, random_state=417
                    )
                    fold_predictions.append(predictions)
                    fold_metrics.append(
                        {"test_origin": fold.test_origin, "metrics": metrics}
                    )
                combined = pl.concat(fold_predictions).join(
                    context,
                    on=["origin_year", "player_id"],
                    validate="m:1",
                )
            predictions_by_engine[engine][variant] = combined
            artifact = write_canonical_parquet(
                combined,
                artifact_path,
                table_name=f"hitter_pitch_game_ablation_{engine}_{variant}_v1",
            )
            report["engines"][engine][variant] = {
                "pooled_metrics": _pooled_metrics(combined),
                "fold_metrics": fold_metrics,
                "subgroup_metrics": _subgroup_metrics(combined),
                "artifact": artifact.as_record(),
            }
            report_path.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

        reference = predictions_by_engine[engine]["base"]
        comparisons = {}
        for variant, challenger in predictions_by_engine[engine].items():
            if variant == "base":
                continue
            comparison = paired_cluster_rmse_delta(
                challenger["actual_component_war"].to_numpy(),
                challenger["predicted_component_war"].to_numpy(),
                reference["predicted_component_war"].to_numpy(),
                challenger["player_id"].to_numpy(),
            )
            active = challenger["actual_active"].to_numpy()
            challenger_probability = challenger["active_probability"].to_numpy()
            reference_probability = reference["active_probability"].to_numpy()
            challenger_classification = classification_metrics(
                active, challenger_probability
            )
            reference_classification = classification_metrics(active, reference_probability)
            comparison.update(
                {
                    "brier_delta": (
                        challenger_classification["brier"]
                        - reference_classification["brier"]
                    ),
                    "log_loss_delta": (
                        challenger_classification["log_loss"]
                        - reference_classification["log_loss"]
                    ),
                }
            )
            comparisons[f"{variant}_minus_base"] = comparison
        report["engines"][engine]["comparisons"] = comparisons

    report["status"] = "chronological_ablation_complete"
    report["generated_at_utc"] = datetime.now(UTC).isoformat()
    report["decision_rule"] = (
        "Retain a block only when it improves pooled expected-WAR RMSE without a "
        "material arrival-probability reversal, then verify fold and player-stage stability."
    )
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = {
        engine: {
            variant: details["pooled_metrics"]["total_value"]["rmse"]
            for variant, details in engine_rows.items()
            if variant != "comparisons"
        }
        for engine, engine_rows in report["engines"].items()
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
