#!/usr/bin/env python3
"""Materialize official MLB position usage for complete 2004-2025 seasons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl
import requests

from universal_baseball.mlb_season_stats import MLB_STATS_URL, _statsapi_get_with_retry
from universal_baseball.position_role_source import project_fielding_usage_splits
from universal_baseball.source_capture import (
    load_parsed_json_captures,
    persist_parsed_json_captures,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FETCH_SEASONS = tuple(range(2004, 2021))
MLB_LEAGUES = (103, 104)
PAGE_LIMIT = 500
OUTPUT_ROOT = Path("reports/generated/mlb-fielding-outcome-inventory-2004-2025")


def _page(
    session: requests.Session, *, season: int, league_id: int, offset: int
) -> tuple[list[Mapping[str, Any]], int | None, dict[str, object]]:
    response = _statsapi_get_with_retry(
        session,
        MLB_STATS_URL,
        params={
            "stats": "season",
            "group": "fielding",
            "season": season,
            "leagueId": league_id,
            "playerPool": "ALL",
            "gameType": "R",
            "limit": PAGE_LIMIT,
            "offset": offset,
        },
        timeout_seconds=120,
    )
    payload = response.json()
    groups = payload.get("stats") or []
    if len(groups) != 1 or not isinstance(groups[0], Mapping):
        raise RuntimeError("fielding response must contain exactly one stats group")
    splits = groups[0].get("splits") or []
    if not isinstance(splits, list) or any(not isinstance(row, Mapping) for row in splits):
        raise RuntimeError("fielding response has invalid split rows")
    total = groups[0].get("totalSplits")
    return list(splits), int(total) if total is not None else None, {
        "requested_url": response.url,
        "status_code": int(response.status_code),
        "source_snapshot_id": (
            f"statsapi:mlb-fielding-outcome:{season}:{league_id}:{offset}"
        ),
        "payload": payload,
    }


def _fetch_all() -> tuple[list[pl.DataFrame], list[tuple[str, dict[str, object]]]]:
    frames: list[pl.DataFrame] = []
    captures: list[tuple[str, dict[str, object]]] = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-fielding-outcome/0.1"
        for season in FETCH_SEASONS:
            for league_id in MLB_LEAGUES:
                splits: list[Mapping[str, Any]] = []
                offset = 0
                expected: int | None = None
                while True:
                    rows, total, capture = _page(
                        session, season=season, league_id=league_id, offset=offset
                    )
                    if expected is None:
                        expected = total
                    elif total is not None and total != expected:
                        raise RuntimeError("fielding pagination total changed")
                    splits.extend(rows)
                    captures.append(
                        (f"fielding-{season}-{league_id}-{offset}.json", capture)
                    )
                    if expected is not None and len(splits) >= expected:
                        break
                    if not rows or len(rows) < PAGE_LIMIT:
                        break
                    offset += len(rows)
                if not splits or expected is not None and len(splits) != expected:
                    raise RuntimeError(
                        f"incomplete fielding source for {season} league {league_id}"
                    )
                frames.append(
                    project_fielding_usage_splits(
                        splits, season=season, league_id=league_id, level_group="MLB"
                    )
                )
    return frames, captures


def _load_captures(root: Path) -> list[pl.DataFrame]:
    frames: list[pl.DataFrame] = []
    grouped: dict[tuple[int, int], list[Mapping[str, Any]]] = {}
    for name, capture in sorted(load_parsed_json_captures(root).items()):
        parts = name.removesuffix(".json").split("-")
        if len(parts) != 4 or parts[0] != "fielding":
            continue
        season, league_id = int(parts[1]), int(parts[2])
        payload = capture["payload"]
        groups = payload.get("stats") or []
        if len(groups) != 1:
            raise RuntimeError("retained fielding capture has invalid stats group")
        grouped.setdefault((season, league_id), []).extend(groups[0].get("splits") or [])
    for season in FETCH_SEASONS:
        for league_id in MLB_LEAGUES:
            splits = grouped.get((season, league_id), [])
            if not splits:
                raise RuntimeError(f"retained fielding capture missing {season}/{league_id}")
            frames.append(
                project_fielding_usage_splits(
                    splits, season=season, league_id=league_id, level_group="MLB"
                )
            )
    return frames


def main() -> int:
    capture_root = OUTPUT_ROOT / "captures"
    if capture_root.is_dir():
        early = _load_captures(capture_root)
        acquisition = "official_statsapi_capture_hash_verified"
    else:
        early, captures = _fetch_all()
        persist_parsed_json_captures(captures, capture_root)
        acquisition = "official_statsapi_capture_hash_verified"

    historical_path = Path(
        "reports/generated/position-capacity-source/historical/reports/generated/"
        "position-role-historical-source/tables/historical_fielding_usage.parquet"
    )
    current_path = Path(
        "reports/generated/position-capacity-source/2025/reports/generated/"
        "position-role-2025-confirmation-source/tables/"
        "position_role_2025_fielding_usage.parquet"
    )
    later = [
        pl.read_parquet(historical_path).filter(pl.col("level_group") == "MLB"),
        pl.read_parquet(current_path).filter(pl.col("level_group") == "MLB"),
    ]
    result = pl.concat([*early, *later], how="vertical_relaxed").sort(
        ["season", "league_id", "team_id", "player_id", "position_code"]
    )
    key = ["season", "league_id", "team_id", "player_id", "position_code"]
    if result.group_by(key).len().filter(pl.col("len") != 1).height:
        raise RuntimeError("MLB fielding outcome inventory violates source grain")
    if result.get_column("season").unique().sort().to_list() != list(range(2004, 2026)):
        raise RuntimeError("MLB fielding outcome inventory has incomplete seasons")

    table_root = OUTPUT_ROOT / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result,
        table_root / "mlb_fielding_usage_2004_2025.parquet",
        table_name="mlb_fielding_outcome_inventory_2004_2025",
    ).as_record()
    coverage = (
        result.group_by("season")
        .agg(
            pl.col("player_id").n_unique().alias("players"),
            pl.len().alias("position_rows"),
            pl.col("fielding_outs").sum().alias("fielding_outs"),
            pl.col("games_started").sum().alias("games_started"),
        )
        .sort("season")
    )
    report = {
        "status": "mlb_fielding_outcome_inventory_materialized",
        "source": "official_mlb_statsapi_season_fielding",
        "seasons": [2004, 2025],
        "rows": result.height,
        "players": result.get_column("player_id").n_unique(),
        "acquisition": acquisition,
        "coverage": coverage.to_dicts(),
        "boundaries": {
            "complete_regular_seasons_only": True,
            "position_usage_not_defensive_quality": True,
            "outside_fv_used": False,
            "war_or_value_assigned": False,
            "later_retrieval_not_vintage_snapshot": True,
        },
        "source_files": {
            historical_path.as_posix(): sha256_file(historical_path),
            current_path.as_posix(): sha256_file(current_path),
        },
        "storage": storage,
    }
    Path("docs/mlb-fielding-outcome-inventory-result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    Path("docs/mlb-fielding-outcome-inventory-result.md").write_text(
        "\n".join([
            "# MLB fielding outcome inventory",
            "",
            "Official MLB position usage now covers every complete season from 2004 through 2025.",
            f"The retained table contains {result.height:,} player/team/position rows and "
            f"{result.get_column('player_id').n_unique():,} players.",
            "",
            "This is position-usage evidence only. It does not measure defensive quality, assign WAR, "
            "or use public FV. Its next use is a strict historical test of position-adjusted prospect outcomes.",
            "",
        ]),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key not in {"coverage", "storage"}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
