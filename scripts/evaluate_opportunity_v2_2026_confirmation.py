#!/usr/bin/env python3
"""Evaluate the frozen 2026 opportunity forecast after the regular season ends."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.opportunity_v2_confirmation import (
    evaluate_opportunity_confirmation,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


TARGET_SEASON = 2026


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forecast-package",
        type=Path,
        default=Path(
            "model_artifacts/opportunity-v2-2026-confirmation-forecast-2026-09-09"
        ),
    )
    parser.add_argument("--target-stats", type=Path, required=True)
    parser.add_argument("--schedule-report", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/opportunity-v2-2026-confirmation-result"),
    )
    return parser.parse_args()


def _verify_forecast_package(root: Path) -> dict[str, object]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["target_outcomes_included"] is not False:
        raise ValueError("confirmation forecast package already contains target outcomes")
    for relative_path, record in manifest["files"].items():
        path = root / relative_path
        if path.stat().st_size != record["bytes"] or sha256_file(path) != record["sha256"]:
            raise ValueError(f"confirmation forecast package hash mismatch: {relative_path}")
    return manifest


def _require_completed_regular_season(path: Path) -> dict[str, object]:
    report = json.loads(path.read_text(encoding="utf-8"))
    schedule = report.get("schedule")
    if not isinstance(schedule, dict):
        raise ValueError("schedule report lacks schedule evidence")
    completed = int(schedule["completed_league_games"])
    scheduled = int(schedule["scheduled_league_games"])
    remaining = float(schedule["remaining_fraction"])
    if scheduled <= 0 or completed != scheduled or abs(remaining) > 1e-12:
        raise ValueError("2026 regular season is not complete; confirmation remains locked")
    return report


def _targets(
    stats: pl.DataFrame,
    universe: pl.DataFrame,
    *,
    group: str,
    count_column: str,
    output_column: str,
) -> pl.DataFrame:
    observed = stats.filter(
        (pl.col("season") == TARGET_SEASON)
        & (pl.col("stat_group") == group)
        & (pl.col("sport_id") == 1)
    ).group_by("player_id").agg(
        pl.col(count_column).sum().cast(pl.Int64).alias(output_column)
    )
    return (
        universe.select("player_id")
        .join(observed, on="player_id", how="left", validate="1:1")
        .with_columns(pl.col(output_column).fill_null(0).cast(pl.Int64))
        .sort("player_id")
    )


def main() -> int:
    args = _args()
    manifest = _verify_forecast_package(args.forecast_package)
    schedule_report = _require_completed_regular_season(args.schedule_report)
    stats = pl.read_parquet(args.target_stats)
    hitter_selected = pl.read_parquet(args.forecast_package / "hitter-selected.parquet")
    pitcher_selected = pl.read_parquet(args.forecast_package / "pitcher-selected.parquet")
    hitter_targets = _targets(
        stats,
        hitter_selected,
        group="hitting",
        count_column="plate_appearances",
        output_column="observed_mlb_pa",
    )
    pitcher_targets = _targets(
        stats,
        pitcher_selected,
        group="pitching",
        count_column="batters_faced",
        output_column="observed_mlb_bf",
    )
    hitter = evaluate_opportunity_confirmation(
        hitter_selected,
        pl.read_parquet(
            args.forecast_package / "hitter-parametric-baseline.parquet"
        ),
        pl.read_parquet(args.forecast_package / "hitter-incumbent.parquet"),
        hitter_targets,
        component="hitter",
        unit="pa",
    )
    pitcher = evaluate_opportunity_confirmation(
        pitcher_selected,
        pl.read_parquet(
            args.forecast_package / "pitcher-parametric-baseline.parquet"
        ),
        pl.read_parquet(args.forecast_package / "pitcher-incumbent.parquet"),
        pitcher_targets,
        component="pitcher",
        unit="bf",
    )
    output = args.output_root
    output.mkdir(parents=True, exist_ok=True)
    metrics = pl.concat(
        [
            hitter.metrics.with_columns(pl.lit("hitter").alias("component")),
            pitcher.metrics.with_columns(pl.lit("pitcher").alias("component")),
        ],
        how="diagonal_relaxed",
    ).sort(["component", "model"])
    storage = {
        "metrics": write_canonical_parquet(
            metrics,
            output / "confirmation-metrics.parquet",
            table_name="opportunity_v2_2026_confirmation_metrics",
        ).as_record(),
        "hitter_targets": write_canonical_parquet(
            hitter_targets,
            output / "hitter-targets.parquet",
            table_name="opportunity_v2_2026_hitter_targets",
        ).as_record(),
        "pitcher_targets": write_canonical_parquet(
            pitcher_targets,
            output / "pitcher-targets.parquet",
            table_name="opportunity_v2_2026_pitcher_targets",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "opportunity_v2_2026_protected_confirmation",
        "target_season": TARGET_SEASON,
        "forecast_package_type": manifest["package_type"],
        "schedule_report": str(args.schedule_report),
        "schedule_capture_sha256": schedule_report["schedule"]["capture"][
            "response_sha256"
        ],
        "target_stats_sha256": sha256_file(args.target_stats),
        "component_results": {
            "hitter": {"confirmed": hitter.confirmed, "gates": hitter.gates},
            "pitcher": {"confirmed": pitcher.confirmed, "gates": pitcher.gates},
        },
        "subgroups_can_override_gate": False,
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

