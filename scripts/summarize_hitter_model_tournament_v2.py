#!/usr/bin/env python3
"""Consolidate saved hitter engine predictions and test simple ensembles."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl
from scipy.optimize import nnls

from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import write_canonical_parquet


KEY = ["origin_year", "target_season", "player_id"]


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("reports/generated/hitter-model-engine-tournament-v2"),
    )
    return parser.parse_args()


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_component_war"].to_numpy(), frame[prediction].to_numpy()
    )


def _sequential_nnls_stack(
    wide: pl.DataFrame, engines: list[str]
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    origins = sorted(wide["origin_year"].unique().to_list())
    predictions: list[pl.DataFrame] = []
    fits: list[dict[str, object]] = []
    feature_names = [f"prediction__{engine}" for engine in engines]
    for origin in origins[1:]:
        train = wide.filter(pl.col("origin_year") < origin)
        test = wide.filter(pl.col("origin_year") == origin)
        weights, _ = nnls(
            train.select(feature_names).to_numpy(),
            train["actual_component_war"].to_numpy(),
        )
        if weights.sum() <= 0:
            weights = np.full(len(engines), 1.0 / len(engines))
        prediction = test.select(feature_names).to_numpy() @ weights
        predictions.append(
            test.select(KEY + ["actual_component_war"]).with_columns(
                pl.Series("prediction_sequential_nnls", prediction)
            )
        )
        fits.append(
            {
                "test_origin": origin,
                "train_origins": sorted(train["origin_year"].unique().to_list()),
                "weights": {
                    engine: float(weight)
                    for engine, weight in zip(engines, weights, strict=True)
                },
            }
        )
    return pl.concat(predictions), fits


def main() -> None:
    args = _args()
    paths = sorted((args.root / "tables").glob("*-predictions.parquet"))
    paths = [path for path in paths if "ensemble" not in path.name]
    if not paths:
        raise ValueError("no engine predictions found")
    frames: dict[str, pl.DataFrame] = {}
    for path in paths:
        engine = path.name.removesuffix("-predictions.parquet")
        frames[engine] = pl.read_parquet(path).sort(KEY)
    reference_engine = sorted(frames)[0]
    reference = frames[reference_engine]
    for engine, frame in frames.items():
        if not frame.select(KEY).equals(reference.select(KEY)):
            raise ValueError(f"prediction keys differ for {engine}")
        if not np.allclose(
            frame["actual_component_war"].to_numpy(),
            reference["actual_component_war"].to_numpy(),
        ):
            raise ValueError(f"actual outcomes differ for {engine}")

    engine_metrics: dict[str, object] = {}
    for engine, frame in frames.items():
        active = frame["actual_active"].to_numpy()
        active_rows = active == 1
        engine_metrics[engine] = {
            "total_value": _metrics(frame, "predicted_component_war"),
            "active_probability": classification_metrics(
                active, frame["active_probability"].to_numpy()
            ),
            "conditional_value_active_players": regression_metrics(
                frame["actual_component_war"].to_numpy()[active_rows],
                frame["predicted_conditional_war"].to_numpy()[active_rows],
            ),
            "fold_total_value": {
                str(origin): _metrics(
                    frame.filter(pl.col("origin_year") == origin),
                    "predicted_component_war",
                )
                for origin in sorted(frame["origin_year"].unique().to_list())
            },
        }
    ranking = sorted(
        frames,
        key=lambda engine: engine_metrics[engine]["total_value"]["rmse"],
    )
    leader = ranking[0]
    comparisons = {
        f"{engine}_minus_{leader}": paired_cluster_rmse_delta(
            reference["actual_component_war"].to_numpy(),
            frames[engine]["predicted_component_war"].to_numpy(),
            frames[leader]["predicted_component_war"].to_numpy(),
            reference["player_id"].to_numpy(),
        )
        for engine in ranking[1:]
    }

    wide = reference.select(KEY + ["actual_component_war"])
    for engine, frame in frames.items():
        wide = wide.with_columns(
            frame["predicted_component_war"].alias(f"prediction__{engine}")
        )
    top_two = ranking[:2]
    top_four = ranking[:4]
    wide = wide.with_columns(
        pl.mean_horizontal([f"prediction__{engine}" for engine in top_two]).alias(
            "prediction_mean_top_two"
        ),
        pl.mean_horizontal([f"prediction__{engine}" for engine in top_four]).alias(
            "prediction_mean_top_four"
        ),
    )
    stack, stack_fits = _sequential_nnls_stack(wide, sorted(frames))
    ensemble = wide.join(stack, on=KEY + ["actual_component_war"], how="left")
    ensemble_metrics = {
        "mean_top_two": {
            "engines": top_two,
            "metrics": _metrics(ensemble, "prediction_mean_top_two"),
            "selection_note": "development-selected; requires nested confirmation",
        },
        "mean_top_four": {
            "engines": top_four,
            "metrics": _metrics(ensemble, "prediction_mean_top_four"),
            "selection_note": "development-selected; requires nested confirmation",
        },
        "sequential_nnls": {
            "engines": sorted(frames),
            "metrics": _metrics(
                ensemble.filter(pl.col("prediction_sequential_nnls").is_not_null()),
                "prediction_sequential_nnls",
            ),
            "evaluated_origins": sorted(stack["origin_year"].unique().to_list()),
            "fits": stack_fits,
            "selection_note": "weights use only earlier out-of-fold seasons",
        },
    }
    artifact = write_canonical_parquet(
        ensemble,
        args.root / "tables/ensemble-predictions.parquet",
        table_name="hitter_model_tournament_v2_ensemble_predictions",
    )
    report = {
        "schema_version": "0.2",
        "status": "fixed_configuration_screen_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "architecture": "two-part: P(MLB active) times conditional total component WAR",
        "ranking_by_total_value_rmse": ranking,
        "engine_metrics": engine_metrics,
        "leader": leader,
        "paired_player_cluster_comparisons": comparisons,
        "ensemble_metrics": ensemble_metrics,
        "ensemble_artifact": artifact.as_record(),
        "decision": {
            "advance_to_nested_tuning": ["ebm", "lightgbm", "xgboost", "catboost"],
            "retain_for_uncertainty": ["ngboost"],
            "do_not_advance": ["ridge", "extra_trees", "histgb", "gpboost"],
            "reason": (
                "EBM leads narrowly; LightGBM, XGBoost, and CatBoost remain close enough "
                "that fixed settings cannot distinguish them fairly."
            ),
        },
    }
    (args.root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ranking": [
                    {
                        "engine": engine,
                        **engine_metrics[engine]["total_value"],
                    }
                    for engine in ranking
                ],
                "ensembles": ensemble_metrics,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
