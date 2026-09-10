#!/usr/bin/env python3
"""Certify complete, traceable fallbacks in the current playable projection."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.fallback_coverage import audit_projection_fallbacks


ROOT = Path("reports/generated/phase2-conditional-war-paths/2026-09-08/tables")
OUTPUT = Path("docs/current-fallback-coverage-result.json")


def main() -> int:
    report = {
        "report_schema_version": "0.1",
        "status": "current_fallback_coverage_certified",
        "as_of_date": "2026-09-08",
        "hitter": audit_projection_fallbacks(
            pl.read_parquet(ROOT / "hitter_expected_war_paths.parquet"),
            component="hitter",
        ),
        "pitcher": audit_projection_fallbacks(
            pl.read_parquet(ROOT / "pitcher_expected_war_paths.parquet"),
            component="pitcher",
        ),
        "production_changed": False,
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        component: {
            "players": report[component]["players"],
            "complete_six_year_paths": report[component]["complete_six_year_paths"],
        }
        for component in ("hitter", "pitcher")
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
