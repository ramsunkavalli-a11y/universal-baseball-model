#!/usr/bin/env python
"""Materialize historical MiLB defense and runner opportunity partitions.

The job streams one public release asset at a time, writes compact Parquet
partitions, and removes the raw download unless ``--keep-raw`` is supplied.
It never reads 2026 and deliberately leaves 2020 absent.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.armstjc_assets import ArmstjcAsset, fetch_pbp_asset_inventory
from universal_baseball.armstjc_schema import (
    KNOWN_COLUMN_ALIASES,
    normalize_known_schema_aliases,
)
from universal_baseball.certification import download_file
from universal_baseball.pbp_opportunity_events import (
    add_sequence_start_state,
    build_fielding_opportunities,
    build_runner_advancement_opportunities,
    project_catcher_pitch_observations,
    project_terminal_play_observations,
    required_catcher_pitch_source_columns,
    required_source_columns,
    summarize_opportunity_coverage,
    write_manifest,
)


DEFAULT_YEARS = (2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024)
DEFAULT_LEVELS = ("aaa", "aa", "a+", "a", "a-", "rk")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    parser.add_argument("--levels", nargs="+", default=list(DEFAULT_LEVELS))
    parser.add_argument("--assets", nargs="*", default=[])
    parser.add_argument(
        "--smallest-per-year-level",
        action="store_true",
        help="Run a bandwidth-minimized coverage audit instead of every asset.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/working/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--download-root",
        type=Path,
        default=Path("data/quarantine/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/pbp-opportunity-foundation-v1"),
    )
    parser.add_argument("--keep-raw", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-pbp-opportunities/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _select_assets(
    inventory: list[ArmstjcAsset],
    *,
    years: set[int],
    levels: set[str],
    names: set[str],
    smallest: bool,
) -> list[ArmstjcAsset]:
    if 2026 in years:
        raise ValueError("2026 is protected and cannot be materialized by this job")
    selected = [
        asset
        for asset in inventory
        if asset.year in years
        and asset.filename_level in levels
        and (not names or asset.name in names)
    ]
    if names:
        missing = sorted(names - {asset.name for asset in selected})
        if missing:
            raise ValueError(f"requested assets not found in selected years/levels: {missing}")
    if not smallest:
        return selected
    by_slice: dict[tuple[int, str], list[ArmstjcAsset]] = {}
    for asset in selected:
        by_slice.setdefault((asset.year, asset.filename_level), []).append(asset)
    return sorted(
        (
            min(rows, key=lambda row: (row.size_bytes, row.filename_period, row.asset_id))
            for rows in by_slice.values()
        ),
        key=lambda row: (row.year, row.filename_level),
    )


def _paths(root: Path, asset: ArmstjcAsset) -> dict[str, Path]:
    stem = asset.name.removesuffix(".csv")
    slice_root = root / f"season={asset.year}" / f"level={asset.filename_level}"
    return {
        "terminal": slice_root / "terminal" / f"{stem}.parquet",
        "fielding": slice_root / "fielding" / f"{stem}.parquet",
        "runners": slice_root / "runners" / f"{stem}.parquet",
        "catcher_pitches": slice_root / "catcher_pitches" / f"{stem}.parquet",
        "manifest": slice_root / "manifests" / f"{stem}.json",
    }


def _read_raw(path: Path) -> pl.DataFrame:
    schema = pl.scan_csv(path, infer_schema_length=10_000).collect_schema()
    columns = list(
        dict.fromkeys(
            [*required_source_columns(), *required_catcher_pitch_source_columns()]
        )
    )
    source_names = set(schema.names())
    aliases_by_canonical = {
        canonical: alias for alias, canonical in KNOWN_COLUMN_ALIASES.items()
    }
    load_columns = [
        name
        if name in source_names
        else aliases_by_canonical.get(name, name)
        for name in columns
    ]
    missing = sorted(set(load_columns) - source_names)
    if missing:
        raise ValueError(f"{path.name} missing opportunity fields: {missing}")
    raw = pl.read_csv(
        path,
        columns=load_columns,
        infer_schema_length=10_000,
        null_values=[""],
        ignore_errors=False,
    )
    normalized, _ = normalize_known_schema_aliases(raw)
    return normalized


def _materialize_asset(
    asset: ArmstjcAsset,
    *,
    output_root: Path,
    download_root: Path,
    keep_raw: bool,
    overwrite: bool,
) -> dict[str, Any]:
    paths = _paths(output_root, asset)
    if not overwrite and all(path.exists() for path in paths.values()):
        return json.loads(paths["manifest"].read_text(encoding="utf-8"))

    raw_path = download_root / asset.name
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    download = download_file(
        asset.browser_download_url, raw_path, attempts=4, timeout_seconds=300
    )
    try:
        raw = _read_raw(raw_path)
        terminal = project_terminal_play_observations(
            raw,
            source_asset=asset.name,
            season=asset.year,
            level=asset.filename_level,
        )
        terminal = add_sequence_start_state(terminal)
        fielding = build_fielding_opportunities(terminal)
        runners = build_runner_advancement_opportunities(terminal)
        catcher_pitches = project_catcher_pitch_observations(
            raw,
            source_asset=asset.name,
            season=asset.year,
            level=asset.filename_level,
            terminal_plays=terminal,
        )
        for name, frame in (
            ("terminal", terminal),
            ("fielding", fielding),
            ("runners", runners),
            ("catcher_pitches", catcher_pitches),
        ):
            paths[name].parent.mkdir(parents=True, exist_ok=True)
            frame.write_parquet(paths[name], compression="zstd", statistics=True)
        report: dict[str, Any] = {
            "report_schema_version": "0.1",
            "source_asset": asset.as_record(),
            "download": download,
            "protected_2026_accessed": False,
            "2020_expected_absence": True,
            "outputs": {name: str(path) for name, path in paths.items()},
            "coverage": summarize_opportunity_coverage(terminal, fielding, runners),
            "accepted": terminal.height > 0 and fielding.height > 0,
        }
        report["coverage"].update(
            {
                "catcher_pitch_count": int(catcher_pitches.height),
                "framing_take_count": int(
                    catcher_pitches.filter(
                        pl.col("called_strike") | pl.col("called_ball")
                    ).height
                ),
                "clean_block_opportunity_count": int(
                    catcher_pitches.filter(pl.col("clean_block_opportunity")).height
                ),
            }
        )
        write_manifest(paths["manifest"], report)
        return report
    finally:
        if not keep_raw and raw_path.exists():
            raw_path.unlink()


def _write_report(root: Path, reports: list[dict[str, Any]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    accepted = sum(bool(report.get("accepted")) for report in reports)
    empty = sum(
        int(report.get("coverage", {}).get("terminal_play_count", 0)) == 0
        for report in reports
    )
    payload = {
        "report_schema_version": "0.1",
        "component": "shared_pbp_defense_runner_opportunity_foundation",
        "asset_count": len(reports),
        "accepted_asset_count": accepted,
        "empty_placeholder_asset_count": empty,
        "protected_2026_accessed": False,
        "reports": reports,
        "accepted": accepted + empty == len(reports) and bool(reports),
    }
    (root / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    lines = [
        "# PBP defense and runner opportunity foundation",
        "",
        f"- Assets processed: {len(reports):,}",
        f"- Assets accepted: {accepted:,}",
        f"- Empty boundary placeholders: {empty:,}",
        "- 2026 accessed: **false**",
        "- 2020 handling: expected missing MiLB season",
        "",
    ]
    for report in reports:
        asset = report["source_asset"]
        coverage = report["coverage"]
        lines.extend(
            [
                f"## {asset['name']}",
                "",
                f"- Accepted: {report['accepted']}",
                f"- Games: {coverage['game_count']:,}",
                f"- Terminal plays: {coverage['terminal_play_count']:,}",
                f"- Fielding opportunities: {coverage['fielding_opportunity_count']:,}",
                f"- Runner opportunities: {coverage['runner_opportunity_count']:,}",
                f"- Framing takes: {coverage.get('framing_take_count', 0):,}",
                f"- Clean block opportunities: {coverage.get('clean_block_opportunity_count', 0):,}",
                f"- Known runner outcomes: {coverage['known_runner_destination_count']:,}",
                f"- Fielding positions: `{coverage['fielding_position_counts']}`",
                f"- Runner types: `{coverage['runner_type_counts']}`",
                "",
            ]
        )
    (root / "report.md").write_text("\n".join(lines), encoding="utf-8")


def _inventory_from_existing_manifests(root: Path) -> list[ArmstjcAsset]:
    assets: dict[str, ArmstjcAsset] = {}
    for path in root.glob("season=*/level=*/manifests/*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = payload.get("source_asset") or {}
        if not raw.get("name") or not raw.get("browser_download_url"):
            continue
        assets[str(raw["name"])] = ArmstjcAsset(
            asset_id=int(raw["asset_id"]),
            name=str(raw["name"]),
            size_bytes=int(raw["size_bytes"]),
            created_at_utc=datetime.fromisoformat(
                str(raw["created_at_utc"]).replace("Z", "+00:00")
            ),
            updated_at_utc=datetime.fromisoformat(
                str(raw["updated_at_utc"]).replace("Z", "+00:00")
            ),
            browser_download_url=str(raw["browser_download_url"]),
            year=int(raw["year"]),
            filename_period=int(raw["filename_period"]),
            filename_level=str(raw["filename_level"]),
        )
    return sorted(
        assets.values(),
        key=lambda row: (row.year, row.filename_level, row.filename_period),
    )


def _inventory_from_historical_report(path: Path) -> list[ArmstjcAsset]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows: list[ArmstjcAsset] = []
    level_order = {level: index for index, level in enumerate(DEFAULT_LEVELS, start=1)}
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    for cell in payload.get("year_level_cells") or []:
        year = int(cell["year"])
        level = str(cell["filename_level"])
        periods = [int(value) for value in cell.get("pbp_periods") or []]
        if not periods:
            continue
        approximate_size = max(
            1, int(cell.get("pbp_size_bytes") or 0) // max(len(periods), 1)
        )
        for period in periods:
            name = f"{year}_{period}_{level}_pbp.csv"
            rows.append(
                ArmstjcAsset(
                    asset_id=-(year * 1000 + period * 10 + level_order.get(level, 9)),
                    name=name,
                    size_bytes=approximate_size,
                    created_at_utc=epoch,
                    updated_at_utc=epoch,
                    browser_download_url=(
                        "https://github.com/armstjc/milb-data-repository/"
                        f"releases/download/pbp/{name}"
                    ),
                    year=year,
                    filename_period=period,
                    filename_level=level,
                )
            )
    # The current-level inventory intentionally omits the former Short-Season
    # A classification.  Those public assets still exist and are valuable for
    # 2016-2019 player histories, so preserve their four playing-season months.
    for year in (2016, 2017, 2018, 2019):
        for period in (6, 7, 8, 9):
            name = f"{year}_{period}_a-_pbp.csv"
            rows.append(
                ArmstjcAsset(
                    asset_id=-(year * 1000 + period * 10 + 5),
                    name=name,
                    size_bytes=1,
                    created_at_utc=epoch,
                    updated_at_utc=epoch,
                    browser_download_url=(
                        "https://github.com/armstjc/milb-data-repository/"
                        f"releases/download/pbp/{name}"
                    ),
                    year=year,
                    filename_period=period,
                    filename_level="a-",
                )
            )
    return rows


def main() -> int:
    args = _parser().parse_args()
    years = set(args.years)
    levels = {str(level).lower() for level in args.levels}
    names = set(args.assets)
    try:
        with _session() as session:
            inventory = fetch_pbp_asset_inventory(session=session)
    except requests.RequestException:
        existing = _inventory_from_existing_manifests(args.output_root)
        planned = _inventory_from_historical_report(
            Path("reports/generated/historical-pbp-expansion-recheck-2026-09-19/report.json")
        )
        inventory_by_name = {asset.name: asset for asset in planned}
        inventory_by_name.update({asset.name: asset for asset in existing})
        inventory = list(inventory_by_name.values())
        if not inventory:
            raise
    selected = _select_assets(
        inventory,
        years=years,
        levels=levels,
        names=names,
        smallest=args.smallest_per_year_level,
    )
    if not selected:
        raise RuntimeError("no PBP assets selected")
    reports: list[dict[str, Any]] = []
    for index, asset in enumerate(selected, start=1):
        print(f"[{index}/{len(selected)}] {asset.name}", flush=True)
        report = _materialize_asset(
            asset,
            output_root=args.output_root,
            download_root=args.download_root,
            keep_raw=args.keep_raw,
            overwrite=args.overwrite,
        )
        reports.append(report)
        _write_report(args.report_root, reports)
        coverage = report["coverage"]
        print(
            f"  games={coverage['game_count']} "
            f"fielding={coverage['fielding_opportunity_count']} "
            f"runners={coverage['runner_opportunity_count']}",
            flush=True,
        )
    successful = all(
        bool(report.get("accepted"))
        or int(report.get("coverage", {}).get("terminal_play_count", 0)) == 0
        for report in reports
    )
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
