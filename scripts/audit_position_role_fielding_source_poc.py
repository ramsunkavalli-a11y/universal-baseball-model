#!/usr/bin/env python3
"""Audit official 2024 bulk fielding surfaces for position/role feasibility.

This is a source-semantic POC only. It compares same-league official Stats API
season `fielding` and `hitting` splits for six representative MLB/affiliated
leagues. It preserves raw response bytes/hashes and does not fit a model, infer
DH from missing fielding rows, or access 2025.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

import requests

from universal_baseball.mlb_season_stats import MLB_STATS_URL, _statsapi_get_with_retry


SEASON = 2024
PAGE_LIMIT = 500
REPRESENTATIVE_LEAGUES: tuple[tuple[int, str, str], ...] = (
    (103, "MLB_AL", "MLB American League"),
    (117, "AAA", "Triple-A International League"),
    (113, "AA", "Double-A Eastern League"),
    (118, "HIGH_A", "High-A Midwest League"),
    (110, "SINGLE_A", "Single-A Florida State League"),
    (121, "ROOKIE_COMPLEX", "Arizona Complex League"),
)
GROUPS = ("fielding", "hitting")
REPORT_ROOT = Path("reports/generated/position-role-fielding-source-poc")
CAPTURE_ROOT = Path("data/quarantine/position-role-fielding-source-poc")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _position_object(split: Mapping[str, Any]) -> tuple[Mapping[str, Any], str]:
    direct = _mapping(split.get("position"))
    if direct:
        return direct, "split.position"
    stat_position = _mapping(_mapping(split.get("stat")).get("position"))
    if stat_position:
        return stat_position, "stat.position"
    return {}, "missing"


def _capture_page(
    session: requests.Session,
    *,
    league_id: int,
    group: str,
    offset: int,
) -> tuple[list[Mapping[str, Any]], int | None, dict[str, Any]]:
    params = {
        "stats": "season",
        "group": group,
        "season": SEASON,
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
            f"expected one Stats API group for league={league_id} group={group}, "
            f"observed={len(stats_groups)}"
        )
    stats_group = stats_groups[0]
    splits = stats_group.get("splits") or []
    if not isinstance(splits, list) or any(not isinstance(row, Mapping) for row in splits):
        raise RuntimeError(
            f"invalid splits payload for league={league_id} group={group} offset={offset}"
        )
    total = stats_group.get("totalSplits")
    total_int = int(total) if total is not None else None

    capture_path = CAPTURE_ROOT / str(SEASON) / str(league_id) / f"{group}_offset_{offset}.json"
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    capture_path.write_bytes(content)
    capture = {
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
    league_id: int,
    group: str,
) -> tuple[list[Mapping[str, Any]], list[dict[str, Any]], bool]:
    all_splits: list[Mapping[str, Any]] = []
    captures: list[dict[str, Any]] = []
    offset = 0
    reported_total: int | None = None
    while True:
        splits, total, capture = _capture_page(
            session,
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
                    f"totalSplits changed across pages for league={league_id} group={group}: "
                    f"{reported_total} -> {total}"
                )
        if reported_total is not None and len(all_splits) >= reported_total:
            break
        if not splits or len(splits) < PAGE_LIMIT:
            break
        offset += len(splits)
        if offset > 5000:
            raise RuntimeError(
                f"pagination exceeded safety bound for league={league_id} group={group}"
            )
    complete = bool(
        all_splits
        and (
            reported_total is None
            or len(all_splits) == int(reported_total)
        )
    )
    return all_splits, captures, complete


def _split_key_inventory(splits: list[Mapping[str, Any]]) -> dict[str, list[str]]:
    split_keys: set[str] = set()
    stat_keys: set[str] = set()
    player_keys: set[str] = set()
    team_keys: set[str] = set()
    position_keys: set[str] = set()
    for split in splits:
        split_keys.update(str(key) for key in split.keys())
        stat_keys.update(str(key) for key in _mapping(split.get("stat")).keys())
        player_keys.update(str(key) for key in _mapping(split.get("player") or split.get("person")).keys())
        team_keys.update(str(key) for key in _mapping(split.get("team")).keys())
        position, _ = _position_object(split)
        position_keys.update(str(key) for key in position.keys())
    return {
        "split_keys": sorted(split_keys),
        "stat_keys": sorted(stat_keys),
        "player_keys": sorted(player_keys),
        "team_keys": sorted(team_keys),
        "position_keys": sorted(position_keys),
    }


def _player_ids(splits: list[Mapping[str, Any]]) -> tuple[set[int], int]:
    ids: set[int] = set()
    missing = 0
    for split in splits:
        player = _mapping(split.get("player") or split.get("person"))
        player_id = _int_or_none(player.get("id"))
        if player_id is None:
            missing += 1
        else:
            ids.add(player_id)
    return ids, missing


def _fielding_diagnostics(splits: list[Mapping[str, Any]]) -> dict[str, Any]:
    player_ids: set[int] = set()
    missing_player = 0
    missing_team = 0
    missing_position = 0
    position_source_counts: Counter[str] = Counter()
    position_values: set[tuple[str, str, str]] = set()
    grain_counts: Counter[tuple[int, int, str, str]] = Counter()

    for split in splits:
        player = _mapping(split.get("player") or split.get("person"))
        team = _mapping(split.get("team"))
        position, position_source = _position_object(split)
        position_source_counts[position_source] += 1

        player_id = _int_or_none(player.get("id"))
        team_id = _int_or_none(team.get("id"))
        code = str(position.get("code") or "").strip()
        abbreviation = str(position.get("abbreviation") or "").strip()
        name = str(position.get("name") or position.get("type") or "").strip()

        if player_id is None:
            missing_player += 1
        else:
            player_ids.add(player_id)
        if team_id is None:
            missing_team += 1
        if not (code or abbreviation or name):
            missing_position += 1

        if code or abbreviation or name:
            position_values.add((code, abbreviation, name))
        if player_id is not None and team_id is not None and (code or abbreviation or name):
            grain_counts[(player_id, team_id, code, abbreviation)] += 1

    duplicate_grain_rows = sum(count - 1 for count in grain_counts.values() if count > 1)
    duplicate_grain_keys = sum(1 for count in grain_counts.values() if count > 1)
    return {
        "split_count": len(splits),
        "unique_player_count": len(player_ids),
        "missing_player_id_split_count": missing_player,
        "missing_team_id_split_count": missing_team,
        "missing_position_split_count": missing_position,
        "position_source_counts": dict(sorted(position_source_counts.items())),
        "observed_positions": [
            {"code": code, "abbreviation": abbreviation, "name": name}
            for code, abbreviation, name in sorted(position_values)
        ],
        "player_team_position_duplicate_key_count": duplicate_grain_keys,
        "player_team_position_duplicate_extra_row_count": duplicate_grain_rows,
        "key_inventory": _split_key_inventory(splits),
    }


def _league_audit(
    session: requests.Session,
    *,
    league_id: int,
    level_group: str,
    display_name: str,
) -> dict[str, Any]:
    group_payloads: dict[str, list[Mapping[str, Any]]] = {}
    group_reports: dict[str, Any] = {}
    errors: list[dict[str, str]] = []

    for group in GROUPS:
        try:
            splits, captures, complete = _fetch_group(
                session,
                league_id=league_id,
                group=group,
            )
            group_payloads[group] = splits
            player_ids, missing_player = _player_ids(splits)
            group_reports[group] = {
                "request_succeeded": True,
                "pagination_complete": complete,
                "split_count": len(splits),
                "unique_player_count": len(player_ids),
                "missing_player_id_split_count": missing_player,
                "page_count": len(captures),
                "captures": captures,
                "key_inventory": _split_key_inventory(splits),
            }
        except Exception as exc:
            errors.append(
                {
                    "group": group,
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            group_reports[group] = {
                "request_succeeded": False,
                "pagination_complete": False,
                "split_count": 0,
                "unique_player_count": 0,
                "missing_player_id_split_count": None,
                "page_count": 0,
                "captures": [],
                "key_inventory": {},
            }

    hitting_splits = group_payloads.get("hitting", [])
    fielding_splits = group_payloads.get("fielding", [])
    hitting_ids, _ = _player_ids(hitting_splits)
    fielding_ids, _ = _player_ids(fielding_splits)
    missing_fielding_ids = sorted(hitting_ids - fielding_ids)
    fielding = _fielding_diagnostics(fielding_splits) if fielding_splits else {}

    request_ok = all(group_reports[group]["request_succeeded"] for group in GROUPS)
    pagination_ok = all(group_reports[group]["pagination_complete"] for group in GROUPS)
    fielding_identity_ok = bool(
        fielding
        and fielding["split_count"] > 0
        and fielding["missing_player_id_split_count"] == 0
        and fielding["missing_team_id_split_count"] == 0
        and fielding["missing_position_split_count"] == 0
    )
    unique_grain_ok = bool(
        fielding
        and fielding["player_team_position_duplicate_key_count"] == 0
    )
    viable = bool(request_ok and pagination_ok and fielding_identity_ok and unique_grain_ok and not errors)

    return {
        "league_id": int(league_id),
        "level_group": level_group,
        "display_name": display_name,
        "groups": group_reports,
        "fielding_diagnostics": fielding,
        "hitting_unique_player_count": len(hitting_ids),
        "fielding_unique_player_count": len(fielding_ids),
        "hitting_players_without_fielding_count": len(missing_fielding_ids),
        "hitting_players_without_fielding_examples": missing_fielding_ids[:25],
        "source_errors": errors,
        "acceptance": {
            "both_group_requests_succeeded": request_ok,
            "pagination_complete": pagination_ok,
            "fielding_identity_team_position_complete": fielding_identity_ok,
            "player_team_position_grain_unique": unique_grain_ok,
            "viable_for_broader_position_source_certification": viable,
        },
    }


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    CAPTURE_ROOT.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-position-role-fielding-poc/0.1"
    try:
        leagues = [
            _league_audit(
                session,
                league_id=league_id,
                level_group=level_group,
                display_name=display_name,
            )
            for league_id, level_group, display_name in REPRESENTATIVE_LEAGUES
        ]
    finally:
        session.close()

    all_viable = all(
        bool(row["acceptance"]["viable_for_broader_position_source_certification"])
        for row in leagues
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "position_role_2024_official_bulk_fielding_source_poc",
        "season": SEASON,
        "source": "official_mlb_stats_api_stats_season",
        "request_contract": {
            "stats": "season",
            "groups": list(GROUPS),
            "season": SEASON,
            "playerPool": "ALL",
            "gameType": "R",
            "sportIds_sent": False,
            "representative_leagues": [league_id for league_id, _, _ in REPRESENTATIVE_LEAGUES],
        },
        "leagues": leagues,
        "decision": {
            "all_representative_leagues_viable": all_viable,
            "broader_historical_position_source_certification_authorized": all_viable,
            "position_model_authorized": False,
            "team_allocator_authorized": False,
        },
        "boundary": {
            "2025_accessed": False,
            "2025_batting_rate_outcomes_accessed": False,
            "playing_time_v1_modified": False,
            "projection_v1_modified": False,
            "position_inferred_from_missing_fielding": False,
            "model_fit": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Position / role fielding source POC — 2024",
        "",
        f"- Broader historical source certification authorized: {all_viable}",
        "- Position model authorized: False",
        "- Team allocator authorized: False",
        "- 2025 accessed: False",
        "",
    ]
    for row in leagues:
        fielding = row["fielding_diagnostics"]
        lines.extend(
            [
                f"## {row['level_group']} — league {row['league_id']}",
                f"- Viable: {row['acceptance']['viable_for_broader_position_source_certification']}",
                f"- Hitting players: {row['hitting_unique_player_count']:,}",
                f"- Fielding players: {row['fielding_unique_player_count']:,}",
                f"- Hitters without fielding row: {row['hitting_players_without_fielding_count']:,}",
                f"- Fielding splits: {fielding.get('split_count', 0):,}",
                f"- Missing player/team/position fields: "
                f"{fielding.get('missing_player_id_split_count')}/"
                f"{fielding.get('missing_team_id_split_count')}/"
                f"{fielding.get('missing_position_split_count')}",
                f"- Duplicate player/team/position keys: "
                f"{fielding.get('player_team_position_duplicate_key_count')}",
                f"- Observed positions: "
                + ", ".join(
                    sorted(
                        {
                            str(pos.get('abbreviation') or pos.get('code') or pos.get('name'))
                            for pos in fielding.get('observed_positions', [])
                        }
                    )
                ),
                "",
            ]
        )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    if not all_viable:
        raise RuntimeError(
            "position/role fielding source POC failed closed; inspect persisted diagnostics"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
