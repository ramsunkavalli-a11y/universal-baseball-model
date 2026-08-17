#!/usr/bin/env python
"""Audit whether duplicated historical MiLB terminal-PA rows are redundant.

Source-feasibility audit only. It does not score players and does not access 2023.
The description-source audit found repeated terminal rows in several 2022 assets.
This script asks whether rows sharing (game_pk, at_bat_number) are exact duplicates
across the fields needed for terminal contact identification and outcome parsing.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.armstjc_assets import ArmstjcAsset, fetch_pbp_asset_inventory
from universal_baseball.certification import download_file

YEARS = (2021, 2022)
LEVELS = ("aaa", "aa", "a+", "a", "rk")
REGULAR_GAME_TYPE = "R"
COMPARE_COLUMNS = (
    "batter", "pitch_number", "type", "bb_type", "hit_location", "hc_x", "hc_y",
    "hit_distance_sc", "launch_speed", "launch_angle", "description", "des",
)
REQUIRED_COLUMNS = ("game_pk", "game_type", "at_bat_number", *COMPARE_COLUMNS)


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-terminal-pa-duplicate-audit/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _choose_asset(inventory: list[ArmstjcAsset], *, year: int, level: str) -> ArmstjcAsset:
    months = {6, 7, 8} if level == "rk" else {4, 5, 6, 7, 8, 9}
    eligible = [
        asset for asset in inventory
        if asset.year == year and asset.filename_level == level and asset.filename_period in months
    ]
    if not eligible:
        raise RuntimeError(f"no audit asset for {year} {level}")
    return min(eligible, key=lambda asset: (asset.size_bytes, asset.filename_period, asset.asset_id))


def _norm(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, 9)
    return value


def _audit(asset: ArmstjcAsset, root: Path) -> dict[str, Any]:
    path = root / asset.name
    meta = download_file(asset.browser_download_url, path, attempts=4, timeout_seconds=240)
    schema = pl.scan_csv(path, infer_schema_length=1000).collect_schema()
    missing = sorted(set(REQUIRED_COLUMNS) - set(schema.names()))
    if missing:
        return {"asset": asset.as_record(), "download": meta, "missing_required_columns": missing}

    frame = pl.read_csv(
        path,
        columns=list(REQUIRED_COLUMNS),
        infer_schema_length=10_000,
        null_values=[""],
        ignore_errors=False,
    ).with_columns(
        pl.col("game_pk").cast(pl.Int64, strict=False),
        pl.col("at_bat_number").cast(pl.Int64, strict=False),
        pl.col("pitch_number").cast(pl.Int64, strict=False),
        pl.col("game_type").cast(pl.String),
    )
    regular = frame.filter(pl.col("game_type") == REGULAR_GAME_TYPE)
    terminal = regular.with_columns(
        pl.col("pitch_number").max().over(["game_pk", "at_bat_number"]).alias("_max_pitch")
    ).filter(pl.col("pitch_number") == pl.col("_max_pitch"))

    groups: dict[tuple[Any, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in terminal.select("game_pk", "at_bat_number", *COMPARE_COLUMNS).to_dicts():
        groups[(row["game_pk"], row["at_bat_number"])].append(row)

    duplicate_groups = {key: rows for key, rows in groups.items() if len(rows) > 1}
    exact_groups = 0
    conflicting_groups = 0
    conflicting_fields: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []

    for key, rows in duplicate_groups.items():
        signatures = {
            tuple(_norm(row[column]) for column in COMPARE_COLUMNS)
            for row in rows
        }
        if len(signatures) == 1:
            exact_groups += 1
            continue
        conflicting_groups += 1
        for column in COMPARE_COLUMNS:
            values = {_norm(row[column]) for row in rows}
            if len(values) > 1:
                conflicting_fields[column] += 1
        if len(examples) < 10:
            examples.append({
                "game_pk": key[0],
                "at_bat_number": key[1],
                "row_count": len(rows),
                "rows": rows[:4],
            })

    excess_rows = sum(len(rows) - 1 for rows in duplicate_groups.values())
    return {
        "asset": asset.as_record(),
        "download": meta,
        "missing_required_columns": [],
        "terminal_row_count": int(terminal.height),
        "unique_terminal_pa_count": len(groups),
        "duplicate_terminal_pa_group_count": len(duplicate_groups),
        "duplicate_excess_row_count": excess_rows,
        "exact_duplicate_group_count": exact_groups,
        "conflicting_duplicate_group_count": conflicting_groups,
        "all_duplicate_groups_exact": conflicting_groups == 0,
        "conflicting_field_counts": dict(sorted(conflicting_fields.items())),
        "conflicting_examples": examples,
    }


def main() -> int:
    work = Path("data/quarantine/current-talent-terminal-pa-duplicates")
    reports = Path("reports/generated/current-talent-terminal-pa-duplicates")
    work.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    with _session() as session:
        inventory = fetch_pbp_asset_inventory(session=session)
    assets = [_choose_asset(inventory, year=year, level=level) for year in YEARS for level in LEVELS]
    audited = [_audit(asset, work) for asset in assets]

    payload = {
        "report_schema_version": "0.1",
        "gate": "current_talent_terminal_pa_duplicate_source_exploration",
        "model_scoring_performed": False,
        "confirmation_2023_accessed": False,
        "accepted": False,
        "assets": audited,
    }
    (reports / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")

    lines = [
        "# Current Talent terminal-PA duplicate source exploration", "",
        "- Model scoring: **false**", "- 2023 accessed: **false**", "- Gate accepted: **false (exploratory)**", "",
    ]
    for result in audited:
        asset = result["asset"]
        lines += [
            f"## {asset['year']} {asset['filename_level']} — `{asset['name']}`", "",
            f"- Terminal rows: {result.get('terminal_row_count')}",
            f"- Unique terminal PAs: {result.get('unique_terminal_pa_count')}",
            f"- Duplicate PA groups: {result.get('duplicate_terminal_pa_group_count')}",
            f"- Excess duplicate rows: {result.get('duplicate_excess_row_count')}",
            f"- Exact duplicate groups: {result.get('exact_duplicate_group_count')}",
            f"- Conflicting duplicate groups: {result.get('conflicting_duplicate_group_count')}",
            f"- All duplicate groups exact: **{result.get('all_duplicate_groups_exact')}**",
            f"- Conflicting fields: `{result.get('conflicting_field_counts', {})}`", "",
        ]
    text = "\n".join(lines)
    (reports / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
