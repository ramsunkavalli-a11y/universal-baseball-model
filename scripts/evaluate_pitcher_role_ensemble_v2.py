#!/usr/bin/env python3
"""Test role-enhanced engines inside the chronology-pruned pitcher ensemble."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.projection_ensemble import chronological_greedy_equal_ensemble
from universal_baseball.storage import write_canonical_parquet


TOURNAMENT_ROOT = Path("reports/generated/pitcher-model-engine-tournament-v2/tables")
ROLE_ROOT = Path("reports/generated/pitcher-role-block-v2/tables")
OLD_ENSEMBLE_PATH = Path("reports/generated/pitcher-model-ensemble-v2/predictions.parquet")
OUTPUT_ROOT = Path("reports/generated/pitcher-role-ensemble-v2")
ROLE_ENGINES = {"ridge", "catboost", "lightgbm"}
MINIMUM_GAIN = 0.00025


def _load_updated() -> tuple[pl.DataFrame, list[str]]:
    combined: pl.DataFrame | None = None
    prediction_columns = []
    for path in sorted(TOURNAMENT_ROOT.glob("*-predictions.parquet")):
        engine = path.name.removesuffix("-predictions.parquet")
        base = pl.read_parquet(path)
        if engine in ROLE_ENGINES:
            role = pl.read_parquet(ROLE_ROOT / path.name)
            source = base.select(
                "origin_year", "player_id", "actual_active", "actual_component_war"
            ).join(
                role.select(
                    "origin_year",
                    "player_id",
                    pl.col("role_active_probability").alias("active_probability"),
                    pl.col("role_conditional_war").alias("predicted_conditional_war"),
                    pl.col("prediction_role").alias("predicted_component_war"),
                ),
                on=["origin_year", "player_id"],
                validate="1:1",
            )
        else:
            source = base
        column = f"prediction__{engine}"
        frame = source.select(
            "origin_year",
            "player_id",
            "actual_active",
            "actual_component_war",
            pl.col("active_probability").alias(f"probability__{engine}"),
            pl.col("predicted_conditional_war").alias(f"conditional__{engine}"),
            pl.col("predicted_component_war").alias(column),
        )
        prediction_columns.append(column)
        if combined is None:
            combined = frame
        else:
            combined = combined.join(
                frame.drop("actual_active", "actual_component_war"),
                on=["origin_year", "player_id"],
                validate="1:1",
            )
    if combined is None:
        raise FileNotFoundError("no pitcher tournament predictions")
    return combined, prediction_columns


def main() -> int:
    frame, columns = _load_updated()
    frame = frame.with_columns(
        pl.Series(
            "prediction_role_all_equal",
            np.mean([frame[column].to_numpy() for column in columns], axis=0),
        )
    )
    chronology, selections = chronological_greedy_equal_ensemble(
        frame, columns, minimum_rmse_gain=MINIMUM_GAIN
    )
    frame = (
        frame.join(
            chronology.select(
                "origin_year", "player_id", "prediction_chronology_pruned_equal"
            ).rename(
                {
                    "prediction_chronology_pruned_equal": (
                        "prediction_role_chronology_pruned_equal"
                    )
                }
            ),
            on=["origin_year", "player_id"],
            validate="1:1",
        )
        .join(
            pl.read_parquet(OLD_ENSEMBLE_PATH).select(
                "origin_year",
                "player_id",
                "prediction_all_equal",
                "prediction_chronology_pruned_equal",
            ),
            on=["origin_year", "player_id"],
            validate="1:1",
        )
        .sort("origin_year", "player_id")
    )
    actual = frame["actual_component_war"].to_numpy()
    ids = frame["player_id"].to_numpy()
    methods = {
        "old_all_equal": "prediction_all_equal",
        "old_chronology_pruned": "prediction_chronology_pruned_equal",
        "role_all_equal": "prediction_role_all_equal",
        "role_chronology_pruned": "prediction_role_chronology_pruned_equal",
    }
    report = {
        "schema_version": "0.1",
        "status": "pitcher_role_ensemble_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "role_enhanced_members": sorted(ROLE_ENGINES),
        "role_rule": (
            "derived role/workload features enter both arrival and conditional value "
            "for the three engines tested in the block"
        ),
        "metrics": {
            name: regression_metrics(actual, frame[column].to_numpy())
            for name, column in methods.items()
        },
        "comparisons": {
            "role_all_equal_minus_old_all_equal": paired_cluster_rmse_delta(
                actual,
                frame[methods["role_all_equal"]].to_numpy(),
                frame[methods["old_all_equal"]].to_numpy(),
                ids,
                bootstrap_samples=5_000,
            ),
            "role_pruned_minus_old_pruned": paired_cluster_rmse_delta(
                actual,
                frame[methods["role_chronology_pruned"]].to_numpy(),
                frame[methods["old_chronology_pruned"]].to_numpy(),
                ids,
                bootstrap_samples=5_000,
            ),
        },
        "chronological_selections": selections,
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    report["artifact"] = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "predictions.parquet",
        table_name="pitcher_role_ensemble_v2_predictions",
    ).as_record()
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
