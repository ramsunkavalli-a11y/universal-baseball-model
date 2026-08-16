"""Reusable armstjc contact-evidence projection and deterministic resolution.

This module promotes the contact-specific source logic that was previously
confined to certification scripts into production code. It does *not* decide
participant authority; see :mod:`contact_identity_overlay` for that step.

Policy follows the accepted source architecture:

- project only fields needed for physical contact/profile evidence;
- infer positive contact from accepted D/E/X pitch codes or preserved hitData
  fields, never from X alone;
- collapse overlapping release snapshots by non-null field consensus at natural
  physical-pitch grain;
- never use filename period, upload time, retrieval time, or row order as a
  source-truth tiebreaker;
- preserve conflicts explicitly so later classification can reduce coverage
  instead of guessing.
"""

from __future__ import annotations

import json
from typing import Any

import polars as pl


CONTACT_IN_PLAY_CODES = frozenset({"D", "E", "X"})
CONTACT_NATURAL_KEY = ("game_pk", "at_bat_index", "pitch_number")
CONTACT_RESOLUTION_POLICY = "non_null_field_consensus_v1"

CONTACT_RESOLVABLE_FIELDS: dict[str, pl.DataType] = {
    "game_date": pl.String,
    "game_type": pl.String,
    "league_id": pl.Int64,
    "source_batter_id": pl.Int64,
    "source_pitcher_id": pl.Int64,
    "batter_side": pl.String,
    "source_is_in_play": pl.Boolean,
    "bb_type": pl.String,
    "hc_x": pl.Float64,
    "hc_y": pl.Float64,
    "result_description": pl.String,
}

RESOLVED_CONTACT_SCHEMA: dict[str, pl.DataType] = {
    "game_pk": pl.Int64,
    "at_bat_index": pl.Int64,
    "pitch_number": pl.Int64,
    **CONTACT_RESOLVABLE_FIELDS,
    "source_snapshot_count": pl.Int64,
    "source_assets_json": pl.String,
    "observation_variant_count": pl.Int64,
    "raw_source_row_count": pl.Int64,
    "conflict_field_count": pl.Int64,
    "conflict_fields_json": pl.String,
    "resolution_policy": pl.String,
}


def _int_expr(column: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or column)
    )


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (
        pl.col(column).cast(pl.String).str.strip_chars() != ""
    )


def project_armstjc_contact_observations(
    frame: pl.DataFrame,
    *,
    source_asset: str,
    season: int | None = None,
    game_type: str | None = "R",
) -> pl.DataFrame:
    """Project one raw PBP asset to contact-relevant source observations.

    The raw release historically uses ``at_bat_number`` for the play-sequence
    index. ``league_id`` and ``description`` are present in recent audited
    releases; historical callers should normalize known schema aliases before
    entering this production adapter.
    """

    required = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "batter",
        "pitcher",
        "batter_side",
        "game_date",
        "game_type",
        "league_id",
        "type",
        "bb_type",
        "hc_x",
        "hc_y",
        "description",
        "hit_location",
        "hit_distance_sc",
        "launch_speed",
        "launch_angle",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{source_asset} missing contact projection fields: {missing}")

    positive_contact = (
        pl.col("type").cast(pl.String).str.strip_chars().str.to_uppercase().is_in(
            sorted(CONTACT_IN_PLAY_CODES)
        )
        | _nonblank("bb_type")
        | _nonblank("hit_location")
        | _nonblank("hc_x")
        | _nonblank("hc_y")
        | _nonblank("hit_distance_sc")
        | _nonblank("launch_speed")
        | _nonblank("launch_angle")
    )

    projected = (
        frame.select(
            _int_expr("game_pk"),
            _int_expr("at_bat_number", "at_bat_index"),
            _int_expr("pitch_number"),
            pl.col("game_date").cast(pl.String),
            pl.col("game_type").cast(pl.String),
            _int_expr("league_id"),
            _int_expr("batter", "source_batter_id"),
            _int_expr("pitcher", "source_pitcher_id"),
            pl.col("batter_side").cast(pl.String),
            positive_contact.alias("source_is_in_play"),
            pl.col("bb_type").cast(pl.String),
            pl.col("hc_x").cast(pl.Float64, strict=False),
            pl.col("hc_y").cast(pl.Float64, strict=False),
            pl.col("description").cast(pl.String).alias("result_description"),
            pl.lit(str(source_asset)).alias("source_asset"),
        )
        .drop_nulls(list(CONTACT_NATURAL_KEY))
    )
    if season is not None:
        projected = projected.filter(pl.col("game_date").str.starts_with(f"{int(season)}-"))
    if game_type is not None:
        projected = projected.filter(pl.col("game_type") == str(game_type))
    return projected


