#!/usr/bin/env python3
"""Rebuild next-season general-defense exposure with the new workload model."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

from lightgbm import LGBMRegressor
import numpy as np
import polars as pl
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.player_value_defense_projection import GENERAL_POSITIONS
from universal_baseball.storage import sha256_file, write_canonical_parquet


OLD_REPORTS = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
WORKLOAD_PATH = Path(
    "reports/generated/hitter-workload-model-v2/chronological-predictions.parquet"
)
PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
FIELDING_ORIGIN_PATH = (
    OLD_REPORTS
    / "position-capacity-source/historical/reports/generated/"
    "position-role-historical-source/tables/historical_fielding_usage.parquet"
)
MLB_FIELDING_PATH = (
    OLD_REPORTS
    / "mlb-fielding-outcome-inventory-2004-2025/tables/"
    "mlb_fielding_usage_2004_2025.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-defense-exposure-v2")
ORIGINS = (2021, 2022, 2023, 2024)
DEVELOPMENT_ORIGINS = (2022, 2023)
CONFIRMATION_ORIGIN = 2024
MAX_DEFENSIVE_OUTS = 4374.0
POSITION_COLUMNS = tuple(sorted(GENERAL_POSITIONS))
NUMERIC_FEATURES = (
    "prediction_candidate_expected_pa",
    "prediction_candidate_active_probability",
    "conditional_mlb_pa",
    "current_mlb_pa",
    "age",
    "prior_mlb_general_outs",
    "prior_mlb_catcher_outs",
    "prior_mlb_dh_starts",
    "prior_affiliated_general_outs",
    "prior_affiliated_catcher_outs",
    *(f"prior_mlb_outs_{position}" for position in POSITION_COLUMNS),
    *(f"prior_affiliated_outs_{position}" for position in POSITION_COLUMNS),
)
CATEGORICAL_FEATURES = ("current_highest_level",)


def _fielding_wide(
    frame: pl.DataFrame,
    *,
    level_filter: str | None,
    prefix: str,
) -> pl.DataFrame:
    data = frame.filter(pl.col("season").is_in(ORIGINS))
    if level_filter is not None:
        data = data.filter(pl.col("level_group") == level_filter)
    general = (
        data.filter(pl.col("position_abbreviation").is_in(POSITION_COLUMNS))
        .group_by("season", "player_id", "position_abbreviation")
        .agg(pl.col("fielding_outs").sum())
        .pivot(
            on="position_abbreviation",
            index=["season", "player_id"],
            values="fielding_outs",
        )
    )
    for position in POSITION_COLUMNS:
        if position not in general.columns:
            general = general.with_columns(pl.lit(0).alias(position))
    general = general.select(
        "season",
        "player_id",
        *(
            pl.col(position).fill_null(0).alias(f"{prefix}_outs_{position}")
            for position in POSITION_COLUMNS
        ),
    ).with_columns(
        pl.sum_horizontal(
            [f"{prefix}_outs_{position}" for position in POSITION_COLUMNS]
        ).alias(f"{prefix}_general_outs")
    )
    other = data.group_by("season", "player_id").agg(
        pl.col("fielding_outs")
        .filter(pl.col("position_abbreviation") == "C")
        .sum()
        .alias(f"{prefix}_catcher_outs"),
        pl.col("games_started")
        .filter(pl.col("position_abbreviation") == "DH")
        .sum()
        .alias(f"{prefix}_dh_starts"),
    )
    return general.join(
        other, on=["season", "player_id"], how="full", coalesce=True
    ).with_columns(
        pl.exclude("season", "player_id").fill_null(0)
    )


def _panel() -> pl.DataFrame:
    workload = pl.read_parquet(WORKLOAD_PATH).filter(
        pl.col("origin_year").is_in(ORIGINS)
    )
    age = pl.read_parquet(PANEL_PATH).select(
        "origin_year", "player_id", pl.col("lag0__age").alias("age")
    )
    origin = pl.read_parquet(FIELDING_ORIGIN_PATH)
    mlb = _fielding_wide(origin, level_filter="MLB", prefix="prior_mlb")
    affiliated = _fielding_wide(
        origin, level_filter=None, prefix="prior_affiliated"
    ).drop("prior_affiliated_dh_starts")
    target = (
        pl.read_parquet(MLB_FIELDING_PATH)
        .filter(
            pl.col("season").is_in([origin + 1 for origin in ORIGINS])
            & pl.col("position_abbreviation").is_in(POSITION_COLUMNS)
        )
        .group_by("season", "player_id")
        .agg(pl.col("fielding_outs").sum().alias("actual_general_outs"))
        .rename({"season": "target_season"})
    )
    return (
        workload.join(age, on=["origin_year", "player_id"], how="left", validate="1:1")
        .join(
            mlb.rename({"season": "origin_year"}),
            on=["origin_year", "player_id"],
            how="left",
            validate="1:1",
        )
        .join(
            affiliated.rename({"season": "origin_year"}),
            on=["origin_year", "player_id"],
            how="left",
            validate="1:1",
        )
        .join(
            target,
            on=["target_season", "player_id"],
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("actual_general_outs").fill_null(0.0),
            pl.col("age").fill_null(pl.col("age").median()),
            pl.when(pl.col("prediction_candidate_active_probability") > 0)
            .then(
                pl.col("prediction_candidate_expected_pa")
                / pl.col("prediction_candidate_active_probability")
            )
            .otherwise(0.0)
            .alias("conditional_mlb_pa"),
            pl.exclude(
                "origin_year",
                "target_season",
                "player_id",
                "actual_active",
                "actual_pa",
                "prediction_candidate_expected_pa",
                "prediction_candidate_active_probability",
                "prediction_carry_forward_pa",
                "current_highest_level",
                "current_mlb_pa",
                "age",
                "actual_general_outs",
                "conditional_mlb_pa",
            ).fill_null(0),
        )
        .sort(["origin_year", "player_id"])
    )


def _pipeline(model: object) -> Pipeline:
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric, list(NUMERIC_FEATURES)),
            ("categorical", categorical, list(CATEGORICAL_FEATURES)),
        ]
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def _models() -> dict[str, Pipeline]:
    return {
        "ridge": _pipeline(Ridge(alpha=100.0)),
        "hist_gradient_boosting": _pipeline(
            HistGradientBoostingRegressor(
                learning_rate=0.05,
                max_iter=250,
                max_leaf_nodes=15,
                min_samples_leaf=50,
                l2_regularization=25.0,
                random_state=1729,
            )
        ),
        "lightgbm": _pipeline(
            LGBMRegressor(
                objective="regression",
                n_estimators=300,
                learning_rate=0.03,
                num_leaves=15,
                min_child_samples=50,
                reg_lambda=25.0,
                verbosity=-1,
                random_state=1729,
                n_jobs=1,
            )
        ),
        "extra_trees": _pipeline(
            ExtraTreesRegressor(
                n_estimators=300,
                min_samples_leaf=20,
                max_features=0.8,
                random_state=1729,
                n_jobs=1,
            )
        ),
    }


def _clip(values: np.ndarray) -> np.ndarray:
    return np.clip(np.asarray(values, dtype=float), 0.0, MAX_DEFENSIVE_OUTS)


def _fit_fold(panel: pl.DataFrame, test_origin: int) -> pl.DataFrame:
    train = panel.filter(pl.col("origin_year") < test_origin)
    test = panel.filter(pl.col("origin_year") == test_origin)
    if train.is_empty() or test.is_empty():
        raise ValueError(f"empty defense exposure fold {test_origin}")
    train_pd = train.select(*NUMERIC_FEATURES, *CATEGORICAL_FEATURES).to_pandas()
    test_pd = test.select(*NUMERIC_FEATURES, *CATEGORICAL_FEATURES).to_pandas()
    y_train = train["actual_general_outs"].to_numpy()

    pa_scale = float(
        y_train.sum()
        / max(train["prediction_candidate_expected_pa"].sum(), 1e-12)
    )
    train_pa = _clip(
        train["prediction_candidate_expected_pa"].to_numpy() * pa_scale
    )
    test_pa = _clip(
        test["prediction_candidate_expected_pa"].to_numpy() * pa_scale
    )
    train_carry = train["prior_mlb_general_outs"].to_numpy().astype(float)
    test_carry = test["prior_mlb_general_outs"].to_numpy().astype(float)
    direction = train_carry - train_pa
    denominator = float(np.dot(direction, direction))
    blend_weight = (
        float(np.clip(np.dot(direction, y_train - train_pa) / denominator, 0.0, 1.0))
        if denominator > 0
        else 0.0
    )
    predictions: dict[str, np.ndarray] = {
        "carry_forward": _clip(test_carry),
        "pa_scale": test_pa,
        "learned_blend": _clip(
            blend_weight * test_carry + (1.0 - blend_weight) * test_pa
        ),
    }
    machine_predictions = []
    for name, model in _models().items():
        model.fit(train_pd, y_train)
        prediction = _clip(model.predict(test_pd))
        predictions[name] = prediction
        machine_predictions.append(prediction)
    predictions["machine_equal_mean"] = np.mean(machine_predictions, axis=0)

    return test.select(
        "origin_year",
        "target_season",
        "player_id",
        "actual_general_outs",
        "prior_mlb_general_outs",
        "prediction_candidate_expected_pa",
        "prediction_candidate_active_probability",
        "current_highest_level",
    ).with_columns(
        pl.lit(pa_scale).alias("fitted_pa_to_general_outs_scale"),
        pl.lit(blend_weight).alias("fitted_carry_blend_weight"),
        *(
            pl.Series(f"prediction__{name}", prediction)
            for name, prediction in predictions.items()
        ),
    )


def _metrics(frame: pl.DataFrame, method: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_general_outs"].to_numpy(),
        frame[f"prediction__{method}"].to_numpy(),
    )


def _subgroups(frame: pl.DataFrame, method: str) -> dict[str, dict[str, float]]:
    groups = {
        "target_positive": pl.col("actual_general_outs") > 0,
        "entrant": (pl.col("prior_mlb_general_outs") == 0)
        & (pl.col("actual_general_outs") > 0),
        "incumbent": (pl.col("prior_mlb_general_outs") > 0)
        & (pl.col("actual_general_outs") > 0),
        "exit": (pl.col("prior_mlb_general_outs") > 0)
        & (pl.col("actual_general_outs") == 0),
    }
    result = {}
    for name, condition in groups.items():
        segment = frame.filter(condition)
        result[name] = {
            "rows": segment.height,
            **_metrics(segment, method),
        }
    return result


def main() -> None:
    panel = _panel()
    predictions = pl.concat(
        [_fit_fold(panel, origin) for origin in DEVELOPMENT_ORIGINS + (CONFIRMATION_ORIGIN,)]
    ).sort(["origin_year", "player_id"])
    methods = [
        column.removeprefix("prediction__")
        for column in predictions.columns
        if column.startswith("prediction__")
    ]
    development = predictions.filter(pl.col("origin_year").is_in(DEVELOPMENT_ORIGINS))
    confirmation = predictions.filter(pl.col("origin_year") == CONFIRMATION_ORIGIN)
    development_metrics = {method: _metrics(development, method) for method in methods}
    simple_methods = ("carry_forward", "pa_scale")
    candidate_methods = [method for method in methods if method not in simple_methods]
    selected = min(candidate_methods, key=lambda name: development_metrics[name]["rmse"])
    best_simple = min(simple_methods, key=lambda name: development_metrics[name]["rmse"])
    development_passed = (
        development_metrics[selected]["rmse"] < development_metrics[best_simple]["rmse"]
        and development_metrics[selected]["mae"]
        <= 1.02 * development_metrics[best_simple]["mae"]
    )
    confirmation_metrics = {method: _metrics(confirmation, method) for method in methods}
    confirmation_passed = (
        development_passed
        and confirmation_metrics[selected]["rmse"]
        < confirmation_metrics[best_simple]["rmse"]
        and confirmation_metrics[selected]["mae"]
        <= 1.02 * confirmation_metrics[best_simple]["mae"]
        and _subgroups(confirmation, selected)["entrant"]["rmse"]
        < _subgroups(confirmation, "carry_forward")["entrant"]["rmse"]
    )

    player_ids = confirmation["player_id"].to_numpy()
    actual = confirmation["actual_general_outs"].to_numpy()
    paired = paired_cluster_rmse_delta(
        actual,
        confirmation[f"prediction__{selected}"].to_numpy(),
        confirmation[f"prediction__{best_simple}"].to_numpy(),
        player_ids,
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        predictions,
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_defense_exposure_v2_chronological_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_defense_exposure_challenger_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season MLB general-position defensive outs",
        "development_origins": list(DEVELOPMENT_ORIGINS),
        "confirmation_origin": CONFIRMATION_ORIGIN,
        "selection_rule": (
            "lowest development RMSE among challengers; must beat the best simple "
            "baseline and keep MAE within 2%; confirmation repeats those gates and "
            "must improve entrant RMSE over raw carry-forward"
        ),
        "development_metrics": development_metrics,
        "confirmation_metrics": confirmation_metrics,
        "selected_challenger": selected,
        "best_simple_baseline": best_simple,
        "development_passed": development_passed,
        "confirmation_passed": confirmation_passed,
        "confirmation_paired_comparison": paired,
        "confirmation_subgroups": {
            method: _subgroups(confirmation, method)
            for method in ("carry_forward", "pa_scale", best_simple, selected)
        },
        "fold_parameters": predictions.group_by("origin_year")
        .agg(
            pl.col("fitted_pa_to_general_outs_scale").first(),
            pl.col("fitted_carry_blend_weight").first(),
        )
        .sort("origin_year")
        .to_dicts(),
        "artifact": artifact.as_record(),
        "sources": {
            "workload": {
                "path": str(WORKLOAD_PATH),
                "sha256": sha256_file(WORKLOAD_PATH),
            },
            "panel": {"path": str(PANEL_PATH), "sha256": sha256_file(PANEL_PATH)},
            "origin_fielding": {
                "path": str(FIELDING_ORIGIN_PATH),
                "sha256": sha256_file(FIELDING_ORIGIN_PATH),
            },
            "mlb_fielding": {
                "path": str(MLB_FIELDING_PATH),
                "sha256": sha256_file(MLB_FIELDING_PATH),
            },
        },
        "limitations": [
            "The model forecasts general-position defensive outs, not defensive skill.",
            "The 2025 fold is exposed development confirmation, not the sealed 2026 test.",
            "Catcher exposure is separate from the general-range bridge.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "selected_challenger": selected,
                "best_simple_baseline": best_simple,
                "development_passed": development_passed,
                "confirmation_passed": confirmation_passed,
                "development_metrics": development_metrics,
                "confirmation_metrics": confirmation_metrics,
                "confirmation_paired_comparison": paired,
                "fold_parameters": report["fold_parameters"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
