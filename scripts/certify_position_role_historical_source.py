#!/usr/bin/env python3
"""Certify official 2021-2024 player position/role source evidence.

Consumes only completed regular-season Stats API `fielding` and same-league
`hitting` surfaces for the frozen MLB/affiliated actual-league map. It preserves
raw response bytes and produces exact games-started / defensive-out evidence.
No position model is fit and no 2025 source is queried.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import polars as pl
import requests

from universal_baseball.mlb_season_stats import MLB_STATS_URL, _statsapi_get_with_retry
from universal_baseball.position_role_source import (
    project_fielding_usage_splits,
    project_hitting_player_ids,
)
from universal_baseball.storage import write_canonical_parquet


SEASONS = (2021, 2022, 2023, 2024)
LEAGUES: tuple[tuple[int, str], ...] = (
    (103, "MLB"),
    (104, "MLB"),
    (112, "AAA"),
    (117, "AAA"),
    (109, "AA"),
    (111, "AA"),
    (113, "AA"),
    (116, "HIGH_A"),
    (118, "HIGH_A"),
    (126, "HIGH_A"),
    (110, "SINGLE_A"),
    (122, "SINGLE_A"),
    (123, "SINGLE_A"),
    (121, "ROOKIE_COMPLEX"),
    (124, "ROOKIE_COMPLEX"),
    (130, "ROOKIE_COMPLEX"),
)
GROUPS = ("fielding", "hitting")
PAGE_LIMIT = 500
REPORT_ROOT = Path("reports/generated/position-role-historical-source")
CAPTURE_ROOT = Path("data/quarantine/position-role-historical-source")


def _capture_page(
    session: requests.Session,
    *,
    season: int,
    league_id: int,
    group: str,
    offset: int,
) -> tuple[list[Mapping[str, Any]], int | None, dict[str, Any]]:
    params = {
        "stats": "season",
        "group": group,
        "season": int(season),
        "leagueId": int(league_id),
        "playerPool": "ALL",
        "gameType": "R",
        "limit": PAGE_LIMIT,
        "offset": int(offset),
    }
    response = _statsapi_get_with_retry(
        session,
        MLB_STATS_URL,
        params=params,
        timeout_seconds=120,
    )
    content = response.content
    payload = response.json()
    stats_groups = payload.get("stats") or []
    if len(stats_groups) != 1:
        raise RuntimeError(
            f"expected one stats group season={season} league={league_id} "
            f"group={group}, observed={len(stats_groups)}"
        )
    stats_group = stats_groups[0]
    splits = stats_group.get("splits") or []
    if not isinstance(splits, list) or any(not isinstance(row, Mapping) for row in splits):
        raise RuntimeError(
            f"invalid splits season={season} league={league_id} group={group} offset={offset}"
        )
    total = stats_group.get("totalSplits")
    total_int = int(total) if total is not None else None

    capture_path = (
        CAPTURE_ROOT
        / str(season)
        / str(league_id)
        / f"{group}_offset_{offset}.json"
    )
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    capture_path.write_bytes(content)
    capture = {
        "season": int(season),
        "league_id": int(league_id),
        "group": group,
        "offset": int(offset),
        "requested_limit": PAGE_LIMIT,
        "requested_url": response.url,
        "status_code": int(response.status_code),
        "response_byte_count": len(content),
        "response_sha256": sha256(content).hexdigest(),
        "returned_split_count": len(splits),
        "reported_total_splits": total_int,
        "capture_path": str(capture_path),
    }
    return list(splits), total_int, capture


def _fetch_group(
    session: requests.Session,
    *,
    season: int,
    league_id: int,
    group: str,
) -> tuple[list[Mapping[str, Any]], list[dict[str, Any]]]:
    all_splits: list[Mapping[str, Any]] = []
    captures: list[dict[str, Any]] = []
    offset = 0
    reported_total: int | None = None
    while True:
        splits, total, capture = _capture_page(
            session,
            season=season,
            league_id=league_id,
            group=group,
            offset=offset,
        )
        captures.append(capture)
        all_splits.extend(splits)
        if total is not None:
            if reported_total is None:
                reported_total = total
            elif reported_total != total:
                raise RuntimeError(
                    f"totalSplits changed season={season} league={league_id} group={group}: "
                    f"{reported_total} -> {total}"
                )
        if reported_total is not None and len(all_splits) >= reported_total:
            break
        if not splits or len(splits) < PAGE_LIMIT:
            break
        offset += len(splits)
        if offset > 10_000:
            raise RuntimeError(
                f"pagination safety bound exceeded season={season} league={league_id} group={group}"
            )
    if not all_splits:
        raise RuntimeError(
            f"empty source season={season} league={league_id} group={group}"
        )
    if reported_total is not None and len(all_splits) != reported_total:
        raise RuntimeError(
            f"incomplete pagination season={season} league={league_id} group={group}: "
            f"observed={len(all_splits)}, reported={reported_total}"
        )
    return all_splits, captures


def _coverage_row(
    frame: pl.DataFrame,
    hitting_ids: set[int],
    *,
    season: int,
    league_id: int,
    level_group: str,
) -> tuple[dict[str, Any], dict[str, object]]:
    fielding_ids = set(int(value) for value in frame.get_column("player_id").unique().to_list())
    missing = sorted(hitting_ids - fielding_ids)
    hitter_usage = frame.filter(pl.col("player_id").is_in(list(hitting_ids)))
    starts = (
        hitter_usage.group_by("player_id")
        .agg(pl.col("games_started").sum().alias("total_games_started"))
        if not hitter_usage.is_empty()
        else pl.DataFrame({"player_id": [], "total_games_started": []})
    )
    zero_start_ids = (
        starts.filter(pl.col("total_games_started") == 0).get_column("player_id").to_list()
        if not starts.is_empty()
        else []
    )
    position_rows = (
        frame.group_by("position_abbreviation")
        .agg(
            pl.len().alias("source_rows"),
            pl.col("games_started").sum().alias("games_started"),
            pl.col("fielding_outs").sum().alias("fielding_outs"),
        )
        .sort("position_abbreviation")
        .to_dicts()
    )
    report = {
        "season": int(season),
        "league_id": int(league_id),
        "level_group": level_group,
        "fielding_row_count": int(frame.height),
        "fielding_unique_player_count": len(fielding_ids),
        "hitting_unique_player_count": len(hitting_ids),
        "hitting_players_without_fielding_count": len(missing),
        "hitting_players_without_fielding_examples": missing[:25],
        "hitting_players_with_fielding_but_zero_games_started_count": len(zero_start_ids),
        "hitting_players_with_fielding_but_zero_games_started_examples": sorted(
            int(value) for value in zero_start_ids
        )[:25],
        "position_totals": position_rows,
    }
    table_row: dict[str, object] = {
        "season": int(season),
        "league_id": int(league_id),
        "level_group": level_group,
        "fielding_rows": int(frame.height),
        "fielding_players": len(fielding_ids),
        "hitting_players": len(hitting_ids),
        "hitting_players_missing_fielding": len(missing),
        "hitting_players_zero_starts": len(zero_start_ids),
    }
    return report, table_row


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    CAPTURE_ROOT.mkdir(parents=True, exist_ok=True)
    table_root = REPORT_ROOT / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-position-role-historical-source/0.1"
    fielding_frames: list[pl.DataFrame] = []
    audit_rows: list[dict[str, Any]] = []
    coverage_table_rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    capture_records: list[dict[str, Any]] = []
    try:
        for season in SEASONS:
            for league_id, level_group in LEAGUES:
                try:
                    fielding_splits, fielding_captures = _fetch_group(
                        session,
                        season=season,
                        league_id=league_id,
                        group="fielding",
                    )
                    hitting_splits, hitting_captures = _fetch_group(
                        session,
                        season=season,
                        league_id=league_id,
                        group="hitting",
                    )
                    capture_records.extend(fielding_captures)
                    capture_records.extend(hitting_captures)
                    fielding = project_fielding_usage_splits(
                        fielding_splits,
                        season=season,
                        league_id=league_id,
                        level_group=level_group,
                    )
                    hitting_ids = project_hitting_player_ids(hitting_splits)
                    coverage, coverage_table = _coverage_row(
                        fielding,
                        hitting_ids,
                        season=season,
                        league_id=league_id,
                        level_group=level_group,
                    )
                    coverage.update(
                        {
                            "fielding_page_count": len(fielding_captures),
                            "hitting_page_count": len(hitting_captures),
                            "fielding_capture_sha256": [
                                row["response_sha256"] for row in fielding_captures
                            ],
                            "hitting_capture_sha256": [
                                row["response_sha256"] for row in hitting_captures
                            ],
                            "accepted": True,
                        }
                    )
                    audit_rows.append(coverage)
                    coverage_table_rows.append(coverage_table)
                    fielding_frames.append(fielding)
                except Exception as exc:
                    errors.append(
                        {
                            "season": int(season),
                            "league_id": int(league_id),
                            "level_group": level_group,
                            "type": type(exc).__name__,
                            "message": str(exc),
                        }
                    )
                    audit_rows.append(
                        {
                            "season": int(season),
                            "league_id": int(league_id),
                            "level_group": level_group,
                            "accepted": False,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
    finally:
        session.close()

    expected_pairs = len(SEASONS) * len(LEAGUES)
    accepted = bool(
        len(audit_rows) == expected_pairs
        and len(fielding_frames) == expected_pairs
        and not errors
        and all(bool(row.get("accepted")) for row in audit_rows)
    )

    storage: dict[str, Any] = {}
    if fielding_frames:
        combined = pl.concat(fielding_frames, how="vertical_relaxed").sort(
            ["season", "league_id", "team_id", "player_id", "position_code"]
        )
        combined_key = ["season", "league_id", "team_id", "player_id", "position_code"]
        if combined.group_by(combined_key).len().filter(pl.col("len") != 1).height:
            raise RuntimeError("combined historical fielding source violates canonical grain")
        storage["fielding_usage"] = write_canonical_parquet(
            combined,
            table_root / "historical_fielding_usage.parquet",
            table_name="position_role_historical_fielding_usage_2021_2024",
        ).as_record()
    if coverage_table_rows:
        coverage_frame = pl.DataFrame(coverage_table_rows).sort(["season", "league_id"])
        storage["coverage"] = write_canonical_parquet(
            coverage_frame,
            table_root / "historical_fielding_coverage.parquet",
            table_name="position_role_historical_fielding_coverage_2021_2024",
        ).as_record()

    report = {
        "report_schema_version": "0.1",
        "gate": "position_role_historical_source_certification_2021_2024",
        "contract": "docs/position-role-historical-source-certification-contract.md",
        "source": "official_mlb_stats_api_stats_season",
        "seasons": list(SEASONS),
        "league_map": [
            {"league_id": league_id, "level_group": level_group}
            for league_id, level_group in LEAGUES
        ],
        "expected_season_league_pairs": expected_pairs,
        "successful_season_league_pairs": len(fielding_frames),
        "audits": audit_rows,
        "source_errors": errors,
        "capture_record_count": len(capture_records),
        "capture_records": capture_records,
        "storage": storage,
        "decision": {
            "historical_position_role_source_certified": accepted,
            "position_profile_design_authorized_next": accepted,
            "position_model_authorized": False,
            "defense_model_authorized": False,
            "team_allocator_authorized": False,
        },
        "boundary": {
            "2025_accessed": False,
            "2025_batting_rate_outcomes_accessed": False,
            "model_fit": False,
            "future_position_projected": False,
            "playing_time_v1_modified": False,
            "team_allocation_performed": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    total_fielding_rows = sum(int(row.get("fielding_row_count", 0)) for row in audit_rows)
    total_hitting_players = sum(int(row.get("hitting_unique_player_count", 0)) for row in audit_rows)
    total_missing = sum(int(row.get("hitting_players_without_fielding_count", 0)) for row in audit_rows)
    lines = [
        "# Position / role historical source certification — 2021–2024",
        "",
        f"- Certified: {accepted}",
        f"- Successful season × league pairs: {len(fielding_frames)}/{expected_pairs}",
        f"- Canonical fielding rows across successful pairs: {total_fielding_rows:,}",
        f"- Same-league hitting player observations: {total_hitting_players:,}",
        f"- Hitting-player observations missing fielding evidence: {total_missing:,}",
        f"- Raw source capture pages retained: {len(capture_records):,}",
        "- Position model fit: False",
        "- Team allocation performed: False",
        "- 2025 accessed: False",
        "",
    ]
    if errors:
        lines.append("## Source errors")
        lines.extend(
            f"- {row['season']} league {row['league_id']}: {row['type']}: {row['message']}"
            for row in errors
        )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    if not accepted:
        raise RuntimeError("historical position/role source certification failed closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
