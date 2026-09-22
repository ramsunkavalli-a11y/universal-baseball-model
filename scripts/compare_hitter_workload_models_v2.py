#!/usr/bin/env python3
"""Compare next-season MLB plate-appearance models on hitter value folds."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.hitter_workload import run_workload_fold
from universal_baseball.storage import write_canonical_parquet


PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-workload-model-v2")
ENGINES = ("lightgbm", "xgboost", "ebm", "ridge")
KEY = ["origin_year", "target_season", "player_id"]


def main() -> None:
    panel = pl.read_parquet(PANEL_PATH)
    folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    engine_predictions: dict[str, pl.DataFrame] = {}
    engine_reports: dict[str, object] = {}
    for engine in ENGINES:
        frames: list[pl.DataFrame] = []
        reports: list[dict[str, object]] = []
        for fold in folds:
            print(f"fitting workload {engine} origin {fold.test_origin}", flush=True)
            result, metrics = run_workload_fold(
                panel,
                fold,
                engine,
                include_direct=engine == "lightgbm",
            )
            frames.append(result)
            reports.append({"test_origin": fold.test_origin, "metrics": metrics})
        engine_predictions[engine] = pl.concat(frames).sort(KEY)
        engine_reports[engine] = {"folds": reports}

    reference = engine_predictions["lightgbm"]
    actual = reference["actual_pa"].to_numpy()
    members = {
        "direct_lightgbm": reference["predicted_direct_pa"].to_numpy(),
        **{
            f"hurdle_{engine}": frame["predicted_hurdle_pa"].to_numpy()
            for engine, frame in engine_predictions.items()
        },
    }
    candidate = np.mean(np.column_stack(list(members.values())), axis=1)
    current_pa = (
        panel.select(
            "origin_year",
            "player_id",
            pl.col("lag0__pa_level__MLB").alias("current_mlb_pa"),
            pl.col("lag0__highest_level").alias("current_highest_level"),
        )
        .join(reference.select(KEY), on=["origin_year", "player_id"], how="inner")
        .sort(KEY)
    )
    carry_forward = current_pa["current_mlb_pa"].to_numpy()
    member_metrics = {
        name: regression_metrics(actual, prediction)
        for name, prediction in members.items()
    }
    leave_one_out = {
        f"without_{omitted}": regression_metrics(
            actual,
            np.mean(
                np.column_stack(
                    [value for name, value in members.items() if name != omitted]
                ),
                axis=1,
            ),
        )
        for omitted in members
    }
    comparisons = {
        "candidate_minus_best_member": paired_cluster_rmse_delta(
            actual,
            candidate,
            members[min(member_metrics, key=lambda name: member_metrics[name]["rmse"])],
            reference["player_id"].to_numpy(),
        ),
        "candidate_minus_carry_forward": paired_cluster_rmse_delta(
            actual,
            candidate,
            carry_forward,
            reference["player_id"].to_numpy(),
        ),
    }
    origin_values = reference["origin_year"].to_numpy()
    folds_report = {}
    for origin in sorted(reference["origin_year"].unique().to_list()):
        mask = origin_values == origin
        folds_report[str(origin)] = {
            "candidate": regression_metrics(actual[mask], candidate[mask]),
            "carry_forward": regression_metrics(
                actual[mask], carry_forward[mask]
            ),
            **{
                name: regression_metrics(actual[mask], prediction[mask])
                for name, prediction in members.items()
            },
        }

    output = reference.select(KEY + ["actual_active", "actual_pa"]).with_columns(
        pl.Series("prediction_candidate_expected_pa", candidate),
        pl.Series("prediction_carry_forward_pa", carry_forward),
        *[
            pl.Series(f"prediction_member__{name}", prediction)
            for name, prediction in members.items()
        ],
        pl.Series(
            "prediction_candidate_active_probability",
            np.mean(
                np.column_stack(
                    [frame["active_probability"].to_numpy() for frame in engine_predictions.values()]
                ),
                axis=1,
            ),
        ),
        current_pa["current_highest_level"],
        current_pa["current_mlb_pa"],
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        output,
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_workload_v2_chronological_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_workload_models_compared",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season zero-inclusive MLB plate appearances",
        "population_rows": reference.height,
        "candidate": {
            "members": list(members),
            "metrics": regression_metrics(actual, candidate),
        },
        "baselines": {
            "carry_forward_current_mlb_pa": regression_metrics(
                actual, carry_forward
            ),
            "always_zero": regression_metrics(actual, np.zeros_like(actual)),
        },
        "member_metrics": member_metrics,
        "leave_one_member_out": leave_one_out,
        "paired_player_cluster_comparisons": comparisons,
        "fold_metrics": folds_report,
        "engine_fold_reports": engine_reports,
        "artifact": artifact.as_record(),
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
