#!/usr/bin/env python3
"""Freeze Tango and no-aging 2026 pitcher forecasts without 2026 outcomes."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_joint_pitcher_aging_2025 import _counterfactual_no_aging
from universal_baseball.storage import sha256_file, write_canonical_parquet


PROJECTION_ROOT = Path("reports/generated/historical-projection-paths/2025-10-15")
SKILL_ROOT = Path("reports/generated/free-agent-historical-skill-source/2025-12-31")
OUTPUT_ROOT = Path("model_artifacts/pitcher-aging-2026-confirmation-forecast-2026-09-10")
CONTRACT = Path("docs/pitcher-aging-2026-confirmation-contract.md")


def main() -> int:
    projection_path = PROJECTION_ROOT / "tables/pitcher-expected-war-paths.parquet"
    source_path = SKILL_ROOT / "tables/mlb_pitching_components.parquet"
    skill_report_path = SKILL_ROOT / "report.json"
    projections = pl.read_parquet(projection_path).filter(pl.col("season") == 2026)
    source = pl.read_parquet(source_path)
    if int(source.get_column("season").max()) > 2025:
        raise ValueError("forecast freeze refuses any 2026 outcome season")
    reference = source.filter(pl.col("season") == 2025)
    skill_report = json.loads(skill_report_path.read_text(encoding="utf-8"))
    runs_per_win = float(skill_report["reference_environment"]["runs_per_win"])
    no_aging = _counterfactual_no_aging(
        projections, reference, runs_per_win=runs_per_win
    )
    unchanged = [
        "player_id", "expected_mlb_bf", "mlb_active_probability",
        "conditional_mlb_bf", "starter_probability_if_active",
        "swingman_probability_if_active", "reliever_probability_if_active",
        "replacement_runs_per_800",
    ]
    for column in unchanged:
        if not projections.get_column(column).equals(no_aging.get_column(column)):
            raise ValueError(f"non-age confirmation field changed: {column}")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    storage = {
        "tango": write_canonical_parquet(
            projections, OUTPUT_ROOT / "tango-aging.parquet",
            table_name="pitcher_aging_2026_tango_forecast",
        ).as_record(),
        "no_aging": write_canonical_parquet(
            no_aging, OUTPUT_ROOT / "no-aging.parquet",
            table_name="pitcher_aging_2026_no_aging_forecast",
        ).as_record(),
    }
    runner = Path(__file__).relative_to(Path.cwd())
    report = {
        "report_schema_version": "0.1",
        "status": "frozen_before_2026_outcome_access",
        "forecast_as_of_date": "2025-10-15",
        "target_season": 2026,
        "players": projections.height,
        "tango_expected_war": float(projections.get_column("expected_war").sum()),
        "no_aging_expected_war": float(no_aging.get_column("expected_war").sum()),
        "2026_outcomes_read": False,
        "runner_path": runner.as_posix(), "runner_sha256": sha256_file(runner),
        "contract_path": CONTRACT.as_posix(), "contract_sha256": sha256_file(CONTRACT),
        "source_files": {
            path.as_posix(): sha256_file(path)
            for path in (projection_path, source_path, skill_report_path)
        },
        "storage": storage,
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
