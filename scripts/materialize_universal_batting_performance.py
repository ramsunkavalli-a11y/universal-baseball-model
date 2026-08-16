#!/usr/bin/env python
"""Combine certified 2024 MLB and affiliated Performance artifacts.

This step performs no source/network work and no cross-level translation. It
simply materializes one universal observed-Performance surface at actual-league
grain so Current Talent can consume a common contract without recomputing the
source layers.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import polars as pl

from universal_baseball.storage import write_canonical_parquet
from universal_baseball.universal_performance import combine_universal_batting_performance


SEASON = 2024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--affiliated-root", type=Path, required=True)
    parser.add_argument("--mlb-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/universal-batting-performance-2024"),
    )
    return parser.parse_args()


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(root.rglob(filename))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {filename} below {root}; found {[str(path) for path in matches]}"
        )
    return matches[0]


def _duckdb_validate(summary_path: Path, profile_path: Path, values_path: Path) -> dict[str, int]:
    connection = duckdb.connect()
    try:
        summary_rows = int(connection.execute("SELECT count(*) FROM read_parquet(?)", [str(summary_path)]).fetchone()[0])
        summary_unique = int(connection.execute(
            "SELECT count(*) FROM (SELECT DISTINCT season, league_id, player_id FROM read_parquet(?))",
            [str(summary_path)],
        ).fetchone()[0])
        profile_rows = int(connection.execute("SELECT count(*) FROM read_parquet(?)", [str(profile_path)]).fetchone()[0])
        profile_unique = int(connection.execute(
            "SELECT count(*) FROM (SELECT DISTINCT season, league_id, player_id, core_bin FROM read_parquet(?))",
            [str(profile_path)],
        ).fetchone()[0])
        value_rows = int(connection.execute("SELECT count(*) FROM read_parquet(?)", [str(values_path)]).fetchone()[0])
        value_unique = int(connection.execute(
            "SELECT count(*) FROM (SELECT DISTINCT season, league_id, core_bin FROM read_parquet(?))",
            [str(values_path)],
        ).fetchone()[0])
    finally:
        connection.close()
    if (summary_rows, profile_rows, value_rows) != (summary_unique, profile_unique, value_unique):
        raise RuntimeError("universal Performance parquet violates canonical-grain uniqueness")
    return {
        "summary_rows": summary_rows,
        "summary_unique_keys": summary_unique,
        "profile_rows": profile_rows,
        "profile_unique_keys": profile_unique,
        "bin_value_rows": value_rows,
        "bin_value_unique_keys": value_unique,
    }


def main() -> int:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)

    affiliated_summary_path = _find_one(
        args.affiliated_root, "batting_performance_summary_2024_affiliated.parquet"
    )
    affiliated_profile_path = _find_one(
        args.affiliated_root, "batting_performance_bins_2024_affiliated.parquet"
    )
    affiliated_values_path = _find_one(
        args.affiliated_root, "league_bin_values_2024_affiliated.parquet"
    )
    mlb_summary_path = _find_one(args.mlb_root, "batting_performance_summary_2024_mlb.parquet")
    mlb_profile_path = _find_one(args.mlb_root, "batting_performance_bins_2024_mlb.parquet")
    mlb_values_path = _find_one(args.mlb_root, "league_bin_values_2024_mlb.parquet")

    summary, profile, values, metrics = combine_universal_batting_performance(
        pl.read_parquet(affiliated_summary_path),
        pl.read_parquet(affiliated_profile_path),
        pl.read_parquet(affiliated_values_path),
        pl.read_parquet(mlb_summary_path),
        pl.read_parquet(mlb_profile_path),
        pl.read_parquet(mlb_values_path),
        expected_season=SEASON,
    )

    summary_path = tables / "batting_performance_summary_2024_universal.parquet"
    profile_path = tables / "batting_performance_bins_2024_universal.parquet"
    values_path = tables / "league_bin_values_2024_universal.parquet"
    summary_artifact = write_canonical_parquet(summary, summary_path, table_name="batting_performance_summary_universal")
    profile_artifact = write_canonical_parquet(profile, profile_path, table_name="batting_performance_bins_universal")
    values_artifact = write_canonical_parquet(values, values_path, table_name="league_performance_bin_values_universal")
    duckdb_metrics = _duckdb_validate(summary_path, profile_path, values_path)

    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "coverage": "MLB through affiliated Rookie/complex and DSL at actual-league grain",
        "metrics": metrics,
        "storage": {
            "summary": summary_artifact.as_record(),
            "profile": profile_artifact.as_record(),
            "bin_values": values_artifact.as_record(),
            "duckdb": duckdb_metrics,
        },
        "interpretation": (
            "Universal observed Performance only. Level translation, Current Talent, "
            "Projection, role/playing time, defense, WAR, and rankings remain downstream."
        ),
    }
    (args.output_root / "universal_batting_performance_2024.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    combined = metrics["combined_contract"]
    lines = [
        "# Universal batting Performance materialization — 2024",
        "",
        f"- Actual leagues: {metrics['actual_league_count']:,}",
        f"- Level groups: {metrics['level_group_count']:,} ({', '.join(metrics['level_groups'])})",
        f"- Player × league × season rows: {combined['summary_row_count']:,}",
        f"- Plate appearances: {combined['total_plate_appearances']:,}",
        f"- Core Performance events: {combined['total_core_profile_events']:,}",
        f"- Core-profile coverage: {combined['core_profile_coverage_rate']:.2%}",
        f"- Contacts: {combined['total_contact_events']:,}",
        f"- Unknown contacts: {combined['unknown_contact_count']:,} ({combined['unknown_contact_rate']:.3%})",
        f"- DuckDB unique summary keys: {duckdb_metrics['summary_unique_keys']:,}/{duckdb_metrics['summary_rows']:,}",
        "",
        "This is a common observed-Performance surface, not a cross-level talent scale.",
    ]
    text = "\n".join(lines) + "\n"
    (args.output_root / "universal_batting_performance_2024.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
