#!/usr/bin/env python3
"""Attribute the hitter gradient gain with fixed cumulative feature families."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor

from score_hitter_gradient_challenger_v1 import (
    EVALUATION_ORIGINS,
    TREE_PARAMETERS,
    _design,
    _metrics,
    _normalize,
    _probabilities,
)
from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES
from universal_baseball.projection_bootstrap import paired_player_cluster_bootstrap
from universal_baseball.storage import write_canonical_parquet


BOOTSTRAP_REPETITIONS = 5000


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path(
            "reports/generated/hitter-gradient-dataset-v1/tables/modeling-rows.parquet"
        ),
    )
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-gradient-ablation-v1"),
    )
    return parser.parse_args()


def _families(frame: pl.DataFrame) -> dict[str, list[str]]:
    numeric = {name for name, dtype in frame.schema.items() if dtype.is_numeric()}
    core = [
        name
        for name in (
            "contacts__feature",
            "log_contacts",
            "age",
            "relative_age",
            "age_centered_sq",
            "relative_age_sq",
            "age_missing",
            "materialized_contacts",
        )
        if name in numeric
    ]
    contact = [
        name
        for name in frame.columns
        if name in numeric
        and (
            (name.startswith("overall__") and name.endswith("__feature"))
            or name.startswith("share__")
            or name.startswith("contact_result__")
            or name.startswith("contact_count__")
        )
    ]
    opponent = [
        name
        for name in frame.columns
        if name in numeric
        and (
            name.startswith("mean__")
            or name
            in {
                "opponent_context_known_rate",
                "contact_share_vs_lhp",
                "contact_share_vs_rhp",
            }
        )
    ]
    park = [
        name
        for name in frame.columns
        if name in numeric
        and (
            name.startswith("park_effect__")
            or name
            in {
                "venue_known_rate",
                "park_factor_known_rate",
                "mean_park_factor_reliability",
                "mean_park_training_seasons",
            }
        )
    ]
    result = {
        "tree_control": core,
        "contact_detail": [*core, *contact],
        "plus_opponent": [*core, *contact, *opponent],
        "plus_park": [*core, *contact, *opponent, *park],
    }
    if [len(result[name]) for name in result] != sorted(len(value) for value in result.values()):
        raise ValueError("feature families must be cumulative")
    return result


def _fit_tree(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    columns: list[str],
) -> np.ndarray:
    x_train, x_score = _design(training, evaluation, columns)
    actual = _probabilities(training, "target__overall__")
    baseline_train = _probabilities(training, "contact_only__overall__")
    baseline_score = _probabilities(evaluation, "contact_only__overall__")
    residual = actual - baseline_train
    weights = training["target_contacts"].to_numpy().astype(float)
    predictions = []
    for index in range(len(CONTACT_OUTCOMES)):
        model = HistGradientBoostingRegressor(**TREE_PARAMETERS).fit(
            x_train, residual[:, index], sample_weight=weights
        )
        predictions.append(model.predict(x_score))
    return _normalize(baseline_score + np.column_stack(predictions))


def main() -> int:
    args = _args()
    frame = pl.read_parquet(args.dataset)
    if frame.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 rows are not allowed")
    families = _families(frame)
    output_rows = []
    fold_metrics = []
    for origin in EVALUATION_ORIGINS:
        training = frame.filter(pl.col("origin_year") < origin)
        evaluation = frame.filter(pl.col("origin_year") == origin)
        base = _probabilities(evaluation, "contact_only__overall__")
        predictions = {
            name: _fit_tree(training, evaluation, columns)
            for name, columns in families.items()
        }
        actual = _probabilities(evaluation, "target__overall__")
        weights = evaluation["target_contacts"].to_numpy().astype(float)
        base_metrics = _metrics(actual, base, weights)
        for name, prediction in predictions.items():
            metric = _metrics(actual, prediction, weights)
            fold_metrics.append(
                {
                    "origin_year": origin,
                    "model": name,
                    "players": evaluation.height,
                    **metric,
                    **{
                        f"{key}_vs_contact_only": metric[key] - base_metrics[key]
                        for key in base_metrics
                    },
                }
            )
        output = evaluation.select(
            "origin_year",
            "target_season",
            "player_id",
            "source_level",
            "target_source_level",
            "target_contacts",
        ).with_columns(
            *(
                pl.Series(f"actual__{outcome}", actual[:, index])
                for index, outcome in enumerate(CONTACT_OUTCOMES)
            ),
            *(
                pl.Series(f"contact_only__{outcome}", base[:, index])
                for index, outcome in enumerate(CONTACT_OUTCOMES)
            ),
        )
        for name, prediction in predictions.items():
            output = output.with_columns(
                *(
                    pl.Series(f"{name}__{outcome}", prediction[:, index])
                    for index, outcome in enumerate(CONTACT_OUTCOMES)
                )
            )
        output_rows.append(output)

    predictions = pl.concat(output_rows, how="vertical_relaxed")
    actual = predictions.select(
        *(f"actual__{value}" for value in CONTACT_OUTCOMES)
    ).to_numpy()
    weights = predictions["target_contacts"].to_numpy().astype(float)
    players = predictions["player_id"].to_numpy()
    model_order = ["contact_only", *families]
    matrices = {
        name: predictions.select(
            *(f"{name}__{value}" for value in CONTACT_OUTCOMES)
        ).to_numpy()
        for name in model_order
    }
    pooled = {name: _metrics(actual, value, weights) for name, value in matrices.items()}
    comparisons = {}
    for index, name in enumerate(model_order[1:], start=1):
        for reference in ("contact_only", model_order[index - 1]):
            key = f"{name}_vs_{reference}"
            if key in comparisons:
                continue
            comparisons[key] = {
                "point_delta": {
                    metric: pooled[name][metric] - pooled[reference][metric]
                    for metric in pooled[name]
                },
                "paired_player_bootstrap": paired_player_cluster_bootstrap(
                    player_ids=players,
                    actual=actual,
                    baseline=matrices[reference],
                    candidate=matrices[name],
                    weights=weights,
                    repetitions=BOOTSTRAP_REPETITIONS,
                    seed=1729,
                ),
            }

    full = comparisons["plus_park_vs_contact_only"]
    statistically_clear = all(
        full["paired_player_bootstrap"][metric]["upper_95"] < 0
        for metric in ("rate_rmse", "multinomial_log_loss", "multinomial_brier")
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "predictions": write_canonical_parquet(
            predictions,
            args.output_root / "predictions.parquet",
            table_name="hitter_gradient_ablation_v1_predictions",
        ).as_record(),
        "fold_metrics": write_canonical_parquet(
            pl.DataFrame(fold_metrics),
            args.output_root / "fold-metrics.parquet",
            table_name="hitter_gradient_ablation_v1_fold_metrics",
        ).as_record(),
    }
    report = {
        "schema_version": "1.0",
        "status": "hitter_gradient_feature_ablation_complete",
        "as_of_date": args.as_of_date.isoformat(),
        "protected_2026_outcomes_used": False,
        "evaluated_players": predictions.height,
        "unique_player_clusters": predictions["player_id"].n_unique(),
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "feature_families": {name: {"feature_count": len(value), "columns": value} for name, value in families.items()},
        "pooled_metrics": pooled,
        "comparisons": comparisons,
        "fold_metrics": fold_metrics,
        "full_model_statistically_clear_on_all_three_metrics": statistically_clear,
        "development_promotion_gate": {
            "passed": statistically_clear,
            "rule": "full model's paired 95% interval must be below zero on RMSE, log loss, and Brier",
        },
        "production_promotion_gate": {
            "passed": False,
            "reason": "2026 remains the protected final confirmation season",
        },
        "artifacts": artifacts,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
