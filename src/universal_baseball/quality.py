"""Canonical quality-issue construction for unresolved source evidence."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from typing import Any

import polars as pl

from universal_baseball.canonical_schema import validate_quality_issue


RESOLUTION_CONFLICT_CHECK = "cross_snapshot_field_consensus"
RESOLUTION_CONFLICT_CHECK_VERSION = "1"


def make_quality_issue_id(
    *,
    issue_code: str,
    entity_type: str,
    entity_key: dict[str, int | str | None],
    check_name: str,
    check_version: str,
    details_identity: dict[str, Any],
) -> str:
    """Return a stable issue identity independent of detection-run timestamp."""

    payload = {
        "issue_code": issue_code,
        "entity_type": entity_type,
        "entity_key": entity_key,
        "check_name": check_name,
        "check_version": check_version,
        "details_identity": details_identity,
    }
    material = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(material).hexdigest()


def quality_issues_from_resolution_conflicts(
    resolved: pl.DataFrame,
    *,
    entity_type: str,
    detected_at_utc: datetime,
) -> pl.DataFrame:
    """Convert unresolved game/pitch field consensus into canonical issues.

    One issue is emitted per conflicted natural entity, not per source row and not
    per conflicted field. The details retain the complete field list and all
    contributing source/normalization IDs.
    """

    if entity_type not in {"game", "pitch"}:
        raise ValueError("resolution quality issues support only game or pitch")
    if detected_at_utc.tzinfo is None or detected_at_utc.utcoffset() is None:
        raise ValueError("detected_at_utc must be timezone-aware")
    if detected_at_utc.utcoffset().total_seconds() != 0:
        raise ValueError("detected_at_utc must be normalized to UTC")

    required = {
        "game_pk",
        "conflict_field_count",
        "conflict_fields",
        "source_snapshot_ids",
        "normalization_ids",
    }
    if entity_type == "pitch":
        required.update({"at_bat_index", "pitch_number"})
    missing = sorted(required - set(resolved.columns))
    if missing:
        raise ValueError(f"resolved {entity_type} view missing quality columns: {missing}")

    conflicts = resolved.filter(pl.col("conflict_field_count") > 0)
    rows: list[dict[str, Any]] = []
    for row in conflicts.to_dicts():
        entity_key = {
            "game_pk": int(row["game_pk"]),
            "at_bat_index": (
                int(row["at_bat_index"]) if entity_type == "pitch" else None
            ),
            "pitch_number": (
                int(row["pitch_number"]) if entity_type == "pitch" else None
            ),
        }
        conflict_fields = sorted(str(value) for value in (row["conflict_fields"] or []))
        source_snapshot_ids = sorted(
            str(value) for value in (row["source_snapshot_ids"] or [])
        )
        normalization_ids = sorted(
            str(value) for value in (row["normalization_ids"] or [])
        )
        details_identity = {
            "conflict_fields": conflict_fields,
            "source_snapshot_ids": source_snapshot_ids,
            "normalization_ids": normalization_ids,
        }
        issue_id = make_quality_issue_id(
            issue_code="source_consensus_conflict",
            entity_type=entity_type,
            entity_key=entity_key,
            check_name=RESOLUTION_CONFLICT_CHECK,
            check_version=RESOLUTION_CONFLICT_CHECK_VERSION,
            details_identity=details_identity,
        )
        rows.append(
            {
                "quality_issue_id": issue_id,
                "issue_code": "source_consensus_conflict",
                "severity": "warning",
                "entity_type": entity_type,
                "game_pk": entity_key["game_pk"],
                "at_bat_index": entity_key["at_bat_index"],
                "pitch_number": entity_key["pitch_number"],
                "source_snapshot_id": None,
                "normalization_id": None,
                "check_name": RESOLUTION_CONFLICT_CHECK,
                "check_version": RESOLUTION_CONFLICT_CHECK_VERSION,
                "detected_at_utc": detected_at_utc,
                "details_json": json.dumps(
                    details_identity,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            }
        )

    if not rows:
        return validate_quality_issue(
            pl.DataFrame(
                schema={
                    "quality_issue_id": pl.String,
                    "issue_code": pl.String,
                    "severity": pl.String,
                    "entity_type": pl.String,
                    "check_name": pl.String,
                    "check_version": pl.String,
                    "detected_at_utc": pl.Datetime(time_unit="us", time_zone="UTC"),
                    "details_json": pl.String,
                }
            )
        )
    return validate_quality_issue(pl.DataFrame(rows))
