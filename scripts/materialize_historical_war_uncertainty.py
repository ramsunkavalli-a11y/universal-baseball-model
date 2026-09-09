#!/usr/bin/env python3
"""Materialize the existing Phase 1 WAR range for a historical checkpoint."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.storage import sha256_file, write_canonical_parquet
from universal_baseball.war_uncertainty_paths import (
    CENTRAL_COVERAGE,
    UNCERTAINTY_MODEL_ID,
    build_component_war_uncertainty,
    build_whole_player_war_uncertainty,
)


REFERENCE_REPORTS = {
    date(2025, 3, 27): Path(
        "reports/generated/free-agent-historical-skill-source/2025-12-31/report.json"
    ),
    date(2025, 10, 15): Path(
        "reports/generated/current-mlb-skill-source/2026-09-08/report.json"
    ),
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    return parser.parse_args()


def _summary(frame: pl.DataFrame) -> dict[str, float]:
    widths = frame.get_column("projected_war_upper") - frame.get_column(
        "projected_war_lower"
    )
    return {
        "rows": frame.height,
        "mean_war": float(frame.get_column("projected_war_mean").sum()),
        "median_reference_width": float(widths.median()),
        "p90_reference_width": float(widths.quantile(0.9)),
        "opportunity_variance_share": float(
            frame.get_column("opportunity_war_variance").sum()
            / frame.get_column("annual_war_variance").sum()
        ),
    }


def main() -> int:
    args = _args()
    if args.as_of_date not in REFERENCE_REPORTS:
        raise ValueError("historical uncertainty has no declared run environment")
    projection_root = (
        Path("reports/generated/historical-projection-paths")
        / args.as_of_date.isoformat()
    )
    hitter_path = projection_root / "tables/hitter-expected-war-paths.parquet"
    pitcher_path = projection_root / "tables/pitcher-expected-war-paths.parquet"
    reference_path = REFERENCE_REPORTS[args.as_of_date]
    reference = json.loads(reference_path.read_text(encoding="utf-8"))[
        "reference_environment"
    ]
    runs_per_win = float(reference["runs_per_win"])
    hitters = build_component_war_uncertainty(
        pl.read_parquet(hitter_path),
        component="hitter",
        conditional_workload_column="conditional_mlb_pa",
        conditional_workload_variance_column="conditional_mlb_pa_variance",
        conditional_war_rate_column="conditional_war_per_600_pa",
        workload_unit=600.0,
        runs_per_win=runs_per_win,
    )
    pitchers = build_component_war_uncertainty(
        pl.read_parquet(pitcher_path),
        component="pitcher",
        conditional_workload_column="conditional_mlb_bf",
        conditional_workload_variance_column="conditional_mlb_bf_variance",
        conditional_war_rate_column="conditional_war_per_800_bf",
        workload_unit=800.0,
        runs_per_win=runs_per_win,
    )
    components = pl.concat([hitters, pitchers]).sort(
        ["player_id", "season", "projection_component"]
    )
    whole = build_whole_player_war_uncertainty(components)
    output = (
        Path("reports/generated/historical-war-uncertainty")
        / args.as_of_date.isoformat()
    )
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "components": write_canonical_parquet(
            components,
            tables / "component-war-uncertainty.parquet",
            table_name="historical_component_war_uncertainty",
        ).as_record(),
        "whole_player": write_canonical_parquet(
            whole,
            tables / "whole-player-war-uncertainty.parquet",
            table_name="historical_whole_player_war_uncertainty",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_phase1_war_uncertainty",
        "as_of_date": args.as_of_date.isoformat(),
        "uncertainty_model_id": UNCERTAINTY_MODEL_ID,
        "central_reference_coverage": CENTRAL_COVERAGE,
        "reference_environment_season": int(reference["season"]),
        "runs_per_win": runs_per_win,
        "hitter": _summary(hitters),
        "pitcher": _summary(pitchers),
        "whole_player": _summary(whole),
        "interpretation": (
            "moment-based Phase 1 reference range; not empirically calibrated "
            "coverage or a correlated career simulation"
        ),
        "boundaries": {
            "model_changed_from_current_phase1_uncertainty": False,
            "cross_season_covariance_modeled": False,
            "hitter_pitcher_covariance_modeled": False,
            "future_team_depth_used": False,
        },
        "source_files": {
            hitter_path.as_posix(): sha256_file(hitter_path),
            pitcher_path.as_posix(): sha256_file(pitcher_path),
            reference_path.as_posix(): sha256_file(reference_path),
        },
        "storage": storage,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "storage"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
