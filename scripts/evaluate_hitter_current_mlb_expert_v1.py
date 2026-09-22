#!/usr/bin/env python3
"""Test a dedicated five-model expert for hitters already in MLB."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_model_tournament import run_engine_fold
from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
    run_lightgbm_architecture_fold,
)
from universal_baseball.storage import write_canonical_parquet


KEY = ["origin_year", "target_season", "player_id"]
ROOT = Path("reports/generated/hitter-current-mlb-expert-v1")
PANEL_PATH = Path(
    "reports/generated/hitter-contact-neutralization-v2/tables/modeling-panel.parquet"
)
BASELINE_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
ENGINES = ("xgboost", "ebm", "ridge")


def _base_panel() -> pl.DataFrame:
    panel = pl.read_parquet(PANEL_PATH)
    added = [column for column in panel.columns if column.startswith("contact_neutral_lag")]
    return panel.drop(added)


def _expert_predictions(panel: pl.DataFrame) -> pl.DataFrame:
    incumbents = panel.filter(pl.col("lag0__pa_level__MLB") > 0)
    folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    outputs = []
    for fold in folds:
        print(f"origin {fold.test_origin}: LightGBM architectures", flush=True)
        architecture, _, _ = run_lightgbm_architecture_fold(
            incumbents, fold, random_state=417
        )
        members = [
            architecture["prediction_direct"].to_numpy(),
            architecture["prediction_three_part"].to_numpy(),
        ]
        for engine in ENGINES:
            print(f"origin {fold.test_origin}: {engine}", flush=True)
            result, _ = run_engine_fold(
                incumbents, fold, engine, random_state=417, variant="balanced"
            )
            members.append(result["predicted_component_war"].to_numpy())
        outputs.append(
            architecture.select(
                *KEY, "actual_active", "actual_component_war"
            ).with_columns(
                pl.Series("expert_prediction", np.mean(members, axis=0))
            )
        )
    return pl.concat(outputs).sort(KEY)


def _metrics(frame: pl.DataFrame, prediction: str) -> dict:
    result = {
        "rows": frame.height,
        "players": frame["player_id"].n_unique(),
        "pooled": regression_metrics(
            frame["actual_component_war"].to_numpy(), frame[prediction].to_numpy()
        ),
        "folds": {},
    }
    for origin in frame["origin_year"].unique().sort().to_list():
        subset = frame.filter(pl.col("origin_year") == origin)
        result["folds"][str(origin)] = regression_metrics(
            subset["actual_component_war"].to_numpy(), subset[prediction].to_numpy()
        )
    return result


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "tables").mkdir(exist_ok=True)
    panel = _base_panel()
    expert = _expert_predictions(panel)
    baseline = pl.read_parquet(BASELINE_PATH).sort(KEY)
    incumbent_comparison = baseline.filter(
        pl.col("player_stage") == "current_mlb"
    ).select(
        *KEY,
        "actual_component_war",
        pl.col("prediction_candidate_equal_mean").alias("baseline_prediction"),
    ).join(expert.select(*KEY, "expert_prediction"), on=KEY, how="inner")
    expected_incumbents = baseline.filter(pl.col("player_stage") == "current_mlb").height
    if incumbent_comparison.height != expected_incumbents:
        raise ValueError("expert predictions do not cover the full incumbent test set")

    routed = baseline.select(
        *KEY,
        "actual_component_war",
        "player_stage",
        pl.col("prediction_candidate_equal_mean").alias("baseline_prediction"),
    ).join(
        expert.select(*KEY, "expert_prediction"),
        on=KEY,
        how="left",
    ).with_columns(
        pl.when(pl.col("player_stage") == "current_mlb")
        .then(pl.col("expert_prediction"))
        .otherwise(pl.col("baseline_prediction"))
        .alias("routed_prediction")
    )

    incumbent_delta = paired_cluster_rmse_delta(
        incumbent_comparison["actual_component_war"].to_numpy(),
        incumbent_comparison["expert_prediction"].to_numpy(),
        incumbent_comparison["baseline_prediction"].to_numpy(),
        incumbent_comparison["player_id"].to_numpy(),
    )
    total_delta = paired_cluster_rmse_delta(
        routed["actual_component_war"].to_numpy(),
        routed["routed_prediction"].to_numpy(),
        routed["baseline_prediction"].to_numpy(),
        routed["player_id"].to_numpy(),
    )
    report = {
        "schema_version": "1.0",
        "status": "chronological_evaluation_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "design": (
            "Fit the established five-model detailed-contact ensemble only on "
            "player-seasons with prior MLB plate appearances; route that expert to "
            "current-MLB hitters and retain the established baseline for prospects."
        ),
        "incumbents": {
            "baseline": _metrics(incumbent_comparison, "baseline_prediction"),
            "expert": _metrics(incumbent_comparison, "expert_prediction"),
            "expert_minus_baseline": incumbent_delta,
        },
        "full_population": {
            "baseline": _metrics(routed, "baseline_prediction"),
            "routed": _metrics(routed, "routed_prediction"),
            "routed_minus_baseline": total_delta,
        },
    }
    artifact = write_canonical_parquet(
        routed,
        ROOT / "tables" / "routed-predictions.parquet",
        table_name="hitter_current_mlb_expert_v1_predictions",
    )
    report["artifact"] = artifact.as_record()
    (ROOT / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "incumbent_baseline_rmse": report["incumbents"]["baseline"]["pooled"]["rmse"],
                "incumbent_expert_rmse": report["incumbents"]["expert"]["pooled"]["rmse"],
                "full_baseline_rmse": report["full_population"]["baseline"]["pooled"]["rmse"],
                "full_routed_rmse": report["full_population"]["routed"]["pooled"]["rmse"],
                "incumbent_comparison": incumbent_delta,
                "full_comparison": total_delta,
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
