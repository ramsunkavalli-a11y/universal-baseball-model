"""Deterministic resolution of immutable canonical observations.

This module resolves *within one normalization/source snapshot*. It deliberately
does not decide which overlapping upstream snapshot is newer; that requires a
source-specific ordering policy and cannot be inferred from our retrieval order.
"""

from __future__ import annotations

import json
from typing import Any

import polars as pl

from universal_baseball.canonical_schema import PITCH_OBSERVATION_SCHEMA


PITCH_NATURAL_KEY = ("game_pk", "at_bat_index", "pitch_number")
_PITCH_PROVENANCE = {
    "normalization_id",
    "source_snapshot_id",
    "payload_hash",
    "duplicate_row_count",
    *PITCH_NATURAL_KEY,
}
PITCH_RESOLVABLE_FIELDS = tuple(
    column for column in PITCH_OBSERVATION_SCHEMA if column not in _PITCH_PROVENANCE
)


def _stable_non_null_value(values: list[Any]) -> tuple[Any, bool]:
    distinct: list[Any] = []
    for value in values:
        if value is None:
            continue
        if value not in distinct:
            distinct.append(value)
        if len(distinct) > 1:
            return None, True
    return (distinct[0] if distinct else None), False


def resolve_pitch_observations_within_snapshot(
    observations: pl.DataFrame,
) -> pl.DataFrame:
    """Return one field-consensus record per natural pitch key.

    Preconditions:
    - observations belong to exactly one ``normalization_id``;
    - observations belong to exactly one ``source_snapshot_id``.

    Resolution rules:
    - exact/repeated payload observations remain represented by their accumulated
      ``duplicate_row_count``;
    - a canonical field resolves when all non-null variants agree;
    - if two non-null variants disagree, the resolved field is null and its name
      appears in ``conflict_fields_json``;
    - null from one variant does not backfill a conflicting non-null value from a
      *different snapshot* because this function never crosses snapshots.
    """

    required = {
        "normalization_id",
        "source_snapshot_id",
        "payload_hash",
        "duplicate_row_count",
        *PITCH_NATURAL_KEY,
    }
    missing = sorted(required - set(observations.columns))
    if missing:
        raise ValueError(f"pitch observations missing resolution columns: {missing}")
    if observations.is_empty():
        raise ValueError("cannot resolve empty pitch observation table")
    if observations.get_column("normalization_id").n_unique() != 1:
        raise ValueError("within-snapshot resolver requires exactly one normalization_id")
    if observations.get_column("source_snapshot_id").n_unique() != 1:
        raise ValueError("within-snapshot resolver requires exactly one source_snapshot_id")

    missing_fields = [field for field in PITCH_RESOLVABLE_FIELDS if field not in observations.columns]
    if missing_fields:
        raise ValueError(f"pitch observations missing canonical fields: {missing_fields}")

    normalization_id = observations.get_column("normalization_id")[0]
    source_snapshot_id = observations.get_column("source_snapshot_id")[0]
    rows: list[dict[str, Any]] = []

    for key_values, group in observations.group_by(list(PITCH_NATURAL_KEY), maintain_order=False):
        # Polars returns a scalar for a one-column group key and a tuple for
        # multiple columns; the natural pitch key always has three columns.
        game_pk, at_bat_index, pitch_number = key_values
        conflicts: list[str] = []
        row: dict[str, Any] = {
            "normalization_id": normalization_id,
            "source_snapshot_id": source_snapshot_id,
            "game_pk": int(game_pk),
            "at_bat_index": int(at_bat_index),
            "pitch_number": int(pitch_number),
            "observation_variant_count": group.height,
            "raw_source_row_count": int(group.get_column("duplicate_row_count").sum()),
        }
        for field in PITCH_RESOLVABLE_FIELDS:
            value, conflict = _stable_non_null_value(group.get_column(field).to_list())
            row[field] = value
            if conflict:
                conflicts.append(field)
        row["conflict_field_count"] = len(conflicts)
        row["conflict_fields_json"] = json.dumps(conflicts, separators=(",", ":"))
        rows.append(row)

    return pl.DataFrame(rows).sort(list(PITCH_NATURAL_KEY))


def pitch_resolution_conflicts(resolved: pl.DataFrame) -> pl.DataFrame:
    """Return only resolved pitch rows with one or more conflicting fields."""

    if "conflict_field_count" not in resolved.columns:
        raise ValueError("resolved pitch table missing conflict_field_count")
    return resolved.filter(pl.col("conflict_field_count") > 0)
