"""Deterministic resolution of immutable canonical observations.

Within-snapshot resolution and cross-snapshot resolution are deliberately
separate. Cross-snapshot resolution does **not** infer a source chronology from
retrieval time, GitHub asset creation time, or a filename period. The reusable
MiLB source has demonstrated that each of those can be misleading.
"""

from __future__ import annotations

import json
from typing import Any

import polars as pl

from universal_baseball.canonical_schema import (
    PITCH_OBSERVATION_SCHEMA,
    validate_normalization_definition,
    validate_pitch_observation,
)
from universal_baseball.game_observation import (
    GAME_OBSERVATION_SCHEMA,
    validate_game_observation,
)


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

GAME_NATURAL_KEY = ("game_pk",)
_GAME_PROVENANCE = {
    "normalization_id",
    "source_snapshot_id",
    "game_pk",
    "payload_hash",
    "evidence_row_count",
}
GAME_RESOLVABLE_FIELDS = tuple(
    column for column in GAME_OBSERVATION_SCHEMA if column not in _GAME_PROVENANCE
)

CROSS_SNAPSHOT_RESOLUTION_POLICY = "non_null_field_consensus_v1"


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

    missing_fields = [
        field for field in PITCH_RESOLVABLE_FIELDS if field not in observations.columns
    ]
    if missing_fields:
        raise ValueError(f"pitch observations missing canonical fields: {missing_fields}")

    normalization_id = observations.get_column("normalization_id")[0]
    source_snapshot_id = observations.get_column("source_snapshot_id")[0]
    rows: list[dict[str, Any]] = []

    for key_values, group in observations.group_by(
        list(PITCH_NATURAL_KEY), maintain_order=False
    ):
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


def _validated_normalization_family(
    observations: pl.DataFrame,
    normalization_definitions: pl.DataFrame,
) -> dict[str, str]:
    """Prove all observations were produced by one comparable normalizer family."""

    definitions = validate_normalization_definition(normalization_definitions)
    observed_links = observations.select(
        ["normalization_id", "source_snapshot_id"]
    ).unique()

    multiple_normalizations = (
        observed_links.group_by("source_snapshot_id")
        .agg(pl.col("normalization_id").n_unique().alias("normalization_count"))
        .filter(pl.col("normalization_count") != 1)
    )
    if not multiple_normalizations.is_empty():
        raise ValueError(
            "cross-snapshot resolver requires exactly one normalization per source snapshot"
        )

    linked = observed_links.join(
        definitions,
        on="normalization_id",
        how="left",
        suffix="_definition",
    )
    missing_definition = linked.filter(pl.col("normalizer_name").is_null())
    if not missing_definition.is_empty():
        raise ValueError("observations reference missing normalization definitions")

    source_mismatch = linked.filter(
        pl.col("source_snapshot_id") != pl.col("source_snapshot_id_definition")
    )
    if not source_mismatch.is_empty():
        raise ValueError(
            "normalization definition source_snapshot_id disagrees with observations"
        )

    family_columns = [
        "normalizer_name",
        "normalizer_version",
        "canonical_schema_version",
    ]
    families = linked.select(family_columns).unique()
    if families.height != 1:
        raise ValueError("cross-snapshot resolver cannot mix normalizer/schema versions")
    row = families.to_dicts()[0]
    return {column: str(row[column]) for column in family_columns}


def resolve_pitch_observations_across_snapshots(
    observations: pl.DataFrame,
    normalization_definitions: pl.DataFrame,
) -> pl.DataFrame:
    """Build an ordering-free working view across overlapping pitch snapshots."""

    canonical = validate_pitch_observation(observations)
    if canonical.is_empty():
        raise ValueError("cannot resolve empty pitch observation table")
    family = _validated_normalization_family(canonical, normalization_definitions)

    aggregations: list[pl.Expr] = [
        pl.col("source_snapshot_id").n_unique().alias("source_snapshot_count"),
        pl.col("source_snapshot_id").unique().sort().alias("source_snapshot_ids"),
        pl.col("normalization_id").n_unique().alias("normalization_count"),
        pl.col("normalization_id").unique().sort().alias("normalization_ids"),
        pl.len().alias("observation_variant_count"),
        pl.col("duplicate_row_count").sum().alias("raw_source_row_count"),
    ]
    conflict_columns: list[str] = []

    for field in PITCH_RESOLVABLE_FIELDS:
        values = pl.col(field).drop_nulls()
        conflict_column = f"__conflict__{field}"
        conflict_columns.append(conflict_column)
        aggregations.extend(
            [
                pl.when(values.n_unique() <= 1)
                .then(values.first())
                .otherwise(pl.lit(None, dtype=PITCH_OBSERVATION_SCHEMA[field]))
                .alias(field),
                (values.n_unique() > 1).alias(conflict_column),
            ]
        )

    resolved = canonical.group_by(list(PITCH_NATURAL_KEY)).agg(aggregations)
    conflict_names = [
        pl.when(pl.col(flag))
        .then(pl.lit(field))
        .otherwise(pl.lit(None, dtype=pl.String))
        for field, flag in zip(PITCH_RESOLVABLE_FIELDS, conflict_columns, strict=True)
    ]
    return (
        resolved.with_columns(
            pl.concat_list(conflict_names)
            .list.drop_nulls()
            .alias("conflict_fields")
        )
        .with_columns(
            pl.col("conflict_fields").list.len().alias("conflict_field_count"),
            pl.lit(CROSS_SNAPSHOT_RESOLUTION_POLICY).alias("resolution_policy"),
            pl.lit(family["normalizer_name"]).alias("normalizer_name"),
            pl.lit(family["normalizer_version"]).alias("normalizer_version"),
            pl.lit(family["canonical_schema_version"]).alias(
                "canonical_schema_version"
            ),
        )
        .drop(conflict_columns)
        .sort(list(PITCH_NATURAL_KEY))
    )


