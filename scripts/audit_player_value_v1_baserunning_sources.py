#!/usr/bin/env python
"""Materialize the live baserunning source audit for Player Value v1."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path

import requests

from universal_baseball.mlb_season_stats import MLB_LEAGUE_IDS, MLB_STATS_URL
from universal_baseball.player_value_baserunning_sources import (
    SAVANT_BASERUNNING_RUN_VALUE_URL,
    audit_mlb_baserunning_splits,
    audit_savant_baserunning_rows,
    parse_savant_baserunning_csv,
    savant_baserunning_query_params,
)
from universal_baseball.player_value_mlb_run_environment import _fetch_group_splits
from universal_baseball.season_stat_assets import fetch_season_stat_asset_inventory


def _fetch_savant_baserunning_season(
    session: requests.Session,
    *,
    season: int,
    timeout_seconds: int = 60,
) -> tuple[dict[str, object], dict[str, object]]:
    params = savant_baserunning_query_params(season)
    response = session.get(
        SAVANT_BASERUNNING_RUN_VALUE_URL,
        params=params,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    text = response.content.decode("utf-8-sig")
    rows = parse_savant_baserunning_csv(text)
    audit = audit_savant_baserunning_rows(rows)
    if not audit["advancement_source_usable"]:
        raise ValueError(
            f"Savant baserunning advancement source failed audit for {season}: {audit}"
        )
    capture = {
        "season": season,
        "requested_url": response.url,
        "response_sha256": hashlib.sha256(response.content).hexdigest(),
        "response_bytes": len(response.content),
        "content_type": response.headers.get("content-type"),
        "row_count": len(rows),
    }
    return audit, capture


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=2024)
    parser.add_argument(
        "--savant-start-season",
        type=int,
        default=2019,
        help="First Savant advancement season to source-audit.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/player-value-v1-baserunning-source-audit-result.json"),
    )
    args = parser.parse_args()
    if args.savant_start_season > args.season:
        raise ValueError("--savant-start-season cannot exceed --season")

    league_results: dict[str, object] = {}
    all_splits = []
    all_captures = []
    savant_season_audits: dict[str, object] = {}
    savant_captures: list[dict[str, object]] = []
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

        for season in range(args.savant_start_season, args.season + 1):
            audit, capture = _fetch_savant_baserunning_season(
                session,
                season=season,
            )
            savant_season_audits[str(season)] = audit
            savant_captures.append(capture)

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
        "mlb_statcast_advancement": {
            "provider": "Baseball Savant",
            "endpoint": SAVANT_BASERUNNING_RUN_VALUE_URL,
            "source_role": "runner-level non-steal advancement run value and opportunity evidence",
            "query_contract": {
                "season_start": args.savant_start_season,
                "season_end": args.season,
                "one_season_per_request": True,
                "minimum_opportunities": 1,
                "runner_type": "Run",
                "game_type": "Regular",
            },
            "season_audits": savant_season_audits,
            "captures": savant_captures,
            "all_audited_seasons_usable": all(
                bool(audit["advancement_source_usable"])
                for audit in savant_season_audits.values()
            ),
        },
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
            "Savant run-value decomposition and opportunity-count identities are diagnostic only; the source gate requires complete finite fields and unique runner rows.",
            "This artifact audits source semantics only and does not select baserunning model parameters.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
