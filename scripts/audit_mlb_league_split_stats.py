#!/usr/bin/env python
"""Test whether MLB bulk season stats support actual AL/NL player grain.

The universal Performance summary keeps ``player + actual league + season`` as
its canonical grain. MLB players can switch between the American and National
Leagues during a season, so the MLB-wide bulk season result is insufficient if
we want the same contract without silently collapsing cross-league evidence.

This audit fetches the completed 2024 MLB-wide, AL (103), and NL (104) bulk
hitting endpoints and tests whether the two league-filtered rows decompose the
MLB-wide player totals exactly for the standard Performance backbone fields.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl
import requests


REPORT_DIR = Path("reports/generated/mlb-league-split-stats")
URL = "https://statsapi.mlb.com/api/v1/stats"
SEASON = 2024
PAGE_LIMIT = 500
LEAGUES = {103: "AL", 104: "NL"}
FIELDS = (
    "plateAppearances",
    "atBats",
    "baseOnBalls",
    "intentionalWalks",
    "hitByPitch",
    "strikeOuts",
    "sacBunts",
    "sacFlies",
)


def _int(value: Any) -> int:
    if value is None or str(value).strip() == "":
        return 0
    numeric = float(str(value))
    if not numeric.is_integer():
        raise ValueError(f"expected integer-like count, got {value!r}")
    return int(numeric)


def _fetch(league_id: int | None) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    captures: list[dict[str, Any]] = []
    offset = 0
    session = requests.Session()
    try:
        while True:
            params: dict[str, Any] = {
                "stats": "season",
                "group": "hitting",
                "season": SEASON,
                "sportIds": 1,
                "playerPool": "ALL",
                "gameType": "R",
                "limit": PAGE_LIMIT,
                "offset": offset,
            }
            if league_id is not None:
                params["leagueId"] = league_id
            response = session.get(URL, params=params, timeout=120)
            response.raise_for_status()
            payload = response.json()
            groups = payload.get("stats") or []
            if len(groups) != 1:
                raise RuntimeError(f"unexpected stats-group count: {len(groups)}")
            group = groups[0]
            splits = group.get("splits") or []
            captures.append(
                {
                    "league_id": league_id,
                    "offset": offset,
                    "returned_split_count": len(splits),
                    "total_splits": group.get("totalSplits"),
                    "response_sha256": sha256(response.content).hexdigest(),
                    "response_byte_count": len(response.content),
                }
            )
            for split in splits:
                person: Mapping[str, Any] = split.get("player") or split.get("person") or {}
                stat: Mapping[str, Any] = split.get("stat") or {}
                player_id = _int(person.get("id"))
                if not player_id:
                    raise RuntimeError("league split lacks MLBAM player ID")
                rows.append(
                    {
                        "season": SEASON,
                        "league_id": league_id,
                        "player_id": player_id,
                        "player_name": str(person.get("fullName") or ""),
                        **{field: _int(stat.get(field)) for field in FIELDS},
                    }
                )
            total = group.get("totalSplits")
            if total is not None and len(rows) >= int(total):
                break
            if len(splits) < PAGE_LIMIT or not splits:
                break
            offset += len(splits)
    finally:
        session.close()
    frame = pl.DataFrame(rows)
    if not frame.is_empty():
        frame = frame.with_columns(
            pl.col("season").cast(pl.Int64),
            pl.col("player_id").cast(pl.Int64),
            pl.col("league_id").cast(pl.Int64, strict=False),
            *[pl.col(field).cast(pl.Int64) for field in FIELDS],
        )
    return frame, captures


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    overall, overall_captures = _fetch(None)
    league_frames: list[pl.DataFrame] = []
    captures: list[dict[str, Any]] = list(overall_captures)
    for league_id in LEAGUES:
        frame, league_captures = _fetch(league_id)
        if frame.is_empty():
            raise RuntimeError(f"league {league_id} bulk season endpoint is empty")
        league_frames.append(frame)
        captures.extend(league_captures)
    leagues = pl.concat(league_frames, how="vertical_relaxed")

    duplicate_league_rows = (
        leagues.group_by(["season", "league_id", "player_id"])
        .len()
        .filter(pl.col("len") > 1)
    )
    summed = leagues.group_by(["season", "player_id"]).agg(
        *[pl.col(field).sum().alias(f"league_sum_{field}") for field in FIELDS],
        pl.col("league_id").n_unique().alias("league_count"),
    )
    comparison = overall.join(summed, on=["season", "player_id"], how="full", coalesce=True)
    for field in FIELDS:
        comparison = comparison.with_columns(
            (
                pl.col(f"league_sum_{field}").fill_null(0)
                - pl.col(field).fill_null(0)
            ).alias(f"difference_{field}")
        )
    mismatch_expr = pl.any_horizontal(
        [pl.col(f"difference_{field}") != 0 for field in FIELDS]
    )
    mismatches = comparison.filter(mismatch_expr)
    cross_league = summed.filter(pl.col("league_count") > 1)
    overall_missing_from_leagues = overall.select("player_id").join(
        leagues.select("player_id").unique(), on="player_id", how="anti"
    )
    league_missing_from_overall = leagues.select("player_id").unique().join(
        overall.select("player_id"), on="player_id", how="anti"
    )

    mismatches.write_csv(REPORT_DIR / "league_sum_mismatches.csv")
    cross_league.sort("player_id").write_csv(REPORT_DIR / "cross_league_players.csv")

    totals = {
        "overall": {field: int(overall.get_column(field).sum() or 0) for field in FIELDS},
        "league_sum": {field: int(leagues.get_column(field).sum() or 0) for field in FIELDS},
    }
    payload = {
        "report_schema_version": 1,
        "season": SEASON,
        "league_ids": LEAGUES,
        "captures": captures,
        "overall_player_count": overall.height,
        "league_player_row_count": leagues.height,
        "unique_league_player_count": leagues.get_column("player_id").n_unique(),
        "cross_league_player_count": cross_league.height,
        "duplicate_player_league_key_count": duplicate_league_rows.height,
        "overall_player_missing_from_league_rows_count": overall_missing_from_leagues.height,
        "league_player_missing_from_overall_count": league_missing_from_overall.height,
        "player_count_field_mismatch_count": mismatches.height,
        "totals": totals,
        "interpretation": (
            "Exact league-sum reconciliation certifies AL/NL filtered bulk season stats "
            "as the MLB player × actual-league × season outcome backbone. A player who "
            "switches leagues remains two Performance rows; later Current Talent may "
            "combine evidence across environments explicitly."
        ),
    }
    (REPORT_DIR / "mlb_league_split_stats.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    lines = [
        "# MLB actual-league season-stat audit — 2024",
        "",
        f"- MLB-wide player rows: {overall.height:,}",
        f"- AL/NL player rows: {leagues.height:,}",
        f"- Unique players across AL/NL: {leagues.get_column('player_id').n_unique():,}",
        f"- Players with PA/counts in both leagues: {cross_league.height:,}",
        f"- Duplicate player-league keys: {duplicate_league_rows.height:,}",
        f"- Overall players absent from AL/NL rows: {overall_missing_from_leagues.height:,}",
        f"- League rows absent from MLB-wide result: {league_missing_from_overall.height:,}",
        f"- Players whose AL+NL counts differ from MLB-wide counts: {mismatches.height:,}",
    ]
    summary = "\n".join(lines)
    (REPORT_DIR / "mlb_league_split_stats.md").write_text(summary, encoding="utf-8")
    print(summary)

    if duplicate_league_rows.height:
        raise RuntimeError("AL/NL bulk result has duplicate player-league keys")
    if overall_missing_from_leagues.height or league_missing_from_overall.height:
        raise RuntimeError("MLB-wide and AL/NL player sets do not reconcile")
    if mismatches.height:
        raise RuntimeError("AL+NL player counts do not exactly reconstruct MLB-wide totals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
