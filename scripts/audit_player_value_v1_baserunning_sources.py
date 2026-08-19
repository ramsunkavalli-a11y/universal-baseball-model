#!/usr/bin/env python
"""Materialize the live baserunning source audit for Player Value v1."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path

import requests

from universal_baseball.mlb_season_stats import MLB_LEAGUE_IDS, MLB_STATS_URL
from universal_baseball.player_value_baserunning_sources import (
    audit_mlb_baserunning_splits,
)
from universal_baseball.player_value_mlb_run_environment import _fetch_group_splits
from universal_baseball.season_stat_assets import fetch_season_stat_asset_inventory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2024)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/player-value-v1-baserunning-source-audit-result.json"),
    )
    args = parser.parse_args()

    league_results: dict[str, object] = {}
    all_splits = []
    all_captures = []
    with requests.Session() as session:
        for league_id in MLB_LEAGUE_IDS:
            splits, captures = _fetch_group_splits(
                session,
                season=args.season,
                league_id=league_id,
                group="hitting",
                page_limit=500,
                timeout_seconds=120,
            )
            audit = audit_mlb_baserunning_splits(splits)
            league_results[str(league_id)] = audit
            all_splits.extend(splits)
            all_captures.extend(captures)
        milb_inventory = fetch_season_stat_asset_inventory("batting", session=session)

    pooled = audit_mlb_baserunning_splits(all_splits)
    source_commit = str(os.environ.get("GITHUB_SHA") or "").strip() or None
    eligible_milb_assets = [
        asset for asset in milb_inventory if asset.year <= args.season and asset.is_nonempty
    ]
    payload = {
        "status": "player_value_v1_baserunning_source_audit_materialized",
        "season": args.season,
        "verified_source_commit": source_commit,
        "mlb_source": {
            "provider": "MLB Stats API",
            "endpoint": MLB_STATS_URL,
            "league_ids": list(MLB_LEAGUE_IDS),
            "group": "hitting",
            "stats": "season",
            "game_type": "R",
            "player_pool": "ALL",
        },
        "mlb_leagues": league_results,
        "mlb_pooled": pooled,
        "captures": [asdict(capture) for capture in all_captures],
        "milb_source": {
            "provider": "armstjc/milb-data-repository",
            "release_tag": "season_player_batting",
            "recognized_nonempty_assets_through_season": [
                {
                    "year": asset.year,
                    "filename_level": asset.filename_level,
                    "name": asset.name,
                    "asset_id": asset.asset_id,
                    "size_bytes": asset.size_bytes,
                    "updated_at_utc": asset.updated_at_utc.isoformat(),
                }
                for asset in eligible_milb_assets
            ],
            "available_years_through_season": sorted(
                {asset.year for asset in eligible_milb_assets}
            ),
            "available_levels_by_year": {
                str(year): sorted(
                    {
                        asset.filename_level
                        for asset in eligible_milb_assets
                        if asset.year == year
                    }
                )
                for year in sorted({asset.year for asset in eligible_milb_assets})
            },
        },
        "audit_contract": "docs/player-value-v1-baserunning-source-audit-contract.md",
        "notes": [
            "Missing source fields remain missing; the audit does not zero-fill them.",
            "MiLB inventory establishes historical asset availability, not yet per-file baserunning field completeness.",
            "This artifact audits source semantics only and does not select baserunning model parameters.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
