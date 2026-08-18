"""Chronology-safe historical MLB roster source adapter for playing-time work.

This module only retrieves/projects official Stats API roster/transaction evidence.
It does not infer playing time, role, roster eligibility, options, injury duration,
or future opportunity. Live source behavior is certified separately before any
field is authorized as a model predictor.
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


def _session(session: requests.Session | None) -> requests.Session:
    if session is not None:
        return session
    created = requests.Session()
    created.headers["User-Agent"] = "universal-baseball-model-playing-time-source/0.1"
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


def project_team_roster_payload(
    payload: dict[str, Any],
    *,
    team_id: int,
    season: int,
    as_of_date: date,
    roster_type: str,
) -> pl.DataFrame:
    if roster_type not in SUPPORTED_ROSTER_TYPES:
        raise ValueError(f"unsupported roster type: {roster_type}")
    rows = payload.get("roster")
    if not isinstance(rows, list):
        raise ValueError("Stats API team roster response missing roster list")

    projected: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Stats API roster row must be an object")
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
    frame = pl.DataFrame(projected, schema=ROSTER_SCHEMA) if projected else pl.DataFrame(schema=ROSTER_SCHEMA)
    if frame.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Stats API roster contains duplicate player IDs within team/date/type")
    return frame.sort("player_id")


def fetch_team_roster_as_of(
    team_id: int,
    *,
    season: int,
    as_of_date: date,
    roster_type: str,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    if roster_type not in SUPPORTED_ROSTER_TYPES:
        raise ValueError(f"unsupported roster type: {roster_type}")
    payload, capture = _get_json(
        f"{STATS_API_BASE}/teams/{int(team_id)}/roster",
        params={
            "rosterType": roster_type,
            "season": int(season),
            "date": as_of_date.isoformat(),
        },
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
