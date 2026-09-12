#!/usr/bin/env python3
"""Verify the 2025 source/topology contract before enabling Current Talent."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

import requests

from universal_baseball.armstjc_assets import fetch_pbp_asset_inventory
from universal_baseball.current_talent_era import POST_REORGANIZATION_LEVEL_SPECS
from universal_baseball.player_game_stats import fetch_player_game_asset_inventory


SEASON = 2025
REFERENCE_COMPLETE_SEASON = 2024


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/current-talent-2025-era-extension-result.json"),
    )
    return parser.parse_args()


def _github_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-era-extension/0.1"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def main() -> int:
    args = _args()
    github = _github_session()
    player_game = fetch_player_game_asset_inventory(session=github)
    pbp = fetch_pbp_asset_inventory(session=github)
    rows = []
    captures = []
    for filename_level, spec in POST_REORGANIZATION_LEVEL_SPECS.items():
        response = requests.get(
            "https://statsapi.mlb.com/api/v1/teams",
            params={"sportId": spec.official_sport_id, "season": SEASON, "hydrate": "league"},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        observed = sorted(
            {
                int(team["league"]["id"])
                for team in payload.get("teams", [])
                if team.get("league", {}).get("id") is not None
            }
        )
        expected = sorted(spec.league_ids)
        pg_assets = [
            asset.name
            for asset in player_game
            if asset.year == SEASON and asset.filename_level == filename_level
        ]
        pbp_assets = [
            asset.name
            for asset in pbp
            if asset.year == SEASON and asset.filename_level == filename_level
        ]
        pg_periods = sorted(
            asset.filename_period
            for asset in player_game
            if asset.year == SEASON and asset.filename_level == filename_level
        )
        pbp_periods = sorted(
            asset.filename_period
            for asset in pbp
            if asset.year == SEASON and asset.filename_level == filename_level
        )
        reference_pg_periods = sorted(
            asset.filename_period
            for asset in player_game
            if asset.year == REFERENCE_COMPLETE_SEASON
            and asset.filename_level == filename_level
        )
        reference_pbp_periods = sorted(
            asset.filename_period
            for asset in pbp
            if asset.year == REFERENCE_COMPLETE_SEASON
            and asset.filename_level == filename_level
        )
        full_season_asset_span = bool(
            pg_periods
            and pbp_periods
            and reference_pg_periods
            and reference_pbp_periods
            and max(pg_periods) >= max(reference_pg_periods)
            and max(pbp_periods) >= max(reference_pbp_periods)
        )
        rows.append(
            {
                "filename_level": filename_level,
                "level_group": spec.level_group,
                "official_sport_id": spec.official_sport_id,
                "expected_league_ids": expected,
                "observed_league_ids": observed,
                "topology_matches": observed == expected,
                "official_team_count": len(payload.get("teams", [])),
                "player_game_asset_count": len(pg_assets),
                "pbp_asset_count": len(pbp_assets),
                "player_game_periods": pg_periods,
                "pbp_periods": pbp_periods,
                "reference_2024_player_game_periods": reference_pg_periods,
                "reference_2024_pbp_periods": reference_pbp_periods,
                "full_season_asset_span": full_season_asset_span,
                "player_game_assets": pg_assets,
                "pbp_assets": pbp_assets,
            }
        )
        captures.append(
            {
                "filename_level": filename_level,
                "request_url": response.url,
                "response_sha256": sha256(response.content).hexdigest(),
                "response_byte_count": len(response.content),
            }
        )
    failures = [
        row
        for row in rows
        if not row["topology_matches"]
        or not row["player_game_asset_count"]
        or not row["pbp_asset_count"]
        or not row["full_season_asset_span"]
    ]
    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_2025_era_extension",
        "season": SEASON,
        "accepted": not failures,
        "topology_accepted": all(row["topology_matches"] for row in rows),
        "full_season_source_accepted": all(
            row["full_season_asset_span"] for row in rows
        ),
        "levels": rows,
        "official_captures": captures,
        "failure_count": len(failures),
        "boundary": {
            "topology_only": True,
            "model_fit": False,
            "talent_scores_computed": False,
            "future_outcomes_accessed": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
