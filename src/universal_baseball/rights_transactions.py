"""Chronology-safe projection of official transaction events.

The ledger preserves source events but deliberately does not infer current rights.
Transaction codes include assignments, options, injuries and administrative changes
as well as true acquisitions and releases; ownership logic belongs in a separately
audited state-transition layer.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import polars as pl


RIGHTS_TRANSACTION_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "transaction_id": pl.Int64,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "transaction_date": pl.Date,
    "effective_date": pl.Date,
    "resolution_date": pl.Date,
    "type_code": pl.String,
    "type_description": pl.String,
    "from_team_id": pl.Int64,
    "to_team_id": pl.Int64,
    "description": pl.String,
    "source_snapshot_id": pl.String,
}


def _parse_date(value: object, *, label: str, required: bool) -> date | None:
    if value in (None, ""):
        if required:
            raise ValueError(f"transaction missing {label}")
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"transaction has invalid {label}") from exc


def project_transaction_payload(
    payload: dict[str, Any],
    *,
    as_of_date: date,
    source_snapshot_id: str,
) -> pl.DataFrame:
    """Project an official transaction response without rights-state inference."""

    if not source_snapshot_id.strip():
        raise ValueError("transaction source_snapshot_id must be nonblank")
    source_rows = payload.get("transactions")
    if not isinstance(source_rows, list):
        raise ValueError("transaction response missing transactions list")
    projected: list[dict[str, object]] = []
    for source in source_rows:
        if not isinstance(source, dict):
            raise ValueError("transaction row must be an object")
        person = source.get("person") or {}
        transaction_id = source.get("id")
        player_id = person.get("id")
        type_code = str(source.get("typeCode") or "").strip()
        transaction_date = _parse_date(
            source.get("date"), label="transaction date", required=True
        )
        effective_date = _parse_date(
            source.get("effectiveDate") or source.get("date"),
            label="effective date",
            required=True,
        )
        resolution_date = _parse_date(
            source.get("resolutionDate"), label="resolution date", required=False
        )
        if transaction_id is None or player_id is None or not type_code:
            raise ValueError("transaction missing identity or type code")
        assert transaction_date is not None
        assert effective_date is not None
        if transaction_date > as_of_date or effective_date > as_of_date:
            raise ValueError("transaction payload crosses as-of cutoff")
        if resolution_date is not None and resolution_date > as_of_date:
            raise ValueError("transaction resolution crosses as-of cutoff")
        projected.append(
            {
                "as_of_date": as_of_date,
                "transaction_id": int(transaction_id),
                "player_id": int(player_id),
                "player_name": str(person.get("fullName") or ""),
                "transaction_date": transaction_date,
                "effective_date": effective_date,
                "resolution_date": resolution_date,
                "type_code": type_code,
                "type_description": str(source.get("typeDesc") or ""),
                "from_team_id": int(source["fromTeam"]["id"])
                if (source.get("fromTeam") or {}).get("id") is not None
                else None,
                "to_team_id": int(source["toTeam"]["id"])
                if (source.get("toTeam") or {}).get("id") is not None
                else None,
                "description": str(source.get("description") or ""),
                "source_snapshot_id": source_snapshot_id,
            }
        )
    result = (
        pl.DataFrame(projected, schema=RIGHTS_TRANSACTION_SCHEMA)
        if projected
        else pl.DataFrame(schema=RIGHTS_TRANSACTION_SCHEMA)
    )
    if result.filter(
        (pl.col("transaction_id") <= 0) | (pl.col("player_id") <= 0)
    ).height:
        raise ValueError("transaction payload has non-positive identity")
    if result.group_by("transaction_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("transaction payload has duplicate transaction_id")
    return result.sort(["player_id", "effective_date", "transaction_id"])
