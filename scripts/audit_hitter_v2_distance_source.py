#!/usr/bin/env python3
"""Audit MiLB hit-distance availability without fitting or scoring offense.

This audit reads only already-disclosed 2021-2024 affiliated PBP.  It reports
field availability, range, batted-ball-type coverage, and co-availability with
tracking fields.  It does not construct a player feature or load forecast
targets.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import duckdb
import polars as pl

from universal_baseball.storage import write_canonical_parquet


LEVEL_ALIASES = {"aplus": "HIGH_A", "a": "SINGLE_A", "rk": "ROOKIE_COMPLEX"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-root",
        type=Path,
        default=Path("data/quarantine/hitter-v2-stage1/pbp"),
    )
    parser.add_argument(
        "--season-2024-root",
        type=Path,
        default=Path(
            "data/quarantine/hitter-v2-stage2-2024-milb/"
            "reconstructed-terminal-source/2024"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-distance-source-audit"),
    )
    return parser.parse_args()


def _level_group(value: str) -> str:
    normalized = value.lower()
    if normalized == "aaa":
        return "AAA"
    if normalized == "aa":
        return "AA"
    try:
        return LEVEL_ALIASES[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown affiliated level directory: {value}") from exc


def _source_files(historical_root: Path, season_2024_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for path in sorted(historical_root.rglob("*_pbp.csv")):
        relative = path.relative_to(historical_root)
        season = int(relative.parts[0])
        if season not in (2021, 2022, 2023):
            continue
        records.append(
            {
                "season": season,
                "level_group": _level_group(relative.parts[1]),
                "path": path,
            }
        )
    for path in sorted(season_2024_root.rglob("*_pbp.csv")):
        relative = path.relative_to(season_2024_root)
        records.append(
            {
                "season": 2024,
                "level_group": _level_group(relative.parts[0]),
                "path": path,
            }
        )
    if not records:
        raise ValueError("no affiliated PBP files found")
    seasons = sorted({int(record["season"]) for record in records})
    if seasons != [2021, 2022, 2023, 2024]:
        raise ValueError(f"expected 2021-2024 PBP, found seasons {seasons}")
    return records


def _aggregate_file(connection: duckdb.DuckDBPyConnection, path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    source = str(path.resolve()).replace("\\", "/")
    base = connection.execute(
        """
        WITH source AS (
          SELECT
            nullif(trim(game_pk), '') AS game_pk,
            nullif(trim(at_bat_number), '') AS at_bat_number,
            upper(nullif(trim(bb_type), '')) AS bb_type,
            try_cast(nullif(trim(hit_distance_sc), '') AS DOUBLE) AS distance,
            try_cast(nullif(trim(launch_speed), '') AS DOUBLE) AS exit_velocity,
            try_cast(nullif(trim(launch_angle), '') AS DOUBLE) AS launch_angle
          FROM read_csv_auto(?, header = true, all_varchar = true)
        ),
        pa AS (
          SELECT
            game_pk,
            at_bat_number,
            max(bb_type) AS bb_type,
            max(distance) AS distance,
            max(exit_velocity) AS exit_velocity,
            max(launch_angle) AS launch_angle,
            count(DISTINCT bb_type) AS distinct_bb_types,
            count(distance) AS distance_rows,
            count(DISTINCT distance) AS distinct_distances,
            count(exit_velocity) AS exit_velocity_rows,
            count(launch_angle) AS launch_angle_rows
          FROM source
          WHERE game_pk IS NOT NULL AND at_bat_number IS NOT NULL
          GROUP BY game_pk, at_bat_number
        )
        SELECT
          (SELECT count(*) FROM source) AS source_rows,
          count(*) AS canonical_pa,
          count(bb_type) AS classified_batted_ball_pa,
          count(distance) AS distance_pa,
          sum(distance_rows) AS raw_distance_rows,
          count(exit_velocity) AS exit_velocity_pa,
          sum(exit_velocity_rows) AS raw_exit_velocity_rows,
          count(launch_angle) AS launch_angle_pa,
          sum(launch_angle_rows) AS raw_launch_angle_rows,
          count(*) FILTER (WHERE distance IS NOT NULL AND exit_velocity IS NOT NULL)
            AS distance_with_exit_velocity_pa,
          count(*) FILTER (WHERE distance IS NOT NULL AND exit_velocity IS NULL)
            AS distance_without_exit_velocity_pa,
          count(*) FILTER (WHERE distance IS NULL AND exit_velocity IS NOT NULL)
            AS exit_velocity_without_distance_pa,
          count(*) FILTER (
            WHERE distance IS NOT NULL AND exit_velocity IS NOT NULL
              AND launch_angle IS NOT NULL
          ) AS distance_with_ev_la_pa,
          min(distance) AS minimum_distance,
          quantile_cont(distance, 0.01) AS distance_p01,
          quantile_cont(distance, 0.50) AS distance_p50,
          quantile_cont(distance, 0.99) AS distance_p99,
          max(distance) AS maximum_distance,
          count(*) FILTER (WHERE distance < 0 OR distance > 600)
            AS implausible_distance_pa,
          count(*) FILTER (WHERE distance_rows > 1) AS pa_with_multiple_distance_rows,
          count(*) FILTER (WHERE distinct_distances > 1) AS pa_with_conflicting_distances,
          count(*) FILTER (WHERE distinct_bb_types > 1) AS pa_with_conflicting_bb_types
        FROM pa
        """,
        [source],
    ).fetchone()
    columns = [item[0] for item in connection.description]
    base_record = dict(zip(columns, base, strict=True))

    by_type_rows = connection.execute(
        """
        WITH source AS (
          SELECT
            nullif(trim(game_pk), '') AS game_pk,
            nullif(trim(at_bat_number), '') AS at_bat_number,
            upper(nullif(trim(bb_type), '')) AS bb_type,
            try_cast(nullif(trim(hit_distance_sc), '') AS DOUBLE) AS distance,
            try_cast(nullif(trim(launch_speed), '') AS DOUBLE) AS exit_velocity,
            try_cast(nullif(trim(launch_angle), '') AS DOUBLE) AS launch_angle
          FROM read_csv_auto(?, header = true, all_varchar = true)
        ),
        pa AS (
          SELECT
            game_pk,
            at_bat_number,
            coalesce(max(bb_type), 'UNCLASSIFIED') AS bb_type,
            max(distance) AS distance,
            max(exit_velocity) AS exit_velocity,
            max(launch_angle) AS launch_angle,
            count(distance) AS raw_distance_rows
          FROM source
          WHERE game_pk IS NOT NULL AND at_bat_number IS NOT NULL
          GROUP BY game_pk, at_bat_number
        )
        SELECT
          bb_type,
          count(*) AS canonical_pa,
          count(distance) AS distance_pa,
          sum(raw_distance_rows) AS raw_distance_rows,
          count(exit_velocity) AS exit_velocity_pa,
          count(launch_angle) AS launch_angle_pa,
          count(*) FILTER (WHERE distance IS NOT NULL AND exit_velocity IS NOT NULL)
            AS distance_with_exit_velocity_pa,
          min(distance) AS minimum_distance,
          quantile_cont(distance, 0.50) AS distance_p50,
          max(distance) AS maximum_distance
        FROM pa
        GROUP BY bb_type
        """,
        [source],
    ).fetchall()
    type_columns = [item[0] for item in connection.description]
    return base_record, [
        dict(zip(type_columns, row, strict=True)) for row in by_type_rows
    ]


def _sum_nullable(values: list[object]) -> float | int | None:
    present = [value for value in values if value is not None]
    return sum(present) if present else None


def _consolidate(records: list[dict[str, object]], dimensions: tuple[str, ...]) -> pl.DataFrame:
    additive = (
        "source_files",
        "source_size_bytes",
        "source_rows",
        "canonical_pa",
        "classified_batted_ball_pa",
        "distance_pa",
        "raw_distance_rows",
        "exit_velocity_pa",
        "raw_exit_velocity_rows",
        "launch_angle_pa",
        "raw_launch_angle_rows",
        "distance_with_exit_velocity_pa",
        "distance_without_exit_velocity_pa",
        "exit_velocity_without_distance_pa",
        "distance_with_ev_la_pa",
        "implausible_distance_pa",
        "pa_with_multiple_distance_rows",
        "pa_with_conflicting_distances",
        "pa_with_conflicting_bb_types",
    )
    groups: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for record in records:
        key = tuple(record[dimension] for dimension in dimensions)
        groups.setdefault(key, []).append(record)
    output: list[dict[str, object]] = []
    for key, group in sorted(groups.items()):
        row = {dimension: key[index] for index, dimension in enumerate(dimensions)}
        for column in additive:
            row[column] = _sum_nullable([record.get(column) for record in group])
        classified = int(row.get("classified_batted_ball_pa") or 0)
        distance = int(row.get("distance_pa") or 0)
        row["distance_coverage_of_classified_batted_balls"] = (
            distance / classified if classified else None
        )
        source_rows = int(row.get("source_rows") or 0)
        row["distance_coverage_of_source_rows"] = (
            distance / source_rows if source_rows else None
        )
        row["distance_with_exit_velocity_rate"] = (
            int(row.get("distance_with_exit_velocity_pa") or 0) / distance
            if distance
            else None
        )
        output.append(row)
    result = pl.DataFrame(output, infer_schema_length=None)
    return result.sort(*dimensions) if dimensions else result


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    args = _parse_args()
    sources = _source_files(args.historical_root, args.season_2024_root)
    connection = duckdb.connect()
    file_records: list[dict[str, object]] = []
    type_records: list[dict[str, object]] = []
    for index, source in enumerate(sources, start=1):
        path = Path(source["path"])
        base, by_type = _aggregate_file(connection, path)
        common = {
            "season": int(source["season"]),
            "level_group": str(source["level_group"]),
            "source_path": str(path),
            "source_size_bytes": path.stat().st_size,
            "source_files": 1,
        }
        file_records.append({**common, **base})
        type_records.extend({**common, **row} for row in by_type)
        print(f"audited {index}/{len(sources)}: {path}")
    connection.close()

    file_table = pl.DataFrame(file_records, infer_schema_length=None).sort(
        "season", "level_group", "source_path"
    )
    coverage = _consolidate(file_records, ("season", "level_group"))
    type_coverage = _consolidate(
        type_records, ("season", "level_group", "bb_type")
    )

    args.report_root.mkdir(parents=True, exist_ok=True)
    table_root = args.report_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    paths = {
        "file_audit": table_root / "distance_source_file_audit.parquet",
        "coverage": table_root / "distance_coverage_by_season_level.parquet",
        "type_coverage": table_root
        / "distance_coverage_by_season_level_batted_ball_type.parquet",
    }
    write_canonical_parquet(
        file_table, paths["file_audit"], table_name="distance_source_file_audit"
    )
    write_canonical_parquet(
        coverage,
        paths["coverage"],
        table_name="distance_coverage_by_season_level",
    )
    write_canonical_parquet(
        type_coverage,
        paths["type_coverage"],
        table_name="distance_coverage_by_season_level_batted_ball_type",
    )

    overall = _consolidate(file_records, tuple()).to_dicts()[0]
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2c_source_audit",
        "audit": "hit_distance_sc_availability",
        "source_seasons": [2021, 2022, 2023, 2024],
        "target_outcomes_loaded": False,
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
        "source_interpretation": {
            "field": "hit_distance_sc",
            "provisional_capability_tier": "tracking_or_enriched_pbp_not_universal_pbp",
            "reason": "availability is audited jointly with launch_speed and launch_angle; absence must preserve exact outcome-only fallback",
        },
        "overall": overall,
        "coverage_by_season_level": coverage.to_dicts(),
        "artifacts": {
            name: {"path": str(path), "sha256": _sha256(path)}
            for name, path in paths.items()
        },
    }
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
