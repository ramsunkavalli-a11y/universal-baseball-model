#!/usr/bin/env python3
"""Add a separately modeled contact-value correction to the leading pitcher forecast."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from evaluate_pitcher_contact_value_block_v2 import _load_cached_mlb_contact
from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    feature_columns,
    matrix_from_panel,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_contact_neutralization import (
    attach_pitcher_contact_value_lags,
)
from universal_baseball.pitcher_contact_value import build_full_mlb_pitcher_value_targets
from universal_baseball.pitcher_model_tournament import to_generic_two_part_panel
from universal_baseball.pitcher_role_features import add_pitcher_role_features
from universal_baseball.pitcher_value_panel import MODEL_ORIGINS, build_pitcher_value_panel
from universal_baseball.storage import write_canonical_parquet


STAGE = "park_defense"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument(
        "--base-panel-root",
        type=Path,
        default=Path("reports/generated/pitcher-value-panel-v2"),
    )
    parser.add_argument(
        "--contact-root",
        type=Path,
        default=Path("reports/generated/pitcher-contact-neutralization-v1"),
    )
    parser.add_argument(
        "--role-predictions",
        type=Path,
        default=Path("reports/generated/pitcher-role-ensemble-v2/predictions.parquet"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-contact-reconciliation-v1"),
    )
    parser.add_argument("--engines", default="ridge,lightgbm")
    return parser.parse_args()


def _predict_delta(
    panel: pl.DataFrame, columns: list[str], engine: str
) -> pl.DataFrame:
    matrix = matrix_from_panel(panel, columns)
    target = panel["target_contact_value_delta"].to_numpy()
    predictions = []
    folds = expanding_year_folds(
        panel["origin_year"].unique().to_list(), minimum_train_years=8
    )
    for fold in folds:
        train = panel["origin_year"].is_in(fold.train_origins).to_numpy()
        test = (panel["origin_year"] == fold.test_origin).to_numpy()
        model = make_engine_models(engine, random_state=1_417 + fold.test_origin).regressor
        model.fit(matrix[train], target[train])
        prediction = np.asarray(model.predict(matrix[test]), dtype=np.float64)
        predictions.append(
            panel.filter(pl.Series(test))
            .select("origin_year", "target_season", "player_id")
            .with_columns(pl.Series("predicted_contact_value_delta", prediction))
        )
    return pl.concat(predictions).sort("origin_year", "player_id")


def _metrics(frame: pl.DataFrame, column: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_full_component_war"].to_numpy(), frame[column].to_numpy()
    )


def main() -> int:
    args = _args()
    stat_features = pl.read_parquet(
        args.base_panel_root / "tables/pitcher-stat-features.parquet"
    )
    clean_targets = pl.read_parquet(
        args.base_panel_root / "tables/pitcher-value-targets.parquet"
    )
    clean_panel = build_pitcher_value_panel(
        stat_features, clean_targets, origins=MODEL_ORIGINS
    )
    cached, capture_paths = _load_cached_mlb_contact(
        args.generated_root / "career-mlb-outcome-inventory-2009-2025/raw"
    )
    full_targets = build_full_mlb_pitcher_value_targets(cached)
    full_panel = build_pitcher_value_panel(
        stat_features, full_targets, origins=MODEL_ORIGINS
    )
    panel = add_pitcher_role_features(clean_panel).join(
        full_panel.select(
            "origin_year",
            "player_id",
            pl.col("target_component_war").alias("target_full_component_war"),
        ),
        on=["origin_year", "player_id"],
        validate="1:1",
    ).with_columns(
        (
            pl.col("target_full_component_war") - pl.col("target_component_war")
        ).alias("target_contact_value_delta")
    )
    base_columns = feature_columns(
        to_generic_two_part_panel(
            panel.drop("target_full_component_war", "target_contact_value_delta")
        )
    )
    annual = pl.read_parquet(
        args.contact_root / f"tables/{STAGE}-player-season.parquet"
    ).select(
        "season",
        "player_id",
        "contact_events",
        "contact_levels",
        "contact_value_residual_rate",
    )
    contact_panel = attach_pitcher_contact_value_lags(
        panel, annual, prefix=f"pitcher_contact_{STAGE}"
    )
    contact_columns = base_columns + [
        column
        for column in contact_panel.columns
        if column.startswith(f"pitcher_contact_{STAGE}")
    ]
    role = pl.read_parquet(args.role_predictions).select(
        "origin_year",
        "player_id",
        pl.col("prediction_role_chronology_pruned_equal").alias(
            "prediction_clean_role_ensemble"
        ),
    )
    scored_base = panel.select(
        "origin_year",
        "target_season",
        "player_id",
        pl.col("target_full_component_war").alias("actual_full_component_war"),
        "target_contact_value_delta",
    ).join(role, on=["origin_year", "player_id"], how="inner", validate="1:1")

    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    report: dict[str, Any] = {
        "schema_version": "0.1",
        "status": "pitcher_contact_reconciliation_evaluated",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "contact_stage": STAGE,
        "architecture": (
            "leading defense-independent role ensemble plus a separately fitted "
            "next-season full-contact-value correction"
        ),
        "cached_mlb_capture_count": len(capture_paths),
        "engines": {},
    }
    for engine in [value.strip() for value in args.engines.split(",") if value.strip()]:
        print(f"starting reconciled contact engine {engine}", flush=True)
        base_delta = _predict_delta(panel, base_columns, engine).rename(
            {"predicted_contact_value_delta": "predicted_delta_base"}
        )
        contact_delta = _predict_delta(contact_panel, contact_columns, engine).rename(
            {"predicted_contact_value_delta": "predicted_delta_contact"}
        )
        comparison = (
            scored_base.join(
                base_delta,
                on=["origin_year", "target_season", "player_id"],
                validate="1:1",
            )
            .join(
                contact_delta,
                on=["origin_year", "target_season", "player_id"],
                validate="1:1",
            )
            .with_columns(
                (
                    pl.col("prediction_clean_role_ensemble")
                    + pl.col("predicted_delta_base")
                ).alias("prediction_reconciled_base"),
                (
                    pl.col("prediction_clean_role_ensemble")
                    + pl.col("predicted_delta_contact")
                ).alias("prediction_reconciled_contact"),
            )
        )
        actual = comparison["actual_full_component_war"].to_numpy()
        ids = comparison["player_id"].to_numpy()
        methods = {
            "clean_role_ensemble": "prediction_clean_role_ensemble",
            "reconciled_base": "prediction_reconciled_base",
            "reconciled_contact": "prediction_reconciled_contact",
        }
        report["engines"][engine] = {
            "pooled": {name: _metrics(comparison, column) for name, column in methods.items()},
            "comparisons": {
                "reconciled_contact_minus_clean": paired_cluster_rmse_delta(
                    actual,
                    comparison["prediction_reconciled_contact"].to_numpy(),
                    comparison["prediction_clean_role_ensemble"].to_numpy(),
                    ids,
                    bootstrap_samples=5_000,
                ),
                "reconciled_contact_minus_base_reconciliation": (
                    paired_cluster_rmse_delta(
                        actual,
                        comparison["prediction_reconciled_contact"].to_numpy(),
                        comparison["prediction_reconciled_base"].to_numpy(),
                        ids,
                        bootstrap_samples=5_000,
                    )
                ),
            },
            "contact_delta": {
                "base": regression_metrics(
                    comparison["target_contact_value_delta"].to_numpy(),
                    comparison["predicted_delta_base"].to_numpy(),
                ),
                "with_neutralized_contact": regression_metrics(
                    comparison["target_contact_value_delta"].to_numpy(),
                    comparison["predicted_delta_contact"].to_numpy(),
                ),
            },
            "folds": [
                {
                    "origin_year": int(key[0]),
                    **{
                        f"{name}_rmse": _metrics(fold, column)["rmse"]
                        for name, column in methods.items()
                    },
                }
                for key, fold in comparison.partition_by("origin_year", as_dict=True).items()
            ],
        }
        write_canonical_parquet(
            comparison,
            table_root / f"{engine}-predictions.parquet",
            table_name=f"pitcher_contact_reconciliation_v1_{engine}_predictions",
        )
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["engines"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
