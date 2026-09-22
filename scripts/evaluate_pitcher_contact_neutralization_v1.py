#!/usr/bin/env python3
"""Test whether context-neutral pitcher contact value improves future MLB value."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import polars as pl

from evaluate_pitcher_contact_value_block_v2 import _load_cached_mlb_contact
from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_contact_neutralization import (
    attach_pitcher_contact_value_lags,
)
from universal_baseball.pitcher_contact_value import build_full_mlb_pitcher_value_targets
from universal_baseball.pitcher_model_tournament import run_pitcher_engine_fold
from universal_baseball.pitcher_value_panel import MODEL_ORIGINS, build_pitcher_value_panel
from universal_baseball.storage import write_canonical_parquet


STAGES = ("physical", "park", "park_defense", "park_defense_batter")


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
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-contact-neutralization-evaluation-v1"),
    )
    parser.add_argument("--engines", default="ridge,lightgbm")
    return parser.parse_args()


def _score(panel: pl.DataFrame, engine: str) -> pl.DataFrame:
    folds = expanding_year_folds(
        panel["origin_year"].unique().to_list(), minimum_train_years=8
    )
    return pl.concat(
        [run_pitcher_engine_fold(panel, fold, engine)[0] for fold in folds]
    ).sort("origin_year", "player_id")


def _metric(frame: pl.DataFrame, column: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_component_war"].to_numpy(), frame[column].to_numpy()
    )


def main() -> int:
    args = _args()
    stat_features = pl.read_parquet(
        args.base_panel_root / "tables/pitcher-stat-features.parquet"
    )
    cached, capture_paths = _load_cached_mlb_contact(
        args.generated_root / "career-mlb-outcome-inventory-2009-2025/raw"
    )
    targets = build_full_mlb_pitcher_value_targets(cached)
    base_panel = build_pitcher_value_panel(stat_features, targets, origins=MODEL_ORIGINS)
    panels = {"base": base_panel}
    for stage in STAGES:
        annual = pl.read_parquet(
            args.contact_root / f"tables/{stage}-player-season.parquet"
        ).select(
            "season",
            "player_id",
            "contact_events",
            "contact_levels",
            "contact_value_residual_rate",
        )
        panels[stage] = attach_pitcher_contact_value_lags(
            base_panel, annual, prefix=f"pitcher_contact_{stage}"
        )

    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    engines = [value.strip() for value in args.engines.split(",") if value.strip()]
    report: dict[str, Any] = {
        "schema_version": "0.1",
        "status": "pitcher_contact_neutralization_evaluated",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season zero-inclusive full hit-type MLB pitcher result value",
        "stages": list(STAGES),
        "cached_mlb_capture_count": len(capture_paths),
        "engines": {},
    }
    for engine in engines:
        print(f"starting context-neutral contact engine {engine}", flush=True)
        scored = {name: _score(panel, engine) for name, panel in panels.items()}
        base = scored["base"]
        keys = ["origin_year", "target_season", "player_id"]
        comparison = base.select(
            *keys,
            "actual_component_war",
            pl.col("active_probability").alias("base_active_probability"),
            pl.col("predicted_conditional_war").alias("base_conditional_war"),
            pl.col("predicted_component_war").alias("prediction_base"),
        )
        for stage in STAGES:
            comparison = comparison.join(
                scored[stage].select(
                    *keys,
                    pl.col("active_probability").alias(f"{stage}_active_probability"),
                    pl.col("predicted_conditional_war").alias(
                        f"{stage}_conditional_war"
                    ),
                    pl.col("predicted_component_war").alias(
                        f"prediction_{stage}_both"
                    ),
                ),
                on=keys,
                validate="1:1",
            ).with_columns(
                (
                    pl.col("base_active_probability")
                    * pl.col(f"{stage}_conditional_war")
                ).alias(f"prediction_{stage}_conditional_only")
            )
        actual = comparison["actual_component_war"].to_numpy()
        ids = comparison["player_id"].to_numpy()
        variants = {"base": "prediction_base"}
        for stage in STAGES:
            variants[f"{stage}_both"] = f"prediction_{stage}_both"
            variants[f"{stage}_conditional_only"] = (
                f"prediction_{stage}_conditional_only"
            )
        report["engines"][engine] = {
            "pooled": {name: _metric(comparison, column) for name, column in variants.items()},
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
                        f"{name}_rmse": _metric(fold, column)["rmse"]
                        for name, column in variants.items()
                    },
                }
                for key, fold in comparison.partition_by("origin_year", as_dict=True).items()
            ],
        }
        write_canonical_parquet(
            comparison,
            table_root / f"{engine}-predictions.parquet",
            table_name=f"pitcher_contact_neutralization_v1_{engine}_predictions",
        )
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["engines"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
