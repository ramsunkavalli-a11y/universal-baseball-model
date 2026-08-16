#!/usr/bin/env python
"""Combine certified level artifacts into one affiliated batting Performance set.

Expected input is a directory containing the five 2024 level artifacts produced
by ``build_batting_performance_level_poc_v2.py``. Files may be nested (as they
are after ``actions/download-artifact``); each canonical table is discovered
recursively by filename pattern.

The script performs no source/network work. It is the final deterministic
materialization step after each level has independently passed its source,
participant-authority, calibration, and storage gates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import polars as pl

from universal_baseball.performance_materialization import (
    combine_batting_performance_frames,
)
from universal_baseball.storage import write_canonical_parquet


SEASON = 2024
EXPECTED_LEVEL_SLUGS = {"aaa", "aa", "aplus", "a", "rk"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("level-artifacts"),
        help="root containing downloaded per-level Performance artifacts",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/affiliated-batting-performance-2024"),
    )
    return parser.parse_args()


def _discover(input_root: Path, stem: str) -> list[Path]:
    paths = sorted(input_root.rglob(f"{stem}_{SEASON}_*.parquet"))
    if not paths:
        raise RuntimeError(f"no {stem} files found below {input_root}")
    return paths


def _slugs(paths: list[Path], stem: str) -> set[str]:
    prefix = f"{stem}_{SEASON}_"
    return {
        path.stem.removeprefix(prefix)
        for path in paths
    }


def _validate_discovery(
    summaries: list[Path], profiles: list[Path], values: list[Path]
) -> None:
    for label, paths, stem in (
        ("summary", summaries, "batting_performance_summary"),
        ("profile", profiles, "batting_performance_bins"),
        ("bin-value", values, "league_bin_values"),
    ):
        slugs = _slugs(paths, stem)
        if slugs != EXPECTED_LEVEL_SLUGS:
            raise RuntimeError(
                f"{label} level artifact coverage mismatch: "
                f"observed={sorted(slugs)}, expected={sorted(EXPECTED_LEVEL_SLUGS)}"
            )
        if len(paths) != len(EXPECTED_LEVEL_SLUGS):
            raise RuntimeError(
                f"{label} discovery found duplicate artifacts: {[str(path) for path in paths]}"
            )


def _duckdb_validate(
    summary_path: Path, profile_path: Path, values_path: Path
) -> dict[str, int]:
    connection = duckdb.connect()
    try:
        summary_rows = int(
            connection.execute(
                "SELECT count(*) FROM read_parquet(?)", [str(summary_path)]
            ).fetchone()[0]
        )
        summary_unique = int(
            connection.execute(
                "SELECT count(*) FROM (SELECT DISTINCT season, league_id, player_id "
                "FROM read_parquet(?))",
                [str(summary_path)],
            ).fetchone()[0]
        )
        profile_rows = int(
            connection.execute(
                "SELECT count(*) FROM read_parquet(?)", [str(profile_path)]
            ).fetchone()[0]
        )
        profile_unique = int(
            connection.execute(
                "SELECT count(*) FROM (SELECT DISTINCT season, league_id, player_id, core_bin "
                "FROM read_parquet(?))",
                [str(profile_path)],
            ).fetchone()[0]
        )
        value_rows = int(
            connection.execute(
                "SELECT count(*) FROM read_parquet(?)", [str(values_path)]
            ).fetchone()[0]
        )
        value_unique = int(
            connection.execute(
                "SELECT count(*) FROM (SELECT DISTINCT season, league_id, core_bin "
                "FROM read_parquet(?))",
                [str(values_path)],
            ).fetchone()[0]
        )
    finally:
        connection.close()

    if summary_rows != summary_unique:
        raise RuntimeError("combined summary fails canonical-grain uniqueness")
    if profile_rows != profile_unique:
        raise RuntimeError("combined profile fails canonical-grain uniqueness")
    if value_rows != value_unique:
        raise RuntimeError("combined bin values fail canonical-grain uniqueness")
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

    summary_paths = _discover(args.input_root, "batting_performance_summary")
    profile_paths = _discover(args.input_root, "batting_performance_bins")
    value_paths = _discover(args.input_root, "league_bin_values")
    _validate_discovery(summary_paths, profile_paths, value_paths)

    summary, profile, values, metrics = combine_batting_performance_frames(
        [pl.read_parquet(path) for path in summary_paths],
        [pl.read_parquet(path) for path in profile_paths],
        [pl.read_parquet(path) for path in value_paths],
        expected_season=SEASON,
        require_all_certified_leagues=True,
    )

    summary_path = tables / "batting_performance_summary_2024_affiliated.parquet"
    profile_path = tables / "batting_performance_bins_2024_affiliated.parquet"
    values_path = tables / "league_bin_values_2024_affiliated.parquet"
    summary_artifact = write_canonical_parquet(
        summary, summary_path, table_name="batting_performance_summary_affiliated"
    )
    profile_artifact = write_canonical_parquet(
        profile, profile_path, table_name="batting_performance_bins_affiliated"
    )
    values_artifact = write_canonical_parquet(
        values, values_path, table_name="league_performance_bin_values_affiliated"
    )
    duckdb_metrics = _duckdb_validate(summary_path, profile_path, values_path)

    if metrics["unvalued_core_event_count"]:
        raise RuntimeError("combined affiliated materialization contains unvalued core events")
    if metrics["uncertified_or_missing_bin_value_player_rows"]:
        raise RuntimeError("uncertified bin values reached combined materialization")

    payload = {
        "report_schema_version": 1,
        "scope": {
            "season": SEASON,
            "coverage": "all certified affiliated MiLB actual leagues",
            "source_level_artifacts": {
                "summary": [str(path) for path in summary_paths],
                "profile": [str(path) for path in profile_paths],
                "bin_values": [str(path) for path in value_paths],
            },
        },
        "metrics": metrics,
        "storage": {
            "summary": summary_artifact.as_record(),
            "profile": profile_artifact.as_record(),
            "bin_values": values_artifact.as_record(),
            "duckdb": duckdb_metrics,
        },
        "interpretation": (
            "Performance-layer player × actual-league × season data only. Players are not "
            "collapsed across levels; Current Talent, projection, playing time, defense, "
            "WAR, and overall ranking are later layers."
        ),
    }
    (args.output_root / "affiliated_batting_performance_2024.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# Affiliated batting Performance materialization — 2024",
        "",
        f"- Actual leagues: {metrics['actual_league_count']:,}",
        f"- Level groups: {metrics['level_group_count']:,}",
        f"- Player × actual-league × season rows: {metrics['summary_row_count']:,}",
        f"- Plate appearances: {metrics['total_plate_appearances']:,}",
        f"- Classified contact events: {metrics['total_contact_events']:,}",
        f"- Screened core Performance events: {metrics['total_core_profile_events']:,}",
        f"- Core-profile coverage: {metrics['core_profile_coverage_rate']:.2%}",
        f"- Net contact residual vs aggregate: {metrics['total_contact_count_residual_vs_aggregate']:+,}",
        f"- Unknown contacts: {metrics['unknown_contact_count']:,} ({metrics['unknown_contact_rate']:.3%})",
        f"- Contacts under official participant overlay: {metrics['official_overlay_contact_count']:,} ({metrics['official_overlay_contact_rate']:.2%})",
        f"- Unvalued core events: {metrics['unvalued_core_event_count']:,}",
        f"- Uncertified/missing-value player rows: {metrics['uncertified_or_missing_bin_value_player_rows']:,}",
        f"- DuckDB unique summary keys: {duckdb_metrics['summary_unique_keys']:,}/{duckdb_metrics['summary_rows']:,}",
        "",
        "This is the first complete 2024 affiliated MiLB batting Performance dataset; it is not a talent estimate or ranking.",
    ]
    text = "\n".join(lines)
    (args.output_root / "affiliated_batting_performance_2024.md").write_text(
        text, encoding="utf-8"
    )
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
