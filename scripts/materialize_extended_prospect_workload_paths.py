#!/usr/bin/env python3
"""Build extended mature post-debut workload paths from official sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_outcome_quality import (
    build_post_debut_workload_paths,
)
from universal_baseball.storage import write_canonical_parquet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root", type=Path,
        default=Path("reports/generated/career-mlb-outcome-inventory-2009-2025"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/prospect-outcome-quality-2009-2025"),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/career-workload-path-extension-result.json"),
    )
    args = parser.parse_args()
    tables = args.source_root / "tables"
    people = pl.read_parquet(tables / "people-debut-dates.parquet")
    hitter = build_post_debut_workload_paths(
        people,
        pl.read_parquet(tables / "mlb_batting_2009_2025.parquet"),
        player_type="hitter",
    )
    pitcher = build_post_debut_workload_paths(
        people,
        pl.read_parquet(tables / "mlb_pitching_2009_2025.parquet"),
        player_type="pitcher",
    )
    paths = pl.concat([hitter, pitcher], how="vertical_relaxed")
    args.output_root.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        paths,
        args.output_root / "post-debut-workload-paths.parquet",
        table_name="extended_prospect_post_debut_workload_paths",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "extended_mature_workload_paths_complete",
        "source_seasons": [2009, 2025],
        "complete_debut_years": [2009, 2020],
        "players": {"hitter": hitter.height, "pitcher": pitcher.height},
        "storage": storage,
        "boundaries": {
            "exact_official_debut_dates": True,
            "six_calendar_year_paths": True,
            "shortened_2020_scaled_162_over_60": True,
            "current_2026_outcomes_used": False,
            "current_values_changed": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
