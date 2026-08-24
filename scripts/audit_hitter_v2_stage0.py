#!/usr/bin/env python
"""Materialize the outcome-blind Hitter v2 Stage 0 reproduction record."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from typing import Any

import polars as pl
import requests

from universal_baseball.hitter_v2_stage0 import (
    OFFICIAL_OUTCOME_COLUMNS,
    STAGE0_ALLOWED_OFFICIAL_SEASONS,
    build_frozen_v1_batting_leaderboard,
    compute_v1_external_validity,
    file_sha256,
    require_stage0_seasons,
    summarize_leaderboard,
)


MLB_STATS_URL = "https://statsapi.mlb.com/api/v1/stats"
MLB_LEAGUE_IDS = (103, 104)
REQUIRED_STAT_FIELDS = (
    "plateAppearances",
    "atBats",
    "hits",
    "doubles",
    "triples",
    "homeRuns",
    "baseOnBalls",
    "intentionalWalks",
    "hitByPitch",
    "strikeOuts",
    "sacFlies",
    "sacBunts",
)


def _integer(value: Any, *, field: str) -> int:
    number = float(str(value))
    if not number.is_integer() or number < 0:
        raise ValueError(f"invalid official integer {field}={value!r}")
    return int(number)


def _fetch_official_outcomes(
    seasons: tuple[int, ...],
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    require_stage0_seasons(seasons)
    rows: list[dict[str, object]] = []
    captures: list[dict[str, object]] = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-hitter-v2-stage0/0.1"
        for season in seasons:
            for league_id in MLB_LEAGUE_IDS:
                offset = 0
                while True:
                    params = {
                        "stats": "season",
                        "group": "hitting",
                        "season": season,
                        "sportIds": 1,
                        "leagueId": league_id,
                        "playerPool": "ALL",
                        "gameType": "R",
                        "limit": 500,
                        "offset": offset,
                    }
                    response = session.get(MLB_STATS_URL, params=params, timeout=120)
                    response.raise_for_status()
                    payload = response.json()
                    groups = payload.get("stats") or []
                    if len(groups) != 1:
                        raise RuntimeError("official MLB response did not contain one stats group")
                    group = groups[0]
                    splits = group.get("splits") or []
                    total = int(group.get("totalSplits") or len(splits))
                    captures.append(
                        {
                            "season": season,
                            "league_id": league_id,
                            "offset": offset,
                            "requested_limit": 500,
                            "returned_split_count": len(splits),
                            "reported_total_splits": total,
                            "response_byte_count": len(response.content),
                            "response_sha256": sha256(response.content).hexdigest(),
                        }
                    )
                    for split in splits:
                        player = split.get("player") or split.get("person") or {}
                        stat = split.get("stat") or {}
                        missing = [field for field in REQUIRED_STAT_FIELDS if field not in stat]
                        if missing:
                            raise RuntimeError(
                                f"official MLB split missing {missing} for {player.get('id')}"
                            )
                        rows.append(
                            {
                                "season": season,
                                "league_id": league_id,
                                "player_id": _integer(player.get("id"), field="player.id"),
                                "player_name": str(player.get("fullName") or ""),
                                "pa": _integer(stat["plateAppearances"], field="PA"),
                                "ab": _integer(stat["atBats"], field="AB"),
                                "h": _integer(stat["hits"], field="H"),
                                "double": _integer(stat["doubles"], field="2B"),
                                "triple": _integer(stat["triples"], field="3B"),
                                "hr": _integer(stat["homeRuns"], field="HR"),
                                "bb": _integer(stat["baseOnBalls"], field="BB"),
                                "ibb": _integer(stat["intentionalWalks"], field="IBB"),
                                "hbp": _integer(stat["hitByPitch"], field="HBP"),
                                "k": _integer(stat["strikeOuts"], field="K"),
                                "sf": _integer(stat["sacFlies"], field="SF"),
                                "sh": _integer(stat["sacBunts"], field="SH"),
                            }
                        )
                    if offset + len(splits) >= total or not splits:
                        break
                    offset += len(splits)

    raw = pl.DataFrame(rows)
    numeric = [
        column
        for column in OFFICIAL_OUTCOME_COLUMNS
        if column not in {"season", "player_id", "player_name"}
    ]
    aggregated = (
        raw.group_by(["season", "player_id"])
        .agg(
            pl.col("player_name").filter(pl.col("player_name") != "").first(),
            *[pl.col(column).sum().alias(column) for column in numeric],
        )
        .with_columns(pl.col("player_name").fill_null(""))
        .select(OFFICIAL_OUTCOME_COLUMNS)
        .sort(["season", "player_id"])
    )
    return aggregated, captures


def _git(command: str) -> str:
    return subprocess.check_output(["git", *command.split()], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--b2-profile", type=Path, required=True)
    parser.add_argument("--performance-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    seasons = require_stage0_seasons(STAGE0_ALLOWED_OFFICIAL_SEASONS)
    leaderboard = build_frozen_v1_batting_leaderboard(
        b2_profile_path=args.b2_profile,
        performance_root=args.performance_root,
    )
    official, captures = _fetch_official_outcomes(seasons)
    result = {
        "report_schema_version": "0.1",
        "gate": "hitter_v2_stage0_v1_external_validity_reproduction",
        "status": "reproduced_stage0_only_no_hitter_v2_candidate_scored",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": {
            "base_main_commit": "197d21a67d707633cb47d720c84a7b126b9c4320",
            "materialization_head": _git("rev-parse HEAD"),
            "branch": _git("branch --show-current"),
        },
        "boundary": {
            "official_outcome_seasons_accessed": list(seasons),
            "2024_already_disclosed_before_stage0": True,
            "2025_offense_accessed_by_this_materialization": False,
            "2026_offense_accessed_by_this_materialization": False,
            "hitter_v2_candidate_fit": False,
            "hitter_v2_candidate_scored": False,
            "protected_confirmation_opened": False,
        },
        "source": {
            "official_outcomes": {
                "provider": "MLB Stats API",
                "endpoint": MLB_STATS_URL,
                "contract": {
                    "stats": "season",
                    "group": "hitting",
                    "sportIds": 1,
                    "leagueIds": list(MLB_LEAGUE_IDS),
                    "playerPool": "ALL",
                    "gameType": "R",
                },
                "captures": captures,
                "raw_payloads_persisted": False,
                "raw_payload_policy": "private quarantine only; hashes retained here",
            },
            "frozen_artifacts": {
                "b2_profile": {
                    "path_role": "projection_2023_to_2024/frozen_b2_profile.parquet",
                    "sha256": file_sha256(args.b2_profile),
                },
                "performance_tables": [
                    {
                        "path_role": name,
                        "sha256": file_sha256(args.performance_root / "tables" / name),
                    }
                    for name in (
                        "batting_performance_summary_2024_mlb.parquet",
                        "batting_performance_bins_2024_mlb.parquet",
                        "league_bin_values_2024_mlb.parquet",
                    )
                ],
            },
            "woba_constants": {
                "provider": "FanGraphs Guts! seasonal constants",
                "season": 2024,
                "methodology_url": "https://library.fangraphs.com/offense/woba/",
                "constants_url": "https://www.fangraphs.com/tools/guts",
                "accessed_date": "2026-08-23",
            },
        },
        "frozen_v1_leaderboard": summarize_leaderboard(leaderboard),
        "external_validity": compute_v1_external_validity(
            leaderboard=leaderboard,
            official_outcomes=official,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
