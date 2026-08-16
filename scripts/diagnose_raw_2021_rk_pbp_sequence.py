#!/usr/bin/env python
"""Capture every raw source field for the one uncovered 2021 Rookie sequence.

Diagnostic only. The contact-sequence coverage audit found that game 657792,
at-bat sequence 54 is the only reusable source sequence in a residual-triggered
game that lacks current official allPlays authority. This script preserves all
raw armstjc PBP rows for that game/sequence across overlapping release snapshots
so source structure can determine whether it is a real physical contact or a
source-quality false positive.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.certification import download_file, read_quarantined_csv


SEASON = 2021
LEVEL = "rk"
GAME_PK = 657792
AT_BAT_NUMBER = 54


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-raw-pbp-sequence/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)


def main() -> int:
    work_dir = Path("data/quarantine/current-talent-2021-rk-raw-sequence")
    report_dir = Path("reports/generated/current-talent-2021-rk-contact-sequence-diagnostic")
    work_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    session = _session()
    matched_rows: list[dict[str, Any]] = []
    asset_summaries: list[dict[str, Any]] = []
    try:
        assets = [
            asset
            for asset in fetch_pbp_asset_inventory(session=session)
            if asset.year == SEASON and asset.filename_level == LEVEL
        ]
        if not assets:
            raise RuntimeError("no reusable 2021 Rookie PBP assets found")
        for asset in assets:
            path = work_dir / asset.name
            if not path.exists() or path.stat().st_size <= 0:
                download_file(asset.browser_download_url, path, timeout_seconds=300)
            raw = read_quarantined_csv(path)
            required = {"game_pk", "at_bat_number"}
            missing = sorted(required - set(raw.columns))
            if missing:
                raise RuntimeError(f"{asset.name} missing raw sequence fields: {missing}")
            target = raw.filter(
                (pl.col("game_pk").cast(pl.Int64, strict=False) == GAME_PK)
                & (pl.col("at_bat_number").cast(pl.Int64, strict=False) == AT_BAT_NUMBER)
            )
            asset_summaries.append(
                {
                    "asset": asset.name,
                    "row_count": int(raw.height),
                    "target_row_count": int(target.height),
                    "column_count": len(raw.columns),
                    "columns": list(raw.columns),
                }
            )
            for row in target.to_dicts():
                matched_rows.append(
                    {
                        "source_asset": asset.name,
                        **{key: _json_safe(value) for key, value in row.items()},
                    }
                )
    finally:
        session.close()

    if not matched_rows:
        raise RuntimeError(
            f"no raw rows found for game={GAME_PK} at_bat_number={AT_BAT_NUMBER}"
        )

    report = {
        "report_schema_version": 1,
        "season": SEASON,
        "level": LEVEL,
        "game_pk": GAME_PK,
        "at_bat_number": AT_BAT_NUMBER,
        "matched_raw_row_count": len(matched_rows),
        "matched_source_assets": sorted({str(row["source_asset"]) for row in matched_rows}),
        "raw_rows": matched_rows,
        "asset_summaries": asset_summaries,
        "accepted": False,
        "interpretation": (
            "Diagnostic only. Any production exclusion must be justified by structured raw source "
            "fields showing this sequence is not physical batted-ball contact; narrative text alone "
            "is not sufficient when a structured discriminator exists."
        ),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True, default=str)
    (report_dir / "raw_missing_sequence.json").write_text(rendered, encoding="utf-8")

    columns = sorted({key for row in matched_rows for key in row})
    compact_rows = []
    for row in matched_rows:
        compact_rows.append({key: row.get(key) for key in columns})
    (report_dir / "raw_missing_sequence_compact.json").write_text(
        json.dumps(compact_rows, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "matched_raw_row_count": len(matched_rows),
                "matched_source_assets": report["matched_source_assets"],
                "raw_rows": matched_rows,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
