#!/usr/bin/env python3
"""Audit frozen March 2025 WAR intervals against completed 2025 outcomes."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file
from universal_baseball.war_uncertainty_validation import (
    summarize_binary_probability_calibration,
    summarize_interval_coverage,
    summarize_named_slices,
    summarize_normal_reference_calibration,
)


ROOT = Path("reports/generated")
CHECKPOINT = "2025-03-27"
TARGET_SEASON = 2025


def _component_frame(component: str) -> pl.DataFrame:
    uncertainty_path = ROOT / "historical-war-uncertainty" / CHECKPOINT / "tables/component-war-uncertainty.parquet"
    score_path = ROOT / "historical-war-score" / CHECKPOINT / f"{component}-neutral-war-scores.parquet"
    path_path = ROOT / "historical-projection-paths" / CHECKPOINT / "tables" / f"{component}-expected-war-paths.parquet"
    workload = "pa" if component == "hitter" else "bf"
    expected_column = f"expected_mlb_{workload}"
    observed_column = "batting_plate_appearances" if component == "hitter" else "pitching_batters_faced"
    paths = pl.read_parquet(path_path).filter(pl.col("season") == TARGET_SEASON)
    scores = pl.read_parquet(score_path)
    uncertainty = pl.read_parquet(uncertainty_path).filter(
        (pl.col("season") == TARGET_SEASON)
        & (pl.col("projection_component") == component)
    )
    metadata = [
        "player_id", expected_column, "mlb_active_probability", "coverage_tier"
    ]
    if component == "pitcher":
        metadata.append("projected_role")
    result = uncertainty.join(
        scores.select("player_id", observed_column, "observed_neutral_war"),
        on="player_id",
        how="inner",
        validate="1:1",
    ).join(paths.select(metadata), on="player_id", how="inner", validate="1:1")
    if result.height != uncertainty.height:
        raise ValueError(f"{component} coverage join changed the frozen universe")
    thresholds = [-float("inf"), 1.0, 100.0, 300.0, float("inf")]
    labels = ["<1", "1-99", "100-299", "300+"]
    return result.with_columns(
        (pl.col(observed_column) > 0).cast(pl.String).replace(
            {"true": "observed_active", "false": "observed_inactive"}
        ).alias("observed_activity"),
        (pl.col(observed_column) > 0).cast(pl.Int64).alias("observed_active"),
        pl.col(expected_column).cut(thresholds[1:-1], labels=labels).alias(
            "expected_workload_band"
        ),
    )


def _whole_player_frame() -> pl.DataFrame:
    uncertainty_path = ROOT / "historical-war-uncertainty" / CHECKPOINT / "tables/whole-player-war-uncertainty.parquet"
    score_path = ROOT / "historical-war-score" / CHECKPOINT / "whole-player-neutral-war-scores.parquet"
    hitter_score = pl.read_parquet(
        ROOT / "historical-war-score" / CHECKPOINT / "hitter-neutral-war-scores.parquet"
    ).select("player_id", "batting_plate_appearances")
    pitcher_score = pl.read_parquet(
        ROOT / "historical-war-score" / CHECKPOINT / "pitcher-neutral-war-scores.parquet"
    ).select("player_id", "pitching_batters_faced")
    uncertainty = pl.read_parquet(uncertainty_path).filter(pl.col("season") == TARGET_SEASON)
    score = pl.read_parquet(score_path)
    result = uncertainty.join(score, on="player_id", how="inner", validate="1:1").join(
        hitter_score, on="player_id", how="left", validate="1:1"
    ).join(pitcher_score, on="player_id", how="left", validate="1:1").with_columns(
        pl.col("batting_plate_appearances").fill_null(0),
        pl.col("pitching_batters_faced").fill_null(0),
    ).with_columns(
        (
            (pl.col("batting_plate_appearances") > 0)
            | (pl.col("pitching_batters_faced") > 0)
        ).cast(pl.String).replace(
            {"true": "observed_active", "false": "observed_inactive"}
        ).alias("observed_activity")
    )
    if result.height != uncertainty.height:
        raise ValueError("whole-player coverage join changed the frozen universe")
    return result


def main() -> int:
    projection_report_path = ROOT / "historical-projection-paths" / CHECKPOINT / "report.json"
    projection_report = json.loads(projection_report_path.read_text(encoding="utf-8"))
    if projection_report["boundaries"]["2025_outcomes_used"]:
        raise ValueError("forecast artifact claims target-season outcome use")

    components: dict[str, object] = {}
    source_paths = [
        projection_report_path,
        ROOT
        / "historical-war-uncertainty"
        / CHECKPOINT
        / "tables/component-war-uncertainty.parquet",
        ROOT
        / "historical-war-uncertainty"
        / CHECKPOINT
        / "tables/whole-player-war-uncertainty.parquet",
        ROOT
        / "historical-war-score"
        / CHECKPOINT
        / "hitter-neutral-war-scores.parquet",
        ROOT
        / "historical-war-score"
        / CHECKPOINT
        / "pitcher-neutral-war-scores.parquet",
        ROOT
        / "historical-war-score"
        / CHECKPOINT
        / "whole-player-neutral-war-scores.parquet",
        ROOT
        / "historical-projection-paths"
        / CHECKPOINT
        / "tables/hitter-expected-war-paths.parquet",
        ROOT
        / "historical-projection-paths"
        / CHECKPOINT
        / "tables/pitcher-expected-war-paths.parquet",
    ]
    for component in ("hitter", "pitcher"):
        frame = _component_frame(component)
        slices = {
            column: summarize_named_slices(frame, slice_column=column)
            for column in (
                "observed_activity",
                "expected_workload_band",
                "coverage_tier",
                *(("projected_role",) if component == "pitcher" else ()),
            )
        }
        components[component] = {
            "all": summarize_interval_coverage(frame),
            "normal_reference_calibration": summarize_normal_reference_calibration(frame),
            "forecast_participation_calibration": summarize_binary_probability_calibration(
                frame,
                probability_column="mlb_active_probability",
                outcome_column="observed_active",
            ),
            "slices": slices,
        }
    whole = _whole_player_frame()
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_2025_war_uncertainty_coverage_audit",
        "checkpoint_date": CHECKPOINT,
        "target_season": TARGET_SEASON,
        "nominal_central_coverage": 0.80,
        "hitter": components["hitter"],
        "pitcher": components["pitcher"],
        "whole_player": {
            "all": summarize_interval_coverage(whole),
            "normal_reference_calibration": summarize_normal_reference_calibration(whole),
            "slices": {
                "observed_activity": summarize_named_slices(
                    whole, slice_column="observed_activity"
                )
            },
        },
        "decision": "diagnostic_only_no_2025_tuning",
        "boundaries": {
            "2025_outcomes_used_by_forecast": False,
            "retrospective_event_cutoff_not_vintage_information_set": True,
            "same_neutral_war_definition": True,
            "zero_outcomes_retained": True,
            "intervals_clipped": False,
            "cross_season_calibration_tested": False,
            "published_war_calibration_tested": False,
        },
        "source_files": {
            path.as_posix(): sha256_file(path)
            for path in source_paths
        },
    }
    output = ROOT / "historical-war-uncertainty-coverage" / CHECKPOINT
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
