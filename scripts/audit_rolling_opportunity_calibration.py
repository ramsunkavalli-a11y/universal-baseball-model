#!/usr/bin/env python3
"""Rolling-origin participation calibration for the universal opportunity models."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.opportunity_model_v2 import (
    build_universal_hitter_opportunity_fold,
    build_universal_hitter_opportunity_predictors,
    fit_universal_hitter_opportunity_form,
)
from universal_baseball.pitcher_opportunity_model_v2 import (
    build_universal_pitcher_opportunity_fold,
    build_universal_pitcher_opportunity_predictors,
    fit_universal_pitcher_opportunity_form,
)
from universal_baseball.playing_time_model import (
    PT_FORM_P,
    PT_FORM_U,
    build_playing_time_design,
    predict_playing_time_hurdle,
)
from universal_baseball.storage import write_canonical_parquet
from universal_baseball.war_uncertainty_validation import (
    summarize_binary_probability_calibration,
)
from universal_baseball.workload_uncertainty_validation import (
    summarize_positive_workload_coverage,
)


SOURCE = Path("reports/generated/opportunity-history-sources-v2/tables")
MEMBERSHIP = Path(
    "reports/generated/opportunity-40man-history/tables/historical_40man_membership.parquet"
)
OUTPUT = Path("reports/generated/rolling-opportunity-calibration")
TARGETS = (2022, 2023, 2024, 2025)
ELIGIBLE_TRAINING_SNAPSHOTS = (2018, 2021, 2022, 2023)


def _stats(year: int) -> pl.DataFrame:
    return pl.read_parquet(SOURCE / str(year) / "affiliated_season_stats.parquet")


def _outcome(stats: pl.DataFrame, *, component: str) -> pl.DataFrame:
    stat_group = "hitting" if component == "hitter" else "pitching"
    exposure = "plate_appearances" if component == "hitter" else "batters_faced"
    return (
        stats.filter((pl.col("sport_id") == 1) & (pl.col("stat_group") == stat_group))
        .group_by("player_id")
        .agg(pl.col(exposure).sum().alias("observed_workload"))
    )


def _forecast(target: int, membership: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    snapshot = target - 1
    training_years = tuple(year for year in ELIGIBLE_TRAINING_SNAPSHOTS if year < snapshot)
    if not training_years:
        raise ValueError(f"target {target} has no eligible training fold")
    hitter_snapshots = pl.read_parquet(SOURCE / "hitter_snapshots.parquet")
    pitcher_snapshots = pl.read_parquet(SOURCE / "pitcher_snapshots.parquet")
    hitter_folds = []
    pitcher_folds = []
    for year in training_years:
        current = _stats(year)
        following = _stats(year + 1)
        hitter_folds.append(
            build_universal_hitter_opportunity_fold(
                hitter_snapshots, current, following, membership, snapshot_year=year
            )
        )
        pitcher_folds.append(
            build_universal_pitcher_opportunity_fold(
                pitcher_snapshots, current, following, membership, snapshot_year=year
            )
        )
    hitter_fit = fit_universal_hitter_opportunity_form(hitter_folds, form=PT_FORM_U)
    pitcher_fit = fit_universal_pitcher_opportunity_form(pitcher_folds, form=PT_FORM_P)
    current = _stats(snapshot)
    hitter_predictors = build_universal_hitter_opportunity_predictors(
        hitter_snapshots, current, membership, snapshot_year=snapshot
    )
    pitcher_predictors = build_universal_pitcher_opportunity_predictors(
        pitcher_snapshots, current, membership, snapshot_year=snapshot
    )
    hitter = predict_playing_time_hurdle(
        hitter_fit, build_playing_time_design(hitter_predictors, form=PT_FORM_U)
    ).select(
        "player_id",
        pl.col("predicted_any_mlb_pa_probability").alias("raw_probability"),
        pl.col("predicted_positive_mlb_pa_mean").alias("conditional_mean"),
        pl.lit(hitter_fit.nb_alpha).alias("nb_alpha"),
    )
    pitcher = predict_playing_time_hurdle(
        pitcher_fit, build_playing_time_design(pitcher_predictors, form=PT_FORM_P)
    ).select(
        "player_id",
        pl.col("predicted_any_mlb_pa_probability").alias("raw_probability"),
        pl.col("predicted_positive_mlb_pa_mean").alias("conditional_mean"),
        pl.lit(pitcher_fit.nb_alpha).alias("nb_alpha"),
    )
    outcomes = _stats(target)

    def attach(prediction: pl.DataFrame, component: str) -> pl.DataFrame:
        return prediction.join(
            _outcome(outcomes, component=component), on="player_id", how="left", validate="1:1"
        ).with_columns(
            pl.col("observed_workload").fill_null(0.0),
            (pl.col("observed_workload").fill_null(0.0) > 0).cast(pl.Int64).alias(
                "observed_active"
            ),
            pl.lit(target).alias("target_season"),
            pl.lit(",".join(map(str, training_years))).alias("training_snapshot_years"),
        )

    return attach(hitter, "hitter"), attach(pitcher, "pitcher")


def _fit_logistic_calibration(training: pl.DataFrame) -> tuple[float, float]:
    probability = np.clip(training.get_column("raw_probability").to_numpy(), 1e-8, 1 - 1e-8)
    outcome = training.get_column("observed_active").to_numpy().astype(float)
    design = np.column_stack([np.ones(len(probability)), np.log(probability / (1 - probability))])
    coefficients = np.asarray([0.0, 1.0])
    for _ in range(100):
        linear = np.clip(design @ coefficients, -30.0, 30.0)
        fitted = 1.0 / (1.0 + np.exp(-linear))
        weights = np.clip(fitted * (1.0 - fitted), 1e-8, None)
        information = design.T @ (weights[:, None] * design)
        score = design.T @ (outcome - fitted)
        step = np.linalg.solve(information, score)
        coefficients += step
        if float(np.max(np.abs(step))) < 1e-10:
            break
    if not np.all(np.isfinite(coefficients)):
        raise ValueError("rolling calibration did not converge")
    return float(coefficients[0]), float(coefficients[1])


def _apply_calibration(frame: pl.DataFrame, intercept: float, slope: float) -> pl.DataFrame:
    clipped = pl.col("raw_probability").clip(1e-8, 1 - 1e-8)
    linear = intercept + slope * (clipped / (1 - clipped)).log()
    return frame.with_columns((1 / (1 + (-linear).exp())).alias("calibrated_probability"))


def _score(frame: pl.DataFrame, column: str) -> dict[str, object]:
    return summarize_binary_probability_calibration(
        frame,
        probability_column=column,
        outcome_column="observed_active",
    )


def _rolling(component: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, object]]:
    rows = []
    yearly = []
    for target in TARGETS:
        validation = component.filter(pl.col("target_season") == target)
        if target == TARGETS[0]:
            calibrated = validation.with_columns(
                pl.col("raw_probability").alias("calibrated_probability")
            )
            intercept, slope = 0.0, 1.0
            status = "warmup_no_prior_rolling_origin"
        else:
            training = component.filter(pl.col("target_season") < target)
            intercept, slope = _fit_logistic_calibration(training)
            calibrated = _apply_calibration(validation, intercept, slope)
            status = "prior_origins_only"
        rows.append(calibrated)
        raw_score = _score(calibrated, "raw_probability")
        calibrated_score = _score(calibrated, "calibrated_probability")
        yearly.append(
            {
                "target_season": target,
                "status": status,
                "calibration_intercept": intercept,
                "calibration_slope": slope,
                "players": calibrated.height,
                "raw": raw_score,
                "calibrated": calibrated_score,
                "calibrated_minus_raw_brier": float(calibrated_score["brier"])
                - float(raw_score["brier"]),
                "calibrated_minus_raw_log_loss": float(calibrated_score["log_loss"])
                - float(raw_score["log_loss"]),
                "conditional_positive_workload": summarize_positive_workload_coverage(
                    calibrated
                ),
            }
        )
    scored = pl.concat(rows).sort("target_season", "player_id")
    evaluation = scored.filter(pl.col("target_season") > TARGETS[0])
    raw = _score(evaluation, "raw_probability")
    calibrated = _score(evaluation, "calibrated_probability")
    return scored, {
        "method": "rolling_prior-origin_logistic_intercept_slope",
        "warmup_target_excluded_from_pooled_comparison": TARGETS[0],
        "annual": yearly,
        "pooled_2023_2025": {"raw": raw, "calibrated": calibrated},
        "pooled_calibrated_minus_raw_brier": float(calibrated["brier"])
        - float(raw["brier"]),
        "pooled_calibrated_minus_raw_log_loss": float(calibrated["log_loss"])
        - float(raw["log_loss"]),
        "pooled_conditional_positive_workload": summarize_positive_workload_coverage(
            scored
        ),
    }


def main() -> int:
    membership = pl.read_parquet(MEMBERSHIP)
    hitter_frames = []
    pitcher_frames = []
    for target in TARGETS:
        hitter, pitcher = _forecast(target, membership)
        hitter_frames.append(hitter)
        pitcher_frames.append(pitcher)
    hitters, hitter_report = _rolling(pl.concat(hitter_frames))
    pitchers, pitcher_report = _rolling(pl.concat(pitcher_frames))
    tables = OUTPUT / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter": write_canonical_parquet(
            hitters,
            tables / "hitter-rolling-participation.parquet",
            table_name="hitter_rolling_participation_calibration",
        ).as_record(),
        "pitcher": write_canonical_parquet(
            pitchers,
            tables / "pitcher-rolling-participation.parquet",
            table_name="pitcher_rolling_participation_calibration",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "rolling_opportunity_probability_calibration",
        "targets": list(TARGETS),
        "hitter": hitter_report,
        "pitcher": pitcher_report,
        "production_changed": False,
        "boundaries": {
            "future_target_used_to_fit_each_calibrator": False,
            "same_snapshot_only_universe_each_year": True,
            "fanGraphs_used": False,
            "model_form": {"hitter": PT_FORM_U, "pitcher": PT_FORM_P},
            "replay_mode": "retrospective_source_reconstruction_not_vintage_archive",
        },
        "storage": storage,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                component: {
                    "brier_delta": report[component]["pooled_calibrated_minus_raw_brier"],
                    "log_loss_delta": report[component][
                        "pooled_calibrated_minus_raw_log_loss"
                    ],
                    "annual": [
                        {
                            "year": row["target_season"],
                            "brier_delta": row["calibrated_minus_raw_brier"],
                            "log_loss_delta": row["calibrated_minus_raw_log_loss"],
                        }
                        for row in report[component]["annual"]
                    ],
                }
                for component in ("hitter", "pitcher")
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
