"""StatsAPI roster-entry adapter for season-opening control states."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.control_events import OPENING_CONTROL_STATE_SCHEMA
from universal_baseball.team_control import SEASON_WINDOW_SCHEMA


STATS_API_PEOPLE_URL = "https://statsapi.mlb.com/api/v1/people"
ROSTER_ENTRY_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "team_id": pl.Int64,
    "parent_org_id": pl.Int64,
    "status_code": pl.String,
    "status_description": pl.String,
    "start_date": pl.Date,
    "end_date": pl.Date,
    "is_active_40man": pl.Boolean,
    "source_snapshot_id": pl.String,
}

OPENING_STATE_REVIEW_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "season": pl.Int64,
    "reason": pl.String,
    "candidate_count": pl.Int64,
    "source_snapshot_ids": pl.String,
}


@dataclass(frozen=True)
class OpeningStateResult:
    opening_states: pl.DataFrame
    review_players: pl.DataFrame


def _parse_date(value: object, *, required: bool) -> date | None:
    if value in (None, ""):
        if required:
            raise ValueError("roster entry missing required date")
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError("roster entry has invalid date") from exc


def project_roster_entries_payload(
    payload: dict[str, Any], *, as_of_date: date, source_snapshot_id: str
) -> pl.DataFrame:
    """Project dated roster entries without interpreting their control state."""

    people = payload.get("people")
    if not isinstance(people, list):
        raise ValueError("StatsAPI people response missing people list")
    if not source_snapshot_id.strip():
        raise ValueError("source_snapshot_id must be nonblank")
    rows: list[dict[str, object]] = []
    for person in people:
        if not isinstance(person, dict) or person.get("id") is None:
            raise ValueError("people row missing player identity")
        entries = person.get("rosterEntries") or []
        if not isinstance(entries, list):
            raise ValueError("rosterEntries must be a list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("roster entry must be an object")
            start = _parse_date(entry.get("startDate"), required=True)
            end = _parse_date(entry.get("endDate"), required=False)
            assert start is not None
            if start > as_of_date:
                continue
            if end is not None and end < start:
                raise ValueError("roster entry has inverted dates")
            team = entry.get("team") or {}
            status = entry.get("status") or {}
            if team.get("id") is None or not str(status.get("code") or "").strip():
                raise ValueError("roster entry missing team or status")
            rows.append(
                {
                    "as_of_date": as_of_date,
                    "player_id": int(person["id"]),
                    "player_name": str(person.get("fullName") or ""),
                    "team_id": int(team["id"]),
                    "parent_org_id": int(team["parentOrgId"])
                    if team.get("parentOrgId") is not None
                    else None,
                    "status_code": str(status["code"]),
                    "status_description": str(status.get("description") or ""),
                    "start_date": start,
                    "end_date": min(end, as_of_date) if end is not None else None,
                    "is_active_40man": bool(entry.get("isActiveFortyMan", False)),
                    "source_snapshot_id": source_snapshot_id,
                }
            )
    return (
        pl.DataFrame(rows, schema=ROSTER_ENTRY_SCHEMA)
        if rows
        else pl.DataFrame(schema=ROSTER_ENTRY_SCHEMA)
    ).sort(["player_id", "start_date", "team_id"])


def _candidate_state(row: dict[str, object], mlb_team_ids: set[int]) -> str | None:
    status = str(row["status_description"]).lower()
    code = str(row["status_code"])
    on_40man = bool(row["is_active_40man"])
    team_is_mlb = int(row["team_id"]) in mlb_team_ids
    if code == "RA" or "rehab assignment" in status:
        return "mlb_injured" if on_40man else None
    if "injured" in status or "disabled" in status:
        return "mlb_injured" if on_40man else "pro_injured"
    if team_is_mlb and code == "A":
        return "mlb_active"
    if not team_is_mlb and code in {"A", "ASG"}:
        return "minors_optioned" if on_40man else "pro_active"
    return None


def build_opening_control_states(
    roster_entries: pl.DataFrame,
    season_windows: pl.DataFrame,
    *,
    mlb_team_ids: set[int],
) -> OpeningStateResult:
    """Choose the most recent specific entry covering each season opening."""

    if roster_entries.schema != ROSTER_ENTRY_SCHEMA:
        roster_entries = roster_entries.select(list(ROSTER_ENTRY_SCHEMA)).cast(
            ROSTER_ENTRY_SCHEMA, strict=True
        )
    if season_windows.schema != SEASON_WINDOW_SCHEMA:
        season_windows = season_windows.select(list(SEASON_WINDOW_SCHEMA)).cast(
            SEASON_WINDOW_SCHEMA, strict=True
        )
    opening_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    source_rows = list(roster_entries.iter_rows(named=True))
    for window in season_windows.iter_rows(named=True):
        season = int(window["season"])
        opening_date = window["start_date"]
        player_ids = sorted({int(row["player_id"]) for row in source_rows})
        for player_id in player_ids:
            candidates = [
                row
                for row in source_rows
                if int(row["player_id"]) == player_id
                and row["start_date"] <= opening_date
                and (row["end_date"] is None or row["end_date"] >= opening_date)
            ]
            classified = [
                (row, _candidate_state(row, mlb_team_ids)) for row in candidates
            ]
            usable = [(row, state) for row, state in classified if state is not None]
            if not usable:
                if candidates:
                    review_rows.append(
                        {
                            "player_id": player_id,
                            "season": season,
                            "reason": "no_specific_opening_state",
                            "candidate_count": len(candidates),
                            "source_snapshot_ids": ",".join(
                                sorted({str(row["source_snapshot_id"]) for row in candidates})
                            ),
                        }
                    )
                continue
            latest_start = max(row["start_date"] for row, _ in usable)
            latest = [(row, state) for row, state in usable if row["start_date"] == latest_start]
            states = {state for _, state in latest}
            if len(states) != 1:
                review_rows.append(
                    {
                        "player_id": player_id,
                        "season": season,
                        "reason": "conflicting_latest_opening_states",
                        "candidate_count": len(latest),
                        "source_snapshot_ids": ",".join(
                            sorted({str(row["source_snapshot_id"]) for row, _ in latest})
                        ),
                    }
                )
                continue
            chosen_row, chosen_state = sorted(latest, key=lambda item: int(item[0]["team_id"]))[0]
            opening_rows.append(
                {
                    "player_id": player_id,
                    "season": season,
                    "roster_state": chosen_state,
                    "source_snapshot_id": str(chosen_row["source_snapshot_id"]),
                }
            )
    openings = (
        pl.DataFrame(opening_rows, schema=OPENING_CONTROL_STATE_SCHEMA)
        if opening_rows
        else pl.DataFrame(schema=OPENING_CONTROL_STATE_SCHEMA)
    ).sort(["player_id", "season"])
    reviews = (
        pl.DataFrame(review_rows, schema=OPENING_STATE_REVIEW_SCHEMA)
        if review_rows
        else pl.DataFrame(schema=OPENING_STATE_REVIEW_SCHEMA)
    ).sort(["player_id", "season"])
    return OpeningStateResult(opening_states=openings, review_players=reviews)


def fetch_roster_entries(
    player_ids: Iterable[int],
    *,
    as_of_date: date,
    batch_size: int = 50,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    """Fetch people in bounded batches and return projected roster entries."""

    ids = sorted({int(player_id) for player_id in player_ids})
    if not ids or any(player_id <= 0 for player_id in ids):
        raise ValueError("player_ids must contain positive identities")
    if batch_size <= 0 or batch_size > 100:
        raise ValueError("batch_size must be between 1 and 100")
    own_session = session is None
    http = session or requests.Session()
    frames: list[pl.DataFrame] = []
    captures: list[dict[str, object]] = []
    try:
        for offset in range(0, len(ids), batch_size):
            batch = ids[offset : offset + batch_size]
            response = http.get(
                STATS_API_PEOPLE_URL,
                params={"personIds": ",".join(map(str, batch)), "hydrate": "rosterEntries"},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("StatsAPI people response must be an object")
            snapshot_id = f"statsapi:people-roster-entries:{as_of_date}:{offset // batch_size + 1}"
            frames.append(
                project_roster_entries_payload(
                    payload, as_of_date=as_of_date, source_snapshot_id=snapshot_id
                )
            )
            captures.append(
                {
                    "source_snapshot_id": snapshot_id,
                    "requested_url": response.url,
                    "status_code": int(response.status_code),
                    "payload": payload,
                }
            )
    finally:
        if own_session:
            http.close()
    return pl.concat(frames).sort(["player_id", "start_date", "team_id"]), captures
