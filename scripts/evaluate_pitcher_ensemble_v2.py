#!/usr/bin/env python3
"""Evaluate equal and chronology-pruned pitcher model ensembles."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.projection_ensemble import (
    chronological_greedy_equal_ensemble,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tournament-root",
        type=Path,
        default=Path("reports/generated/pitcher-model-engine-tournament-v2"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-model-ensemble-v2"),
    )
    parser.add_argument("--minimum-rmse-gain", type=float, default=0.00025)
    return parser.parse_args()


def _load_predictions(root: Path) -> tuple[pl.DataFrame, list[str]]:
    paths = sorted((root / "tables").glob("*-predictions.parquet"))
    if not paths:
        raise FileNotFoundError("no completed engine predictions found")
    combined: pl.DataFrame | None = None
    prediction_columns: list[str] = []
    for path in paths:
        engine = path.name.removesuffix("-predictions.parquet")
        column = f"prediction__{engine}"
        frame = pl.read_parquet(path).select(
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
    assert combined is not None
    return combined, prediction_columns


def main() -> int:
    args = _args()
    frame, prediction_columns = _load_predictions(args.tournament_root)
    all_equal = np.mean(
        [frame[column].to_numpy() for column in prediction_columns], axis=0
    )
    engines = [column.removeprefix("prediction__") for column in prediction_columns]
    all_probability = np.mean(
        [frame[f"probability__{engine}"].to_numpy() for engine in engines], axis=0
    )
    all_conditional = np.mean(
        [frame[f"conditional__{engine}"].to_numpy() for engine in engines], axis=0
    )
    frame = frame.with_columns(
        pl.Series("prediction_all_equal", all_equal),
        pl.Series("probability_all_equal", all_probability),
        pl.Series("conditional_all_equal", all_conditional),
    )
    chronology, selections = chronological_greedy_equal_ensemble(
        frame,
        prediction_columns,
        minimum_rmse_gain=args.minimum_rmse_gain,
    )
    frame = frame.join(
        chronology.select(
            "origin_year", "player_id", "prediction_chronology_pruned_equal"
        ),
        on=["origin_year", "player_id"],
        validate="1:1",
    )
    auxiliary = []
    for selection in selections:
        origin = int(selection["test_origin"])
        selected_engines = [
            column.removeprefix("prediction__")
            for column in selection["selected_members"]
        ]
        test = frame.filter(pl.col("origin_year") == origin)
        probability = np.mean(
            [test[f"probability__{engine}"].to_numpy() for engine in selected_engines],
            axis=0,
        )
        conditional = np.mean(
            [test[f"conditional__{engine}"].to_numpy() for engine in selected_engines],
            axis=0,
        )
        auxiliary.append(
            test.select("origin_year", "player_id").with_columns(
                pl.Series("probability_chronology_pruned_equal", probability),
                pl.Series("conditional_chronology_pruned_equal", conditional),
            )
        )
    frame = frame.join(
        pl.concat(auxiliary),
        on=["origin_year", "player_id"],
        validate="1:1",
    )
    actual = frame["actual_component_war"].to_numpy()
    metrics = {
        column.removeprefix("prediction__"): regression_metrics(
            actual, frame[column].to_numpy()
        )
        for column in prediction_columns
    }
    metrics["all_equal"] = regression_metrics(
        actual, frame["prediction_all_equal"].to_numpy()
    )
    metrics["chronology_pruned_equal"] = regression_metrics(
        actual, frame["prediction_chronology_pruned_equal"].to_numpy()
    )
    active = frame["actual_active"].to_numpy()
    active_rows = active == 1
    ensemble_component_metrics = {
        "all_equal": {
            "arrival": classification_metrics(
                active, frame["probability_all_equal"].to_numpy()
            ),
            "conditional_value_active_pitchers": regression_metrics(
                actual[active_rows],
                frame["conditional_all_equal"].to_numpy()[active_rows],
            ),
        },
        "chronology_pruned_equal": {
            "arrival": classification_metrics(
                active, frame["probability_chronology_pruned_equal"].to_numpy()
            ),
            "conditional_value_active_pitchers": regression_metrics(
                actual[active_rows],
                frame["conditional_chronology_pruned_equal"].to_numpy()[active_rows],
            ),
        },
    }
    best_single = min(
        prediction_columns,
        key=lambda column: metrics[column.removeprefix("prediction__")]["rmse"],
    )
    comparisons = {
        "all_equal_minus_best_single": paired_cluster_rmse_delta(
            actual,
            frame["prediction_all_equal"].to_numpy(),
            frame[best_single].to_numpy(),
            frame["player_id"].to_numpy(),
            bootstrap_samples=5_000,
        ),
        "chronology_pruned_minus_all_equal": paired_cluster_rmse_delta(
            actual,
            frame["prediction_chronology_pruned_equal"].to_numpy(),
            frame["prediction_all_equal"].to_numpy(),
            frame["player_id"].to_numpy(),
            bootstrap_samples=5_000,
        ),
    }
    leave_one_out = {}
    for omitted in prediction_columns:
        retained = [column for column in prediction_columns if column != omitted]
        if not retained:
            continue
        prediction = np.mean([frame[column].to_numpy() for column in retained], axis=0)
        leave_one_out[omitted.removeprefix("prediction__")] = regression_metrics(
            actual, prediction
        )["rmse"]

    args.output_root.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        args.output_root / "predictions.parquet",
        table_name="pitcher_model_ensemble_v2_predictions",
    ).as_record()
    report = {
        "schema_version": "0.1",
        "status": "development_ensemble_evaluated",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "members": [column.removeprefix("prediction__") for column in prediction_columns],
        "minimum_prior_rmse_gain_to_drop_member": args.minimum_rmse_gain,
        "best_pooled_single": best_single.removeprefix("prediction__"),
        "metrics": metrics,
        "ensemble_component_metrics": ensemble_component_metrics,
        "comparisons": comparisons,
        "chronological_selections": selections,
        "all_equal_leave_one_out_rmse": leave_one_out,
        "artifact": artifact,
        "selection_warning": (
            "best pooled single and leave-one-out results are development descriptions; "
            "only the chronology-pruned rule chooses members without the scored fold"
        ),
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