def _stable_non_null(values: list[Any]) -> tuple[Any, bool]:
    distinct: list[Any] = []
    for value in values:
        if value is None:
            continue
        if value not in distinct:
            distinct.append(value)
        if len(distinct) > 1:
            return None, True
    return (distinct[0] if distinct else None), False


def resolve_armstjc_contact_observations(
    observations: pl.DataFrame,
    *,
    contacts_only: bool = True,
) -> pl.DataFrame:
    """Resolve overlapping source observations at physical-pitch grain.

    Null plus one observed non-null value resolves to the observed value. Two
    distinct non-null values conflict and resolve to null for that field.
    ``source_is_in_play`` is subject to the same rule; a contact-status conflict
    therefore does not silently enter the contact table.
    """

    required = {
        *CONTACT_NATURAL_KEY,
        *CONTACT_RESOLVABLE_FIELDS,
        "source_asset",
    }
    missing = sorted(required - set(observations.columns))
    if missing:
        raise ValueError(f"contact observations missing resolution columns: {missing}")
    if observations.is_empty():
        return pl.DataFrame(schema=RESOLVED_CONTACT_SCHEMA)

    raw_rows = observations.height
    exact = observations.unique(maintain_order=True)
    rows: list[dict[str, Any]] = []

    for key_values, group in exact.group_by(list(CONTACT_NATURAL_KEY), maintain_order=False):
        game_pk, at_bat_index, pitch_number = key_values
        conflicts: list[str] = []
        row: dict[str, Any] = {
            "game_pk": int(game_pk),
            "at_bat_index": int(at_bat_index),
            "pitch_number": int(pitch_number),
            "source_snapshot_count": int(group.get_column("source_asset").n_unique()),
            "source_assets_json": json.dumps(
                sorted(str(v) for v in group.get_column("source_asset").unique().to_list()),
                separators=(",", ":"),
            ),
            "observation_variant_count": int(group.height),
            # exact rows are already collapsed; recover multiplicity by matching
            # this physical key in the original observation frame.
            "raw_source_row_count": int(
                observations.filter(
                    (pl.col("game_pk") == int(game_pk))
                    & (pl.col("at_bat_index") == int(at_bat_index))
                    & (pl.col("pitch_number") == int(pitch_number))
                ).height
            ),
            "resolution_policy": CONTACT_RESOLUTION_POLICY,
        }
        for field in CONTACT_RESOLVABLE_FIELDS:
            value, conflict = _stable_non_null(group.get_column(field).to_list())
            row[field] = value
            if conflict:
                conflicts.append(field)
        row["conflict_field_count"] = len(conflicts)
        row["conflict_fields_json"] = json.dumps(conflicts, separators=(",", ":"))
        rows.append(row)

    result = (
        pl.DataFrame(rows, schema=RESOLVED_CONTACT_SCHEMA)
        .sort(list(CONTACT_NATURAL_KEY))
    )
    if contacts_only:
        result = result.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    return result


def contact_resolution_metrics(
    observations: pl.DataFrame,
    resolved_contacts: pl.DataFrame,
) -> dict[str, int]:
    """Return compact quality metrics for source-contact materialization."""

    if observations.is_empty():
        return {
            "raw_observation_count": 0,
            "resolved_contact_count": 0,
            "contact_conflict_count": 0,
            "batter_conflict_count": 0,
            "profile_field_conflict_contact_count": 0,
        }
    if resolved_contacts.is_empty():
        return {
            "raw_observation_count": observations.height,
            "resolved_contact_count": 0,
            "contact_conflict_count": 0,
            "batter_conflict_count": 0,
            "profile_field_conflict_contact_count": 0,
        }

    conflicts = resolved_contacts.filter(pl.col("conflict_field_count") > 0)
    return {
        "raw_observation_count": observations.height,
        "resolved_contact_count": resolved_contacts.height,
        "contact_conflict_count": resolved_contacts.filter(
            pl.col("conflict_fields_json").str.contains('"source_is_in_play"')
        ).height,
        "batter_conflict_count": resolved_contacts.filter(
            pl.col("conflict_fields_json").str.contains('"source_batter_id"')
        ).height,
        "profile_field_conflict_contact_count": conflicts.filter(
            pl.col("conflict_fields_json").str.contains(
                '"(batter_side|bb_type|hc_x|hc_y|result_description)"'
            )
        ).height,
    }
