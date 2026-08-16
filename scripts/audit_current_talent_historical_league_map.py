#!/usr/bin/env python
"""Audit actual-league mapping for the initial historical Current Talent window.

This is intentionally cheaper than a historical PBP backfill. For each selected
year x filename-level cell it downloads the two largest published player-game
assets and observes regular-season positive-PA league IDs directly from source.
The audit exists to prevent 2024 league assumptions from being projected
backward across MiLB restructuring without evidence.

Passing this gate does *not* certify historical PBP, participant identity, or
Performance parity. It only certifies that the sampled player-game source has a
nonempty, internally coherent year x filename-level actual-league map suitable
for the next scoped materialization gate.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import polars as pl
import requests

from universal_baseball.certification import download_file, read_quarantined_csv
from universal_baseball.current_talent_history import (
    CURRENT_AFFILIATED_FILENAME_LEVELS,
    summarize_historical_league_mapping,
)
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory


TARGET_YEARS = (2019, 2021, 2022, 2023, 2024)
ASSETS_PER_CELL = 2
MINIMAL_FIELDS = (
    "game_id",
    "game_date",
    "game_type",
    "league_id",
    "player_id",
    "batting_PA",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/current-talent-historical-league-map"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/current-talent-historical-league-map"),
    )
    return parser.parse_args()


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-historical-league-map/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _project_mapping_rows(
    raw: pl.DataFrame,
    *,
    source_asset: str,
    source_year: int,
    filename_level: str,
) -> pl.DataFrame:
    missing = sorted(set(MINIMAL_FIELDS) - set(raw.columns))
    if missing:
        raise ValueError(f"{source_asset} missing historical mapping fields: {missing}")
    return raw.select(
        pl.lit(int(source_year)).cast(pl.Int64).alias("source_year"),
        pl.lit(str(filename_level)).alias("filename_level"),
        pl.col("game_id").cast(pl.Float64, strict=False).cast(pl.Int64, strict=False),
        pl.col("game_date").cast(pl.String),
        pl.col("game_type").cast(pl.String),
        pl.col("league_id").cast(pl.Float64, strict=False).cast(pl.Int64, strict=False),
        pl.col("player_id").cast(pl.Float64, strict=False).cast(pl.Int64, strict=False),
        pl.col("batting_PA").cast(pl.Float64, strict=False),
        pl.lit(str(source_asset)).alias("source_asset"),
    )


def main() -> int:
    args = parse_args()
    args.work_root.mkdir(parents=True, exist_ok=True)
    args.report_root.mkdir(parents=True, exist_ok=True)

    session = _github_session()
    try:
        inventory = fetch_player_game_asset_inventory(session=session)
    finally:
        session.close()

    selected_assets: list[dict[str, Any]] = []
    asset_errors: list[dict[str, Any]] = []
    frames: list[pl.DataFrame] = []

    for year in TARGET_YEARS:
        for level in CURRENT_AFFILIATED_FILENAME_LEVELS:
            candidates = [
                asset
                for asset in inventory
                if asset.year == year and asset.filename_level == level
            ]
            chosen = sorted(
                candidates,
                key=lambda asset: (asset.size_bytes, asset.filename_period, asset.asset_id),
                reverse=True,
            )[:ASSETS_PER_CELL]
            for asset in sorted(chosen, key=lambda row: (row.filename_period, row.asset_id)):
                selected_assets.append(
                    {
                        "year": year,
                        "filename_level": level,
                        "asset_name": asset.name,
                        "filename_period": asset.filename_period,
                        "size_bytes": asset.size_bytes,
                    }
                )
                local = args.work_root / str(year) / level / asset.name
                local.parent.mkdir(parents=True, exist_ok=True)
                try:
                    if not local.exists() or local.stat().st_size <= 0:
                        download_file(asset.browser_download_url, local, timeout_seconds=240)
                    raw = read_quarantined_csv(local)
                    frames.append(
                        _project_mapping_rows(
                            raw,
                            source_asset=asset.name,
                            source_year=year,
                            filename_level=level,
                        )
                    )
                except Exception as exc:  # report source/schema failures before exiting
                    asset_errors.append(
                        {
                            "year": year,
                            "filename_level": level,
                            "asset_name": asset.name,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )

    if frames:
        observations = pl.concat(frames, how="vertical_relaxed")
        mapping = summarize_historical_league_mapping(
            observations,
            years=TARGET_YEARS,
            levels=CURRENT_AFFILIATED_FILENAME_LEVELS,
        )
    else:
        observations = pl.DataFrame()
        mapping = {
            "years": list(TARGET_YEARS),
            "levels": list(CURRENT_AFFILIATED_FILENAME_LEVELS),
            "raw_observation_count": 0,
            "eligible_positive_pa_observation_count": 0,
            "year_level_rows": [],
            "missing_year_level_cells": [
                {"year": year, "filename_level": level}
                for year in TARGET_YEARS
                for level in CURRENT_AFFILIATED_FILENAME_LEVELS
            ],
            "cross_level_league_conflicts": [],
            "date_year_mismatch_count": 0,
            "player_game_league_identity_conflict_count": 0,
            "accepted_mapping_gate": False,
            "interpretation": "No readable mapping observations were produced.",
        }

    accepted = bool(mapping["accepted_mapping_gate"] and not asset_errors)
    report = {
        "report_schema_version": 1,
        "target_years": list(TARGET_YEARS),
        "filename_levels": list(CURRENT_AFFILIATED_FILENAME_LEVELS),
        "assets_per_cell": ASSETS_PER_CELL,
        "selected_asset_count": len(selected_assets),
        "selected_assets": selected_assets,
        "asset_errors": asset_errors,
        "mapping": mapping,
        "accepted": accepted,
        "interpretation": (
            "Player-game actual-league mapping gate only. Passing does not certify historical "
            "PBP semantics, participant authority, chronology, Performance parity, or model use."
        ),
    }
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )

    if mapping["year_level_rows"]:
        pl.DataFrame(mapping["year_level_rows"]).write_csv(args.report_root / "league_map.csv")
    if asset_errors:
        pl.DataFrame(asset_errors).write_csv(args.report_root / "asset_errors.csv")

    lines = [
        "# Current Talent historical actual-league map audit",
        "",
        f"- Target years: {', '.join(str(year) for year in TARGET_YEARS)}",
        f"- Selected player-game assets: {len(selected_assets):,}",
        f"- Asset/schema errors: {len(asset_errors):,}",
        f"- Mapping rows: {len(mapping['year_level_rows']):,}",
        f"- Missing year-level cells: {len(mapping['missing_year_level_cells']):,}",
        f"- Cross-level league-ID conflicts: {len(mapping['cross_level_league_conflicts']):,}",
        f"- Player-game league-identity conflicts: "
        f"{mapping['player_game_league_identity_conflict_count']:,}",
        f"- Date/source-year mismatches: {mapping['date_year_mismatch_count']:,}",
        f"- Accepted mapping gate: {accepted}",
        "",
        "## Observed map",
        "",
    ]
    for row in mapping["year_level_rows"]:
        lines.append(
            f"- {row['year']} {row['filename_level']}: leagues={row['league_ids']}; "
            f"games={row['regular_game_count']:,}; player-games={row['positive_pa_player_game_count']:,}; "
            f"dates={row['min_game_date']}..{row['max_game_date']}"
        )
    lines.extend(
        [
            "",
            "This audit observes source league identity only; it does not back-cast the 2024 league map.",
        ]
    )
    text = "\n".join(lines)
    (args.report_root / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