def resolve_game_observations_across_snapshots(
    observations: pl.DataFrame,
    normalization_definitions: pl.DataFrame,
) -> pl.DataFrame:
    """Build one field-consensus game record across overlapping source assets.

    A game date or level can remain usable even when a re-upload changes a team
    display label. As with pitch resolution, no asset is declared globally newer.
    Conflicting non-null fields remain null and are listed explicitly.
    """

    canonical = validate_game_observation(observations)
    if canonical.is_empty():
        raise ValueError("cannot resolve empty game observation table")
    family = _validated_normalization_family(canonical, normalization_definitions)

    aggregations: list[pl.Expr] = [
        pl.col("source_snapshot_id").n_unique().alias("source_snapshot_count"),
        pl.col("source_snapshot_id").unique().sort().alias("source_snapshot_ids"),
        pl.col("normalization_id").n_unique().alias("normalization_count"),
        pl.col("normalization_id").unique().sort().alias("normalization_ids"),
        pl.len().alias("observation_variant_count"),
        pl.col("evidence_row_count").sum().alias("raw_source_row_count"),
    ]
    conflict_columns: list[str] = []
    for field in GAME_RESOLVABLE_FIELDS:
        values = pl.col(field).drop_nulls()
        conflict_column = f"__conflict__{field}"
        conflict_columns.append(conflict_column)
        aggregations.extend(
            [
                pl.when(values.n_unique() <= 1)
                .then(values.first())
                .otherwise(pl.lit(None, dtype=GAME_OBSERVATION_SCHEMA[field]))
                .alias(field),
                (values.n_unique() > 1).alias(conflict_column),
            ]
        )

    resolved = canonical.group_by("game_pk").agg(aggregations)
    conflict_names = [
        pl.when(pl.col(flag))
        .then(pl.lit(field))
        .otherwise(pl.lit(None, dtype=pl.String))
        for field, flag in zip(GAME_RESOLVABLE_FIELDS, conflict_columns, strict=True)
    ]
    return (
        resolved.with_columns(
            pl.concat_list(conflict_names)
            .list.drop_nulls()
            .alias("conflict_fields")
        )
        .with_columns(
            pl.col("conflict_fields").list.len().alias("conflict_field_count"),
            pl.lit(CROSS_SNAPSHOT_RESOLUTION_POLICY).alias("resolution_policy"),
            pl.lit(family["normalizer_name"]).alias("normalizer_name"),
            pl.lit(family["normalizer_version"]).alias("normalizer_version"),
            pl.lit(family["canonical_schema_version"]).alias(
                "canonical_schema_version"
            ),
        )
        .drop(conflict_columns)
        .sort("game_pk")
    )


def pitch_resolution_conflicts(resolved: pl.DataFrame) -> pl.DataFrame:
    """Return only resolved pitch rows with one or more conflicting fields."""

    if "conflict_field_count" not in resolved.columns:
        raise ValueError("resolved pitch table missing conflict_field_count")
    return resolved.filter(pl.col("conflict_field_count") > 0)


def game_resolution_conflicts(resolved: pl.DataFrame) -> pl.DataFrame:
    """Return only resolved game rows with one or more conflicting fields."""

    if "conflict_field_count" not in resolved.columns:
        raise ValueError("resolved game table missing conflict_field_count")
    return resolved.filter(pl.col("conflict_field_count") > 0)
