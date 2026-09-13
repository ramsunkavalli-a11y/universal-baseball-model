#!/usr/bin/env python3
"""Materialize official MiLB position usage at historical prospect origins."""

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
from universal_baseball.storage import write_canonical_parquet


ORIGIN_SEASONS = (2008, 2013, 2016, 2018, 2019, 2021)
SPORT_LEVELS = {
    11: "AAA",
    12: "AA",
    13: "HIGH_A",
    14: "SINGLE_A",
    16: "ROOKIE_COMPLEX",
}
PAGE_LIMIT = 500
OUTPUT_ROOT = Path("reports/generated/milb-fielding-origin-inventory")


def _page(
    session: requests.Session, *, season: int, sport_id: int, offset: int
) -> tuple[list[Mapping[str, Any]], int | None, dict[str, object]]:
    response = _statsapi_get_with_retry(
        session,
        MLB_STATS_URL,
        params={
            "stats": "season",
            "group": "fielding",
            "season": season,
            "sportId": sport_id,
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
    total = groups[0].get("totalSplits")
    return list(splits), int(total) if total is not None else None, {
        "requested_url": response.url,
        "status_code": int(response.status_code),
        "source_snapshot_id": f"statsapi:milb-fielding-origin:{season}:{sport_id}:{offset}",
        "payload": payload,
    }


def _fetch_all() -> tuple[dict[tuple[int, int], list[Mapping[str, Any]]], list[tuple[str, dict[str, object]]]]:
    grouped: dict[tuple[int, int], list[Mapping[str, Any]]] = {}
    captures: list[tuple[str, dict[str, object]]] = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-milb-position/0.1"
        for season in ORIGIN_SEASONS:
            for sport_id in SPORT_LEVELS:
                rows: list[Mapping[str, Any]] = []
                offset = 0
                expected: int | None = None
                while True:
                    page, total, capture = _page(
                        session, season=season, sport_id=sport_id, offset=offset
                    )
                    expected = total if expected is None else expected
                    if total is not None and total != expected:
                        raise RuntimeError("fielding pagination total changed")
                    rows.extend(page)
                    captures.append(
                        (f"fielding-{season}-{sport_id}-{offset}.json", capture)
                    )
                    if expected is not None and len(rows) >= expected:
                        break
                    if not page or len(page) < PAGE_LIMIT:
                        break
                    offset += len(page)
                if not rows or expected is not None and len(rows) != expected:
                    raise RuntimeError(f"incomplete fielding source for {season}/{sport_id}")
                grouped[(season, sport_id)] = rows
    return grouped, captures


def _load_captures(root: Path) -> dict[tuple[int, int], list[Mapping[str, Any]]]:
    grouped: dict[tuple[int, int], list[Mapping[str, Any]]] = {}
    for name, capture in sorted(load_parsed_json_captures(root).items()):
        parts = name.removesuffix(".json").split("-")
        if len(parts) != 4 or parts[0] != "fielding":
            continue
        key = (int(parts[1]), int(parts[2]))
        groups = capture["payload"].get("stats") or []
        if len(groups) != 1:
            raise RuntimeError("retained fielding capture has invalid stats group")
        grouped.setdefault(key, []).extend(groups[0].get("splits") or [])
    return grouped


def _project(grouped: dict[tuple[int, int], list[Mapping[str, Any]]]) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for season in ORIGIN_SEASONS:
        for sport_id, level in SPORT_LEVELS.items():
            splits = grouped.get((season, sport_id), [])
            if not splits:
                raise RuntimeError(f"missing retained fielding source for {season}/{sport_id}")
            by_league: dict[int, list[Mapping[str, Any]]] = {}
            for split in splits:
                league = split.get("league") or {}
                league_id = int(league.get("id") or 0)
                if league_id <= 0:
                    raise RuntimeError("fielding split lacks league identity")
                by_league.setdefault(league_id, []).append(split)
            frames.extend(
                project_fielding_usage_splits(
                    rows,
                    season=season,
                    league_id=league_id,
                    level_group=level,
                )
                for league_id, rows in sorted(by_league.items())
            )
    result = pl.concat(frames, how="vertical_relaxed").sort(
        ["season", "league_id", "team_id", "player_id", "position_code"]
    )
    key = ["season", "league_id", "team_id", "player_id", "position_code"]
    if result.group_by(key).len().filter(pl.col("len") != 1).height:
        raise RuntimeError("MiLB fielding origin inventory violates source grain")
    return result


def main() -> int:
    capture_root = OUTPUT_ROOT / "captures"
    if capture_root.is_dir():
        grouped = _load_captures(capture_root)
        required = {
            (season, sport_id)
            for season in ORIGIN_SEASONS
            for sport_id in SPORT_LEVELS
        }
        if set(grouped) != required:
            grouped, captures = _fetch_all()
            persist_parsed_json_captures(captures, capture_root)
    else:
        grouped, captures = _fetch_all()
        persist_parsed_json_captures(captures, capture_root)
    result = _project(grouped)
    table_root = OUTPUT_ROOT / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result,
        table_root / "milb_fielding_usage_at_origins.parquet",
        table_name="milb_fielding_usage_at_prospect_origins",
    ).as_record()
    coverage = (
        result.group_by("season", "level_group")
        .agg(
            pl.col("player_id").n_unique().alias("players"),
            pl.len().alias("position_rows"),
        )
        .sort("season", "level_group")
    )
    report = {
        "status": "milb_fielding_origin_inventory_materialized",
        "source": "official_mlb_statsapi_season_fielding",
        "origin_seasons": list(ORIGIN_SEASONS),
        "sport_levels": SPORT_LEVELS,
        "rows": result.height,
        "players": result["player_id"].n_unique(),
        "coverage": coverage.to_dicts(),
        "unavailable_origin": {
            "season": 2003,
            "reason": "StatsAPI returned zero fielding splits for all five affiliated sport levels",
        },
        "boundaries": {
            "position_usage_only": True,
            "outside_fv_used": False,
            "model_fit": False,
        },
        "storage": storage,
    }
    Path("docs/milb-fielding-origin-inventory-result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    Path("docs/milb-fielding-origin-inventory-result.md").write_text(
        "\n".join(
            [
                "# MiLB fielding origin inventory",
                "",
                "Official position usage was retained at the 2008, 2013, 2016, 2018, 2019 and 2021 prospect origins.",
                f"The source contains {result.height:,} player/team/position rows for {result['player_id'].n_unique():,} players.",
                "StatsAPI returned no fielding splits at the five affiliated levels for 2003, so that origin is explicitly unavailable rather than inferred.",
                "",
                "This source measures usage, not defensive quality, FV or player value.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in report.items() if key not in {"coverage", "storage"}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
