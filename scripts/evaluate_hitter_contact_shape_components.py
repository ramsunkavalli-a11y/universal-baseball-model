#!/usr/bin/env python3
"""Test explicit contact shape against next-season MLB outcome composition."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    feature_columns,
    matrix_from_panel,
)
from universal_baseball.projection_bootstrap import paired_player_cluster_bootstrap
from universal_baseball.storage import write_canonical_parquet


COMPONENTS = ("K", "BB", "HBP", "1B", "2B", "3B", "HR", "OTHER")
PREFIX = "contact_neutral_lag"


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
        "--mlb-components",
        type=Path,
        required=True,
        help="Historical MLB hitter component table through 2025.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-contact-shape-components-v1"),
    )
    return parser.parse_args()


def _component_targets(frame: pl.DataFrame) -> pl.DataFrame:
    required = {
        "season",
        "player_id",
        "batting_plate_appearances",
        "batting_hits",
        "batting_doubles",
        "batting_triples",
        "batting_home_runs",
        "batting_base_on_balls",
        "batting_hit_by_pitch",
        "batting_strike_outs",
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"MLB component targets missing fields: {missing}")
    if frame.filter(pl.col("season") >= 2026).height:
        raise ValueError("protected 2026 outcomes are not allowed")
    counts = frame.with_columns(
        (
            pl.col("batting_hits")
            - pl.col("batting_doubles")
            - pl.col("batting_triples")
            - pl.col("batting_home_runs")
        ).alias("_1B"),
    ).with_columns(
        pl.col("batting_strike_outs").alias("_K"),
        pl.col("batting_base_on_balls").alias("_BB"),
        pl.col("batting_hit_by_pitch").alias("_HBP"),
        pl.col("batting_doubles").alias("_2B"),
        pl.col("batting_triples").alias("_3B"),
        pl.col("batting_home_runs").alias("_HR"),
    ).with_columns(
        (
            pl.col("batting_plate_appearances")
            - pl.sum_horizontal(*(f"_{component}" for component in COMPONENTS[:-1]))
        ).alias("_OTHER")
    )
    if counts.filter(
        pl.any_horizontal(*(pl.col(f"_{component}") < 0 for component in COMPONENTS))
    ).height:
        raise ValueError("component target accounting produced a negative count")
    return (
        counts.filter(pl.col("batting_plate_appearances") > 0)
        .select(
            pl.col("season").alias("target_season"),
            "player_id",
            pl.col("batting_plate_appearances").alias("target_pa"),
            *(
                (pl.col(f"_{component}") / pl.col("batting_plate_appearances")).alias(
                    f"target_rate__{component}"
                )
                for component in COMPONENTS
            ),
        )
        .sort("target_season", "player_id")
    )


def _variants(panel: pl.DataFrame) -> dict[str, pl.DataFrame]:
    added = [column for column in panel.columns if column.startswith(PREFIX)]
    shape = {
        column
        for column in added
        if "__neutral_shape__" in column
        or column.endswith("__neutral_contact_events")
        or column.endswith("__neutral_contact_levels")
        or column.endswith("__available")
    }
    return {
        "base": panel.drop(added),
        "base_plus_shape": panel.select(
            column
            for column in panel.columns
            if not column.startswith(PREFIX) or column in shape
        ),
    }


def _model(random_state: int):
    from lightgbm import LGBMRegressor

    return LGBMRegressor(
        objective="regression_l2",
        n_estimators=250,
        learning_rate=0.03,
        num_leaves=15,
        max_depth=5,
        min_child_samples=60,
        colsample_bytree=0.70,
        reg_alpha=0.25,
        reg_lambda=4.0,
        random_state=random_state,
        n_jobs=-1,
        verbosity=-1,
    )


def _normalize(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, 1e-6, None)
    return clipped / clipped.sum(axis=1, keepdims=True)


def _metrics(
    actual: np.ndarray, predicted: np.ndarray, weight: np.ndarray
) -> dict[str, object]:
    denominator = float(weight.sum())
    component_rmse = {
        component: float(
            np.sqrt(
                np.sum(weight * np.square(predicted[:, index] - actual[:, index]))
                / denominator
            )
        )
        for index, component in enumerate(COMPONENTS)
    }
    clipped = np.clip(predicted, 1e-7, 1.0)
    return {
        "rate_rmse": float(
            np.sqrt(
                np.sum(weight[:, None] * np.square(predicted - actual))
                / (denominator * len(COMPONENTS))
            )
        ),
        "multinomial_log_loss": float(
            -np.sum(weight[:, None] * actual * np.log(clipped)) / denominator
        ),
        "multinomial_brier": float(
            np.sum(weight[:, None] * np.square(predicted - actual)) / denominator
        ),
        "component_rmse": component_rmse,
    }


def _run_variant(
    panel: pl.DataFrame, targets: pl.DataFrame, name: str
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    columns = feature_columns(panel)
    joined = panel.join(
        targets,
        on=["target_season", "player_id"],
        how="inner",
        validate="m:1",
    )
    folds = expanding_year_folds(panel["origin_year"].unique().to_list())
    outputs: list[pl.DataFrame] = []
    fold_metrics: list[dict[str, object]] = []
    for fold in folds:
        train = joined.filter(pl.col("origin_year").is_in(fold.train_origins))
        test = joined.filter(pl.col("origin_year") == fold.test_origin)
        x_train = matrix_from_panel(train, columns)
        x_test = matrix_from_panel(test, columns)
        actual_train = train.select(
            *(f"target_rate__{component}" for component in COMPONENTS)
        ).to_numpy()
        actual_test = test.select(
            *(f"target_rate__{component}" for component in COMPONENTS)
        ).to_numpy()
        training_weight = np.sqrt(train["target_pa"].to_numpy().astype(float))
        predictions = []
        for index, component in enumerate(COMPONENTS):
            model = _model(417 + fold.test_origin * 10 + index)
            model.fit(
                x_train,
                actual_train[:, index],
                sample_weight=training_weight,
            )
            predictions.append(model.predict(x_test))
        predicted = _normalize(np.column_stack(predictions))
        evaluation_weight = test["target_pa"].to_numpy().astype(float)
        metric = _metrics(actual_test, predicted, evaluation_weight)
        fold_metrics.append(
            {
                "origin_year": fold.test_origin,
                "target_season": fold.test_origin + 1,
                "players": test.height,
                "plate_appearances": int(test["target_pa"].sum()),
                **metric,
            }
        )
        outputs.append(
            test.select(
                "origin_year",
                "target_season",
                "player_id",
                "target_pa",
                pl.col("lag0__highest_level").alias("source_highest_level"),
                *(f"target_rate__{component}" for component in COMPONENTS),
            ).with_columns(
                pl.lit(name).alias("model"),
                *(
                    pl.Series(f"predicted_rate__{component}", predicted[:, index])
                    for index, component in enumerate(COMPONENTS)
                ),
            )
        )
    return pl.concat(outputs), fold_metrics


def _matrix(frame: pl.DataFrame, prefix: str) -> np.ndarray:
    return frame.select(
        *(f"{prefix}_rate__{component}" for component in COMPONENTS)
    ).to_numpy()


def main() -> int:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(exist_ok=True)
    panel = pl.read_parquet(args.panel)
    if panel.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 targets are not allowed")
    targets = _component_targets(pl.read_parquet(args.mlb_components))
    predictions: dict[str, pl.DataFrame] = {}
    folds: dict[str, list[dict[str, object]]] = {}
    for name, variant in _variants(panel).items():
        print(f"{name}: {len(feature_columns(variant))} features", flush=True)
        predictions[name], folds[name] = _run_variant(variant, targets, name)
    combined = pl.concat(predictions.values())
    artifact = write_canonical_parquet(
        combined,
        table_root / "predictions.parquet",
        table_name="hitter_contact_shape_component_predictions_v1",
    )

    pooled: dict[str, object] = {}
    subgroup: dict[str, object] = {}
    for name, frame in predictions.items():
        actual = _matrix(frame, "target")
        predicted = _matrix(frame, "predicted")
        weight = frame["target_pa"].to_numpy().astype(float)
        pooled[name] = _metrics(actual, predicted, weight)
        subgroup[name] = {
            group: _metrics(
                _matrix(selected, "target"),
                _matrix(selected, "predicted"),
                selected["target_pa"].to_numpy().astype(float),
            )
            for group, selected in (
                (
                    "current_mlb",
                    frame.filter(pl.col("source_highest_level") == "MLB"),
                ),
                (
                    "advancing_to_mlb",
                    frame.filter(pl.col("source_highest_level") != "MLB"),
                ),
            )
            if not selected.is_empty()
        }
    base = predictions["base"]
    candidate = predictions["base_plus_shape"]
    actual = _matrix(base, "target")
    base_probability = _matrix(base, "predicted")
    candidate_probability = _matrix(candidate, "predicted")
    comparison = paired_player_cluster_bootstrap(
        player_ids=base["player_id"].to_numpy(),
        actual=actual,
        baseline=base_probability,
        candidate=candidate_probability,
        weights=base["target_pa"].to_numpy().astype(float),
        repetitions=5_000,
        seed=1729,
    )
    report = {
        "schema_version": "1.0",
        "status": "chronological_component_evaluation_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season MLB plate-appearance outcome composition among active hitters",
        "components": list(COMPONENTS),
        "players": base.height,
        "unique_players": base["player_id"].n_unique(),
        "plate_appearances": int(base["target_pa"].sum()),
        "pooled_metrics": pooled,
        "subgroup_metrics": subgroup,
        "fold_metrics": folds,
        "shape_minus_base_bootstrap": comparison,
        "artifact": artifact.as_record(),
        "source": {
            "panel": str(args.panel),
            "mlb_components": str(args.mlb_components),
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "base": pooled["base"],
                "base_plus_shape": pooled["base_plus_shape"],
                "shape_minus_base_bootstrap": comparison,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
