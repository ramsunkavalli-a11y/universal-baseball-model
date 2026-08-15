"""Compare normalized source snapshots without inventing snapshot precedence.

The historical bootstrap contains overlapping upstream assets whose raw payloads
can differ for harmless representation reasons as well as genuine source
revisions. This module compares *resolved canonical fields* instead of raw rows.
It deliberately does not choose a winning snapshot.
"""

from __future__ import annotations

import json
from typing import Any

import polars as pl

from universal_baseball.resolution import (
    PITCH_NATURAL_KEY,
    PITCH_RESOLVABLE_FIELDS,
)


_RESOLUTION_METADATA = {
    "normalization_id",
    "source_snapshot_id",
    "observation_variant_count",
    "raw_source_row_count",
    "conflict_field_count",
    "conflict_fields_json",
    *PITCH_NATURAL_KEY,
}


def _conflict_fields(value: Any) -> set[str]:
    if value is None:
        return set()
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return set()
    if not isinstance(parsed, list):
        return set()
    return {str(item) for item in parsed}


def compare_resolved_pitch_snapshots(
    left: pl.DataFrame,
    right: pl.DataFrame,
) -> dict[str, Any]:
    """Compare two within-snapshot-resolved canonical pitch tables.

    For each shared natural pitch key and canonical field:

    - equal non-null values are agreements;
    - null on one side and non-null on the other is one-sided evidence/enrichment;
    - two different non-null values are a substantive cross-snapshot conflict;
    - a null caused by an explicit within-snapshot conflict is tracked separately
      and is never mistaken for ordinary missingness.

    No precedence policy is applied. The report is evidence for deciding whether
    cross-snapshot consensus is sufficient or an authoritative source is needed.
    """

    required = {*PITCH_NATURAL_KEY, *PITCH_RESOLVABLE_FIELDS, "conflict_fields_json"}
    for label, frame in (("left", left), ("right", right)):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{label} resolved pitch table missing columns: {missing}")
        duplicates = frame.group_by(list(PITCH_NATURAL_KEY)).len().filter(pl.col("len") > 1)
        if not duplicates.is_empty():
            raise ValueError(f"{label} resolved pitch table is not unique by natural key")

    left_rows = {
        tuple(row[column] for column in PITCH_NATURAL_KEY): row
        for row in left.to_dicts()
    }
    right_rows = {
        tuple(row[column] for column in PITCH_NATURAL_KEY): row
        for row in right.to_dicts()
    }
    left_keys = set(left_rows)
    right_keys = set(right_rows)
    shared_keys = left_keys & right_keys

    field_stats: dict[str, dict[str, int]] = {
        field: {
            "both_null": 0,
            "equal_non_null": 0,
            "left_only_non_null": 0,
            "right_only_non_null": 0,
            "non_null_conflict": 0,
            "left_within_snapshot_conflict": 0,
            "right_within_snapshot_conflict": 0,
        }
        for field in PITCH_RESOLVABLE_FIELDS
    }

    keys_with_non_null_conflict = 0
    keys_with_one_sided_evidence = 0
    keys_with_within_snapshot_conflict = 0
    conflict_examples: list[dict[str, Any]] = []

    for key in sorted(shared_keys):
        left_row = left_rows[key]
        right_row = right_rows[key]
        left_internal = _conflict_fields(left_row.get("conflict_fields_json"))
        right_internal = _conflict_fields(right_row.get("conflict_fields_json"))

        key_conflicts: dict[str, dict[str, Any]] = {}
        key_one_sided = False
        key_internal = bool(left_internal or right_internal)

        for field in PITCH_RESOLVABLE_FIELDS:
            stats = field_stats[field]
            if field in left_internal:
                stats["left_within_snapshot_conflict"] += 1
            if field in right_internal:
                stats["right_within_snapshot_conflict"] += 1

            left_value = left_row.get(field)
            right_value = right_row.get(field)

            if left_value is None and right_value is None:
                stats["both_null"] += 1
            elif left_value is None:
                stats["right_only_non_null"] += 1
                key_one_sided = True
            elif right_value is None:
                stats["left_only_non_null"] += 1
                key_one_sided = True
            elif left_value == right_value:
                stats["equal_non_null"] += 1
            else:
                stats["non_null_conflict"] += 1
                key_conflicts[field] = {"left": left_value, "right": right_value}

        if key_conflicts:
            keys_with_non_null_conflict += 1
            if len(conflict_examples) < 25:
                conflict_examples.append(
                    {
                        **{
                            column: key[index]
                            for index, column in enumerate(PITCH_NATURAL_KEY)
                        },
                        "conflicts": key_conflicts,
                    }
                )
        if key_one_sided:
            keys_with_one_sided_evidence += 1
        if key_internal:
            keys_with_within_snapshot_conflict += 1

    fields_with_non_null_conflict = {
        field: stats["non_null_conflict"]
        for field, stats in field_stats.items()
        if stats["non_null_conflict"]
    }
    fields_with_non_null_conflict = dict(
        sorted(fields_with_non_null_conflict.items(), key=lambda item: (-item[1], item[0]))
    )

    fields_with_one_sided_evidence = {
        field: stats["left_only_non_null"] + stats["right_only_non_null"]
        for field, stats in field_stats.items()
        if stats["left_only_non_null"] or stats["right_only_non_null"]
    }
    fields_with_one_sided_evidence = dict(
        sorted(fields_with_one_sided_evidence.items(), key=lambda item: (-item[1], item[0]))
    )

    return {
        "natural_key": list(PITCH_NATURAL_KEY),
        "canonical_field_count": len(PITCH_RESOLVABLE_FIELDS),
        "left_pitch_key_count": len(left_keys),
        "right_pitch_key_count": len(right_keys),
        "shared_pitch_key_count": len(shared_keys),
        "left_only_pitch_key_count": len(left_keys - right_keys),
        "right_only_pitch_key_count": len(right_keys - left_keys),
        "shared_keys_with_non_null_conflict": keys_with_non_null_conflict,
        "shared_keys_with_one_sided_evidence": keys_with_one_sided_evidence,
        "shared_keys_with_within_snapshot_conflict": keys_with_within_snapshot_conflict,
        "shared_key_non_null_conflict_rate": (
            keys_with_non_null_conflict / len(shared_keys) if shared_keys else None
        ),
        "fields_with_non_null_conflict": fields_with_non_null_conflict,
        "fields_with_one_sided_evidence": fields_with_one_sided_evidence,
        "field_stats": field_stats,
        "non_null_conflict_examples": conflict_examples,
    }
