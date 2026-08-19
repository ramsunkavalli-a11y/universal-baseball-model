"""Source-semantic audits for Player Value v1 baserunning evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


MLB_BASERUNNING_SOURCE_FIELDS = (
    "stolenBases",
    "caughtStealing",
    "groundIntoDoublePlay",
    "gidpOpp",
)


def _optional_integer_count(value: Any, label: str) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    numeric = float(str(value))
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"invalid {label}: {value!r}")
    return int(numeric)


def audit_mlb_baserunning_splits(
    splits: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Audit field presence and count semantics without filling missing values."""

    if not splits:
        raise ValueError("MLB baserunning audit requires at least one hitting split")

    field_present_rows = {field: 0 for field in MLB_BASERUNNING_SOURCE_FIELDS}
    field_nonnull_rows = {field: 0 for field in MLB_BASERUNNING_SOURCE_FIELDS}
    gidp_checked_rows = 0
    gidp_violation_rows = 0

    for split in splits:
        stat = split.get("stat") or {}
        parsed: dict[str, int | None] = {}
        for field in MLB_BASERUNNING_SOURCE_FIELDS:
            if field in stat:
                field_present_rows[field] += 1
            value = _optional_integer_count(stat.get(field), field)
            parsed[field] = value
            if value is not None:
                field_nonnull_rows[field] += 1

        gidp = parsed["groundIntoDoublePlay"]
        opportunities = parsed["gidpOpp"]
        if gidp is not None and opportunities is not None:
            gidp_checked_rows += 1
            if gidp > opportunities:
                gidp_violation_rows += 1

    if gidp_violation_rows:
        raise ValueError(
            "MLB baserunning source violates groundIntoDoublePlay <= gidpOpp "
            f"in {gidp_violation_rows} rows"
        )

    row_count = len(splits)
    return {
        "row_count": row_count,
        "fields": {
            field: {
                "present_rows": field_present_rows[field],
                "nonnull_rows": field_nonnull_rows[field],
                "missing_rows": row_count - field_nonnull_rows[field],
                "complete": field_nonnull_rows[field] == row_count,
            }
            for field in MLB_BASERUNNING_SOURCE_FIELDS
        },
        "gidp_opportunity_identity": {
            "checked_rows": gidp_checked_rows,
            "violation_rows": 0,
        },
    }
