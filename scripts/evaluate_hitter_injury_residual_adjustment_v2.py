#!/usr/bin/env python3
"""Test a narrow injury-only residual adjustment to selected hitter workload."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from universal_baseball.historical_injury_features import FEATURE_COLUMNS
from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


PANEL_PATH = Path(
    "reports/generated/hitter-injury-feature-challenger-v2/"
    "modeling-panel-with-injury.parquet"
)
BASELINE_PATH = Path(
    "reports/generated/hitter-roster-feature-challenger-v2/"
    "chronological-predictions.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-injury-residual-adjustment-v2")
ALPHAS = (10.0, 100.0, 1000.0)
FEATURES = (
    "prediction_roster_expected_pa",
    "injury__placements_365",
    "injury__placements_730",
    "injury__days_365",
    "injury__days_730",
    "injury__long_placements_730",
    "injury__activations_365",
    "injury__on_list_at_cutoff",
    "injury__current_spell_days",
)


def _eligible_expression() -> pl.Expr:
    return (pl.col("player_stage") == "current_mlb") & (
        pl.col("injury__days_730") > 0
    )


def _fit_predict(
    train: pl.DataFrame,
    test: pl.DataFrame,
    *,
    alpha: float,
) -> np.ndarray:
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        Ridge(alpha=alpha),
    )
    x_train = train.select(FEATURES).to_numpy()
    residual = (
        train["actual_pa"].to_numpy()
        - train["prediction_roster_expected_pa"].to_numpy()
    )
    model.fit(x_train, residual)
    return np.clip(model.predict(test.select(FEATURES).to_numpy()), -100.0, 100.0)


def _choose_alpha(prior: pl.DataFrame) -> tuple[float, dict[str, float]]:
    origins = sorted(prior["origin_year"].unique().to_list())
    if len(origins) < 2:
        return 100.0, {}
    validation_origin = origins[-1]
    train = prior.filter(
        (pl.col("origin_year") < validation_origin) & _eligible_expression()
    )
    validation_all = prior.filter(pl.col("origin_year") == validation_origin)
    validation = validation_all.filter(_eligible_expression())
    if train.height < 100 or validation.height < 25:
        return 100.0, {}
    actual = validation_all["actual_pa"].to_numpy()
    baseline = validation_all["prediction_roster_expected_pa"].to_numpy()
    scores: dict[str, float] = {}
    eligible_ids = set(validation["player_id"].to_list())
    mask = np.array(
        [player_id in eligible_ids for player_id in validation_all["player_id"]],
        dtype=bool,
    )
    for alpha in ALPHAS:
        adjusted = baseline.copy()
        adjusted[mask] = np.clip(
            baseline[mask] + _fit_predict(train, validation, alpha=alpha),
            0.0,
            750.0,
        )
        scores[str(alpha)] = regression_metrics(actual, adjusted)["rmse"]
    return min(ALPHAS, key=lambda alpha: scores[str(alpha)]), scores


def _segment_metrics(frame: pl.DataFrame) -> dict[str, object]:
    actual = frame["actual_pa"].to_numpy()
    baseline = frame["prediction_roster_expected_pa"].to_numpy()
    adjusted = frame["prediction_injury_residual_expected_pa"].to_numpy()
    return {
        "rows": frame.height,
        "baseline": regression_metrics(actual, baseline),
        "residual_adjustment": regression_metrics(actual, adjusted),
        "adjustment_minus_baseline_rmse": (
            regression_metrics(actual, adjusted)["rmse"]
            - regression_metrics(actual, baseline)["rmse"]
        ),
    }


def main() -> None:
    panel = pl.read_parquet(PANEL_PATH).select(
        "origin_year",
        "player_id",
        "lag0__pa_level__MLB",
        *FEATURE_COLUMNS,
    )
    frame = (
        pl.read_parquet(BASELINE_PATH)
        .join(panel, on=["origin_year", "player_id"], how="left", validate="1:1")
        .with_columns(
            pl.when(pl.col("lag0__pa_level__MLB") > 0)
            .then(pl.lit("current_mlb"))
            .when(pl.col("player_stage").is_in(["upper_minors", "lower_minors"]))
            .then(pl.col("player_stage"))
            .otherwise(pl.lit("lower_minors"))
            .alias("player_stage")
        )
        .sort(["origin_year", "player_id"])
    )
    output_frames: list[pl.DataFrame] = []
    fold_details: dict[str, object] = {}
    for origin in sorted(frame["origin_year"].unique().to_list()):
        test = frame.filter(pl.col("origin_year") == origin)
        prior = frame.filter(pl.col("origin_year") < origin)
        eligible_test = test.filter(_eligible_expression())
        alpha, tuning = _choose_alpha(prior)
        adjusted = test["prediction_roster_expected_pa"].to_numpy().copy()
        if not prior.is_empty() and not eligible_test.is_empty():
            train = prior.filter(_eligible_expression())
            if train.height >= 100:
                eligible_ids = set(eligible_test["player_id"].to_list())
                mask = np.array(
                    [player_id in eligible_ids for player_id in test["player_id"]],
                    dtype=bool,
                )
                adjusted[mask] = np.clip(
                    adjusted[mask]
                    + _fit_predict(train, eligible_test, alpha=alpha),
                    0.0,
                    750.0,
                )
        fold = test.with_columns(
            pl.Series("prediction_injury_residual_expected_pa", adjusted),
            pl.lit(alpha).alias("residual_ridge_alpha"),
            _eligible_expression().cast(pl.Int8).alias("injury_adjustment_eligible"),
        )
        output_frames.append(fold)
        fold_details[str(origin)] = {
            "selected_alpha": alpha,
            "earlier_fold_tuning_rmse": tuning,
            "training_eligible_rows": int(
                prior.filter(_eligible_expression()).height
            ),
            "adjusted_test_rows": int(eligible_test.height),
            "metrics": _segment_metrics(fold),
        }
    result = pl.concat(output_frames).sort(["origin_year", "player_id"])
    actual = result["actual_pa"].to_numpy()
    baseline = result["prediction_roster_expected_pa"].to_numpy()
    adjusted = result["prediction_injury_residual_expected_pa"].to_numpy()
    by_stage = {
        stage: _segment_metrics(result.filter(pl.col("player_stage") == stage))
        for stage in ("current_mlb", "upper_minors", "lower_minors")
    }
    by_injury = {
        "eligible_injury_history": _segment_metrics(
            result.filter(pl.col("injury_adjustment_eligible") == 1)
        ),
        "unchanged_population": _segment_metrics(
            result.filter(pl.col("injury_adjustment_eligible") == 0)
        ),
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        result,
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_injury_residual_adjustment_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_injury_residual_adjustment_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "population_rows": result.height,
        "design": (
            "chronological ridge correction to expected PA only for current MLB "
            "players with public injured-list days in the prior 730 days"
        ),
        "features": list(FEATURES),
        "alpha_grid": list(ALPHAS),
        "adjustment_clip_pa": [-100.0, 100.0],
        "overall": {
            "roster_baseline": regression_metrics(actual, baseline),
            "residual_adjustment": regression_metrics(actual, adjusted),
            "paired_adjustment_minus_baseline": paired_cluster_rmse_delta(
                actual,
                adjusted,
                baseline,
                result["player_id"].to_numpy(),
            ),
        },
        "folds": fold_details,
        "by_player_stage": by_stage,
        "by_injury_history": by_injury,
        "active_probability_changed": False,
        "sources": {
            "panel": {"path": str(PANEL_PATH), "sha256": sha256_file(PANEL_PATH)},
            "baseline": {
                "path": str(BASELINE_PATH),
                "sha256": sha256_file(BASELINE_PATH),
            },
        },
        "artifact": artifact.as_record(),
        "limitations": [
            "The first test fold is unchanged because no earlier out-of-fold residuals exist.",
            "This test cannot improve or harm Brier or log loss because arrival probabilities are unchanged.",
            "The correction is deliberately restricted to established MLB players with public injury evidence.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
