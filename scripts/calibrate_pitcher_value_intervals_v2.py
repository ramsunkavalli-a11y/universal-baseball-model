#!/usr/bin/env python3
"""Create chronology-calibrated ranges around the leading pitcher value forecast."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.chronological_intervals import (
    add_player_stage,
    chronological_residual_intervals,
    interval_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


PREDICTION_PATH = Path("reports/generated/pitcher-role-ensemble-v2/predictions.parquet")
PANEL_PATH = Path("reports/generated/pitcher-value-panel-v2/tables/modeling-panel.parquet")
OUTPUT_ROOT = Path("reports/generated/pitcher-value-intervals-v2")
PREDICTION_COLUMN = "prediction_role_chronology_pruned_equal"


def main() -> None:
    predictions = pl.read_parquet(PREDICTION_PATH)
    panel = pl.read_parquet(PANEL_PATH).select(
        "origin_year",
        "player_id",
        pl.col("lag0__highest_level").alias("current_highest_level"),
        pl.col("lag0__bf_level__MLB").alias("current_mlb_pa"),
        "lag0__start_share",
    )
    staged = add_player_stage(
        predictions.join(
            panel,
            on=["origin_year", "player_id"],
            how="left",
            validate="1:1",
        )
    ).with_columns(
        pl.when(pl.col("lag0__start_share") >= 0.5)
        .then(pl.lit("starter"))
        .otherwise(pl.lit("reliever"))
        .alias("current_role")
    )
    broad_intervals, _ = chronological_residual_intervals(
        staged,
        prediction_column=PREDICTION_COLUMN,
    )
    role_staged = staged.rename({"player_stage": "broad_player_stage"}).with_columns(
        pl.concat_str("broad_player_stage", "current_role", separator="__").alias(
            "player_stage"
        )
    )
    intervals, calibration = chronological_residual_intervals(
        role_staged,
        prediction_column=PREDICTION_COLUMN,
    )
    overall = interval_metrics(intervals)
    broad_overall = interval_metrics(broad_intervals)
    by_stage = {
        stage: interval_metrics(
            intervals.filter(pl.col("broad_player_stage") == stage)
        )
        for stage in sorted(intervals["broad_player_stage"].unique().to_list())
    }
    by_role = {
        role: interval_metrics(intervals.filter(pl.col("current_role") == role))
        for role in sorted(intervals["current_role"].unique().to_list())
    }
    by_origin = {
        str(origin): interval_metrics(intervals.filter(pl.col("origin_year") == origin))
        for origin in sorted(intervals["origin_year"].unique().to_list())
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    prediction_artifact = write_canonical_parquet(
        intervals,
        OUTPUT_ROOT / "interval-predictions.parquet",
        table_name="pitcher_value_v2_interval_predictions",
    )
    calibration_artifact = write_canonical_parquet(
        calibration,
        OUTPUT_ROOT / "calibration-offsets.parquet",
        table_name="pitcher_value_v2_interval_offsets",
    )
    broad_artifact = write_canonical_parquet(
        broad_intervals,
        OUTPUT_ROOT / "broad-stage-sensitivity.parquet",
        table_name="pitcher_value_v2_broad_stage_interval_sensitivity",
    )
    report = {
        "schema_version": "0.1",
        "status": "chronological_pitcher_value_intervals_calibrated",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season defense-independent pitcher component WAR",
        "point_forecast": PREDICTION_COLUMN,
        "method": (
            "asymmetric residual quantiles within forecast-time MLB/upper-minors/"
            "lower-minors stage crossed with starter/reliever history, using only "
            "earlier out-of-fold seasons"
        ),
        "method_selection": {
            "selected": "player_stage_crossed_with_current_role",
            "reason": (
                "broad stage alone materially under-covered starter histories; the "
                "role-aware calibration brings starter 80% and 90% coverage close to "
                "nominal while keeping pooled coverage calibrated"
            ),
            "selected_overall": overall,
            "broad_stage_sensitivity": broad_overall,
        },
        "source_origins": sorted(staged["origin_year"].unique().to_list()),
        "scored_origins": sorted(intervals["origin_year"].unique().to_list()),
        "excluded_origin": int(staged["origin_year"].min()),
        "exclusion_reason": "no earlier out-of-fold residuals exist for calibration",
        "overall": overall,
        "by_player_stage": by_stage,
        "by_current_role": by_role,
        "by_origin": by_origin,
        "sources": {
            "predictions": {
                "path": str(PREDICTION_PATH),
                "sha256": sha256_file(PREDICTION_PATH),
            },
            "panel": {"path": str(PANEL_PATH), "sha256": sha256_file(PANEL_PATH)},
        },
        "artifacts": {
            "predictions": prediction_artifact.as_record(),
            "calibration": calibration_artifact.as_record(),
            "broad_stage_sensitivity": broad_artifact.as_record(),
        },
        "limitations": [
            "Coverage is marginal within stage, not a guarantee for one player.",
            "The range covers the current defense-independent pitcher target, not complete pitcher WAR.",
            "Cells with fewer than 200 prior errors fall back to all earlier players.",
            "The final 2026 range must use completed historical residuals without opening 2026 outcomes.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
