"""Chronology-safe historical MLB roster source adapter for playing-time work.

This module retrieves/projects official Stats API roster/transaction evidence.
The certified 40-man feature is deliberately **set membership only**. The source
can return the same player twice with conflicting row-level status (documented
for José Buttó on 2022/2023 Mets snapshots), and can expose row-level
``parentTeamId`` values that differ from the requested MLB organization for a
player returned by that organization's 40Man endpoint. Therefore Active/Minors/
IL status and row-level parent-team metadata are diagnostics only and are not
used to infer binary 40-man membership.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import polars as pl
import requests


STATS_API_BASE = "https://statsapi.mlb.com/api/v1"
SUPPORTED_ROSTER_TYPES = frozenset({"40Man", "active"})
ROSTER_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "season": pl.Int64,
    "team_id": pl.Int64,
    "roster_type": pl.String,
    "player_id": pl.Int64,
    "full_name": pl.String,
    "position_code": pl.String,
    "position_abbreviation": pl.String,
    "status_code": pl.String,
    "status_description": pl.String,
}
FORTY_MAN_MEMBERSHIP_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "season": pl.Int64,
    "team_id": pl.Int64,
    "player_id": pl.Int64,
    "on_40man": pl.Boolean,
    "source_row_count": pl.Int64,
    "source_status_codes": pl.String,
    "source_status_conflict": pl.Boolean,
    "source_parent_team_ids": pl.String,
    "source_parent_team_id_mismatch": pl.Boolean,
}


def _session(session: requests.Session | None) -> requests.Session:
    if session is not None:
        return session
    created = requests.Session()
    created.headers["User-Agent"] = "universal-baseball-model-playing-time-source/0.2"
    return created


def _get_json(
    url: str,
    *,
    params: dict[str, Any],
    session: requests.Session | None = None,
    timeout_seconds: int = 30,
) -> tuple[dict[str, Any], dict[str, Any]]:
    own_session = session is None
    http = _session(session)
    try:
        response = http.get(url, params=params, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Stats API response must be a JSON object")
        capture = {
            "requested_url": response.url,
            "status_code": int(response.status_code),
            "content_type": response.headers.get("content-type", ""),
            "payload": payload,
        }
        return payload, capture
    finally:
        if own_session:
            http.close()


def _roster_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = payload.get("roster")
    if not isinstance(rows, list):
        raise ValueError("Stats API team roster response missing roster list")
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("Stats API roster row must be an object")
    return rows


def project_team_roster_payload(
    payload: dict[str, Any],
    *,
    team_id: int,
    season: int,
    as_of_date: date,
    roster_type: str,
) -> pl.DataFrame:
    """Project row-level roster status, failing on duplicate players.

    This remains appropriate for diagnostics such as `active`. It is deliberately
    *not* the authorized 40-man membership projector because 40Man source rows can
    contain conflicting status duplicates for one unambiguous member.
    """
    if roster_type not in SUPPORTED_ROSTER_TYPES:
        raise ValueError(f"unsupported roster type: {roster_type}")
    rows = _roster_rows(payload)

    projected: list[dict[str, object]] = []
    for row in rows:
        person = row.get("person") or {}
        position = row.get("position") or {}
        status = row.get("status") or {}
        player_id = person.get("id")
        if player_id is None:
            raise ValueError("Stats API roster row missing person.id")
        projected.append(
            {
                "as_of_date": as_of_date,
                "season": int(season),
                "team_id": int(team_id),
                "roster_type": roster_type,
                "player_id": int(player_id),
                "full_name": str(person.get("fullName") or ""),
                "position_code": str(position.get("code") or ""),
                "position_abbreviation": str(position.get("abbreviation") or ""),
                "status_code": str(status.get("code") or ""),
                "status_description": str(status.get("description") or ""),
            }
        )
    frame = (
        pl.DataFrame(projected, schema=ROSTER_SCHEMA)
        if projected
        else pl.DataFrame(schema=ROSTER_SCHEMA)
    )
    if frame.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Stats API roster contains duplicate player IDs within team/date/type")
    return frame.sort("player_id")


def project_team_40man_membership_payload(
    payload: dict[str, Any],
    *,
    team_id: int,
    season: int,
    as_of_date: date,
) -> pl.DataFrame:
    """Project one binary 40-man membership row per player.

    Duplicate source rows are allowed only when player identity is unambiguous.
    Conflicting source `status` and `parentTeamId` values are preserved as
    diagnostics but are **not** interpreted. The authorized membership fact is
    only that `player_id` is present in the requested official team's 40Man
    endpoint as of the requested date. Cross-team endpoint conflicts are checked
    by the caller after all MLB teams are collected.
    """
    rows = _roster_rows(payload)
    by_player: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        person = row.get("person") or {}
        player_id = person.get("id")
        if player_id is None:
            raise ValueError("Stats API 40Man row missing person.id")
        by_player.setdefault(int(player_id), []).append(row)

    projected: list[dict[str, object]] = []
    for player_id, player_rows in sorted(by_player.items()):
        identity_tuples = {
            (
                str((row.get("person") or {}).get("fullName") or ""),
                str((row.get("person") or {}).get("link") or ""),
            )
            for row in player_rows
        }
        if len(identity_tuples) != 1:
            raise ValueError(f"Stats API 40Man duplicate identity conflict for player {player_id}")
        status_codes = sorted(
            {
                str((row.get("status") or {}).get("code") or "")
                for row in player_rows
            }
        )
        parent_team_ids = sorted(
            {
                int(row["parentTeamId"])
                for row in player_rows
                if row.get("parentTeamId") is not None
            }
        )
        projected.append(
            {
                "as_of_date": as_of_date,
                "season": int(season),
                "team_id": int(team_id),
                "player_id": player_id,
                "on_40man": True,
                "source_row_count": len(player_rows),
                "source_status_codes": ",".join(status_codes),
                "source_status_conflict": len(status_codes) > 1,
                "source_parent_team_ids": ",".join(str(value) for value in parent_team_ids),
                "source_parent_team_id_mismatch": any(
                    value != int(team_id) for value in parent_team_ids
                ),
            }
        )
    frame = (
        pl.DataFrame(projected, schema=FORTY_MAN_MEMBERSHIP_SCHEMA)
        if projected
        else pl.DataFrame(schema=FORTY_MAN_MEMBERSHIP_SCHEMA)
    )
    if frame.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("40-man membership projector failed unique player grain")
    return frame.sort("player_id")


def _fetch_roster_payload(
    team_id: int,
    *,
    season: int,
    as_of_date: date,
    roster_type: str,
    session: requests.Session | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if roster_type not in SUPPORTED_ROSTER_TYPES:
        raise ValueError(f"unsupported roster type: {roster_type}")
    return _get_json(
        f"{STATS_API_BASE}/teams/{int(team_id)}/roster",
        params={
            "rosterType": roster_type,
            "season": int(season),
            "date": as_of_date.isoformat(),
        },
        session=session,
    )


def fetch_team_roster_as_of(
    team_id: int,
    *,
    season: int,
    as_of_date: date,
    roster_type: str,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    payload, capture = _fetch_roster_payload(
        team_id,
        season=season,
        as_of_date=as_of_date,
        roster_type=roster_type,
        session=session,
    )
    return (
        project_team_roster_payload(
            payload,
            team_id=int(team_id),
            season=int(season),
            as_of_date=as_of_date,
            roster_type=roster_type,
        ),
        capture,
    )


def fetch_team_40man_membership_as_of(
    team_id: int,
    *,
    season: int,
    as_of_date: date,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    payload, capture = _fetch_roster_payload(
        team_id,
        season=season,
        as_of_date=as_of_date,
        roster_type="40Man",
        session=session,
    )
    return (
        project_team_40man_membership_payload(
            payload,
            team_id=int(team_id),
            season=int(season),
            as_of_date=as_of_date,
        ),
        capture,
    )


def fetch_mlb_teams(
    season: int,
    *,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    payload, capture = _get_json(
        f"{STATS_API_BASE}/teams",
        params={"sportId": 1, "season": int(season)},
        session=session,
    )
    teams = payload.get("teams")
    if not isinstance(teams, list):
        raise ValueError("Stats API teams response missing teams list")
    rows = [
        {
            "season": int(season),
            "team_id": int(team["id"]),
            "team_name": str(team.get("name") or ""),
        }
        for team in teams
        if isinstance(team, dict) and team.get("id") is not None
    ]
    frame = pl.DataFrame(rows).sort("team_id")
    if frame.group_by("team_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Stats API MLB team list has duplicate team IDs")
    return frame, capture


def fetch_team_transactions_around(
    team_id: int,
    *,
    as_of_date: date,
    days_each_side: int = 2,
    session: requests.Session | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if days_each_side < 0:
        raise ValueError("transaction window must be nonnegative")
    start = as_of_date - timedelta(days=days_each_side)
    end = as_of_date + timedelta(days=days_each_side)
    payload, capture = _get_json(
        f"{STATS_API_BASE}/transactions",
        params={
            "teamId": int(team_id),
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
        },
        session=session,
    )
    transactions = payload.get("transactions", [])
    if not isinstance(transactions, list):
        raise ValueError("Stats API transactions response has invalid transactions field")
    return [row for row in transactions if isinstance(row, dict)], capture
