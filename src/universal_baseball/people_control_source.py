"""Batched StatsAPI people evidence for team-control calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.rights_transactions import project_transaction_payload
from universal_baseball.roster_entry_source import (
    STATS_API_PEOPLE_URL,
    project_roster_entries_payload,
)


PEOPLE_CONTROL_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "birth_date": pl.Date,
    "mlb_debut_date": pl.Date,
    "current_team_id": pl.Int64,
    "current_team_parent_org_id": pl.Int64,
    "first_pro_contract_date": pl.Date,
    "first_pro_contract_basis": pl.String,
    "source_snapshot_id": pl.String,
}

SIGNING_TRANSACTION_CODES = frozenset({"IFA", "SFA", "SGN"})


@dataclass(frozen=True)
class PeopleControlEvidence:
    people: pl.DataFrame
    roster_entries: pl.DataFrame
    transactions: pl.DataFrame
    captures: list[dict[str, object]]


def _date_value(value: object, *, label: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"invalid people {label}") from exc


def _transactions_with_people(payload: dict[str, Any], as_of_date: date) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for person in payload.get("people") or []:
        if not isinstance(person, dict) or person.get("id") is None:
            raise ValueError("people control payload missing identity")
        for original in person.get("transactions") or []:
            if not isinstance(original, dict):
                raise ValueError("people transaction must be an object")
            row = dict(original)
            row.setdefault(
                "person", {"id": person["id"], "fullName": person.get("fullName") or ""}
            )
            transaction_date = _date_value(row.get("date"), label="transaction date")
            effective_date = _date_value(
                row.get("effectiveDate") or row.get("date"), label="effective date"
            )
            if (
                transaction_date is not None
                and transaction_date > as_of_date
                or effective_date is not None
                and effective_date > as_of_date
            ):
                continue
            resolution = _date_value(row.get("resolutionDate"), label="resolution date")
            if resolution is not None and resolution > as_of_date:
                row["resolutionDate"] = None
            output.append(row)
    return output


def project_people_control_payload(
    payload: dict[str, Any], *, as_of_date: date, source_snapshot_id: str
) -> PeopleControlEvidence:
    """Project people, roster entries and transactions from one batch response."""

    people = payload.get("people")
    if not isinstance(people, list):
        raise ValueError("StatsAPI people response missing people list")
    roster_entries = project_roster_entries_payload(
        payload, as_of_date=as_of_date, source_snapshot_id=source_snapshot_id
    )
    raw_transactions = _transactions_with_people(payload, as_of_date)
    transactions = project_transaction_payload(
        {"transactions": raw_transactions},
        as_of_date=as_of_date,
        source_snapshot_id=source_snapshot_id,
    )
    signing_dates: dict[int, date] = {}
    for row in transactions.filter(
        pl.col("type_code").is_in(sorted(SIGNING_TRANSACTION_CODES))
    ).iter_rows(named=True):
        player_id = int(row["player_id"])
        event_date = row["effective_date"]
        signing_dates[player_id] = min(event_date, signing_dates.get(player_id, event_date))

    rows: list[dict[str, object]] = []
    for person in people:
        if not isinstance(person, dict) or person.get("id") is None:
            raise ValueError("people control payload missing identity")
        player_id = int(person["id"])
        current_team = person.get("currentTeam") or {}
        first_contract = signing_dates.get(player_id)
        rows.append(
            {
                "as_of_date": as_of_date,
                "player_id": player_id,
                "player_name": str(person.get("fullName") or ""),
                "birth_date": _date_value(person.get("birthDate"), label="birth date"),
                "mlb_debut_date": _date_value(
                    person.get("mlbDebutDate"), label="MLB debut date"
                ),
                "current_team_id": int(current_team["id"])
                if current_team.get("id") is not None
                else None,
                "current_team_parent_org_id": int(current_team["parentOrgId"])
                if current_team.get("parentOrgId") is not None
                else None,
                "first_pro_contract_date": first_contract,
                "first_pro_contract_basis": "earliest_statsapi_signing_transaction"
                if first_contract is not None
                else "missing_statsapi_signing_transaction",
                "source_snapshot_id": source_snapshot_id,
            }
        )
    people_frame = pl.DataFrame(rows, schema=PEOPLE_CONTROL_SCHEMA).sort("player_id")
    if people_frame.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("people control payload has duplicate player IDs")
    return PeopleControlEvidence(
        people=people_frame,
        roster_entries=roster_entries,
        transactions=transactions,
        captures=[],
    )


def fetch_people_control_evidence(
    player_ids: Iterable[int],
    *,
    as_of_date: date,
    batch_size: int = 25,
    session: requests.Session | None = None,
) -> PeopleControlEvidence:
    """Fetch all control evidence in bounded, reproducible person batches."""

    ids = sorted({int(player_id) for player_id in player_ids})
    if not ids or any(player_id <= 0 for player_id in ids):
        raise ValueError("player_ids must contain positive identities")
    if batch_size <= 0 or batch_size > 50:
        raise ValueError("batch_size must be between 1 and 50")
    own_session = session is None
    http = session or requests.Session()
    batches: list[PeopleControlEvidence] = []
    captures: list[dict[str, object]] = []
    try:
        for offset in range(0, len(ids), batch_size):
            batch = ids[offset : offset + batch_size]
            response = http.get(
                STATS_API_PEOPLE_URL,
                params={
                    "personIds": ",".join(map(str, batch)),
                    "hydrate": "currentTeam,rosterEntries,transactions,draft",
                },
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("StatsAPI people response must be an object")
            snapshot_id = f"statsapi:people-control:{as_of_date}:{offset // batch_size + 1}"
            batch_result = project_people_control_payload(
                payload, as_of_date=as_of_date, source_snapshot_id=snapshot_id
            )
            returned = set(batch_result.people.get_column("player_id").to_list())
            if returned != set(batch):
                raise ValueError("StatsAPI people batch did not return the requested identities")
            batches.append(batch_result)
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
    return PeopleControlEvidence(
        people=pl.concat([batch.people for batch in batches]).sort("player_id"),
        roster_entries=pl.concat(
            [batch.roster_entries for batch in batches], how="vertical_relaxed"
        ).sort(["player_id", "start_date", "team_id"]),
        transactions=pl.concat(
            [batch.transactions for batch in batches], how="vertical_relaxed"
        ).sort(["player_id", "effective_date", "transaction_id"]),
        captures=captures,
    )
