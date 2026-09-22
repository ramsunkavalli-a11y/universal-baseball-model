#!/usr/bin/env python3
"""Create chronology-calibrated uncertainty ranges around hitter value forecasts."""

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
from universal_baseball.storage import write_canonical_parquet


PREDICTION_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-value-intervals-v2")


def main() -> None:
    predictions = pl.read_parquet(PREDICTION_PATH)
    panel = pl.read_parquet(PANEL_PATH).select(
        "origin_year",
        "player_id",
        pl.col("lag0__highest_level").alias("current_highest_level"),
        pl.col("lag0__pa_level__MLB").alias("current_mlb_pa"),
    )
    joined = predictions.join(panel, on=["origin_year", "player_id"], how="left")
    staged = add_player_stage(joined)
    intervals, calibration = chronological_residual_intervals(
        staged,
        prediction_column="prediction_candidate_equal_mean",
    )
    overall = interval_metrics(intervals)
    by_stage = {
        stage: interval_metrics(intervals.filter(pl.col("player_stage") == stage))
        for stage in sorted(intervals["player_stage"].unique().to_list())
    }
    by_origin = {
        str(origin): interval_metrics(intervals.filter(pl.col("origin_year") == origin))
        for origin in sorted(intervals["origin_year"].unique().to_list())
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    prediction_artifact = write_canonical_parquet(
        intervals,
        OUTPUT_ROOT / "interval-predictions.parquet",
        table_name="hitter_value_v2_interval_predictions",
    )
    calibration_artifact = write_canonical_parquet(
        calibration,
        OUTPUT_ROOT / "calibration-offsets.parquet",
        table_name="hitter_value_v2_calibration_offsets",
    )
    report = {
        "schema_version": "0.1",
        "status": "chronological_hitter_value_intervals_calibrated",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "method": (
            "asymmetric residual quantiles within forecast-time player stage, "
            "using only earlier out-of-fold seasons"
        ),
        "first_scored_origin": int(intervals["origin_year"].min()),
        "excluded_origin": 2017,
        "exclusion_reason": "no earlier out-of-fold residuals exist for calibration",
        "overall": overall,
        "by_player_stage": by_stage,
        "by_origin": by_origin,
        "artifacts": {
            "predictions": prediction_artifact.as_record(),
            "calibration": calibration_artifact.as_record(),
        },
        "limitations": [
            "Coverage is marginal within stage, not a guarantee for one player.",
            "The range covers batting-plus-replacement WAR, not defense or baserunning.",
            "A complete 2025 source season is still required before issuing 2026 ranges.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
