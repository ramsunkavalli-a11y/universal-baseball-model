#!/usr/bin/env python3
"""Calibrate intervals around the selected combined hitter value forecast."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.chronological_intervals import (
    chronological_residual_intervals,
    interval_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


PREDICTION_PATH = Path(
    "reports/generated/hitter-catcher-defense-value-v2/"
    "chronological-predictions.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-full-stack-intervals-v2")
PREDICTION_COLUMN = (
    "prediction_total_chronological_skill_pa_scaled_opportunity"
)


def main() -> None:
    source = pl.read_parquet(PREDICTION_PATH).with_columns(
        pl.col("actual_partial_war_with_catcher").alias("actual_component_war")
    )
    expanding_intervals, expanding_calibration = chronological_residual_intervals(
        source,
        prediction_column=PREDICTION_COLUMN,
    )
    origins = sorted(source["origin_year"].unique().to_list())
    recency_frames: list[pl.DataFrame] = []
    recency_calibrations: list[pl.DataFrame] = []
    for prior_origin, test_origin in zip(origins[:-1], origins[1:], strict=True):
        pair = source.filter(
            pl.col("origin_year").is_in([prior_origin, test_origin])
        )
        pair_intervals, pair_calibration = chronological_residual_intervals(
            pair,
            prediction_column=PREDICTION_COLUMN,
        )
        recency_frames.append(pair_intervals)
        recency_calibrations.append(pair_calibration)
    intervals = pl.concat(recency_frames).sort(["origin_year", "player_id"])
    calibration = pl.concat(recency_calibrations).sort(
        ["test_origin", "player_stage", "confidence"]
    )
    overall = interval_metrics(intervals)
    expanding_overall = interval_metrics(expanding_intervals)
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
        table_name="hitter_full_stack_interval_predictions_v2",
    )
    calibration_artifact = write_canonical_parquet(
        calibration,
        OUTPUT_ROOT / "calibration-offsets.parquet",
        table_name="hitter_full_stack_interval_offsets_v2",
    )
    expanding_artifact = write_canonical_parquet(
        expanding_intervals,
        OUTPUT_ROOT / "expanding-history-sensitivity.parquet",
        table_name="hitter_full_stack_expanding_interval_sensitivity_v2",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_full_stack_intervals_calibrated",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": (
            "batting plus replacement plus position plus baserunning plus "
            "catcher-defense WAR"
        ),
        "method": (
            "asymmetric quantiles of the immediately preceding whole-stack out-of-fold "
            "season, calibrated within forecast-time player stage when at least 200 rows exist"
        ),
        "method_selection": {
            "selected": "most_recent_prior_origin",
            "reason": (
                "the modern stack is nonstationary and recency calibration was closer "
                "to nominal coverage than pooling all earlier modern origins"
            ),
            "selected_overall": overall,
            "expanding_history_sensitivity": expanding_overall,
        },
        "source_origins": sorted(source["origin_year"].unique().to_list()),
        "scored_origins": sorted(intervals["origin_year"].unique().to_list()),
        "first_origin_excluded": int(source["origin_year"].min()),
        "exclusion_reason": "no earlier comparable whole-stack residuals exist",
        "overall": overall,
        "by_player_stage": by_stage,
        "by_origin": by_origin,
        "sources": {
            "predictions": {
                "path": str(PREDICTION_PATH),
                "sha256": sha256_file(PREDICTION_PATH),
            }
        },
        "artifacts": {
            "predictions": prediction_artifact.as_record(),
            "calibration": calibration_artifact.as_record(),
            "expanding_history_sensitivity": expanding_artifact.as_record(),
        },
        "limitations": [
            "Comparable public catcher-component history limits this calibration to modern target seasons.",
            "Only the 2024 and 2025 target seasons can be scored because 2023 supplies the first calibration residuals.",
            "Coverage is marginal within player stage, not a guarantee for one player.",
            "The final 2026 range must be fit from all available 2023-2025 residuals without opening 2026 outcomes.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
