"""Reusable armstjc contact-evidence projection and deterministic resolution.

This module promotes the contact-specific source logic that was previously
confined to certification scripts into production code. It does *not* decide
participant authority; see :mod:`contact_identity_overlay` for that step.

Policy follows the accepted source architecture:

- project only fields needed for physical contact/profile evidence;
- infer positive contact from accepted D/E/X pitch codes or preserved hitData
  fields, never from X alone;
- apply only pinned, fully fingerprinted false-positive contact exclusions that
  were separately certified against official game evidence;
- collapse overlapping release snapshots by non-null field consensus at natural
  physical-pitch grain;
- never use filename period, upload time, retrieval time, or row order as a
  source-truth tiebreaker;
- preserve conflicts explicitly so later classification can reduce coverage
  instead of guessing.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import polars as pl


CONTACT_IN_PLAY_CODES = frozenset({"D", "E", "X"})
CONTACT_NATURAL_KEY = ("game_pk", "at_bat_index", "pitch_number")
CONTACT_RESOLUTION_POLICY = "non_null_field_consensus_v1"
CERTIFIED_FALSE_POSITIVE_CONTACT_POLICY = "certified_raw_false_positive_contact_exclusion_v1"


def _optional_text(row: dict[str, Any], name: str) -> str | None:
    value = row.get(name)
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped if stripped else None


@dataclass(frozen=True)
class CertifiedFalsePositiveContact:
    source_asset: str
    season: int
    game_pk: int
    at_bat_index: int
    pitch_number: int
    game_date: str
    league_id: int
    batter_id: int
    pitcher_id: int
    type_code: str
    hit_location: str
    result_description: str
    evidence: str


CERTIFIED_FALSE_POSITIVE_CONTACTS: tuple[CertifiedFalsePositiveContact, ...] = (
    CertifiedFalsePositiveContact(
        source_asset="2021_7_rk_pbp.csv",
        season=2021,
        game_pk=657792,
        at_bat_index=54,
        pitch_number=1,
        game_date="2021-07-22",
        league_id=124,
        batter_id=678365,
        pitcher_id=683690,
        type_code="X",
        hit_location="1",
        result_description=(
            "Julio Herrera caught stealing 2nd base, pitcher Royber Salinas to second baseman "
            "Joseph Fernando."
        ),
        evidence=(
            "2021 Rookie raw-sequence audit run 31978717668: the source row is a caught-stealing "
            "runner event with no event result, bb_type, spray coordinates, launch data, or hit "
            "distance. It is admitted as contact only because the reusable release stamps type=X "
            "and hit_location=1. Current official play-sequence authority contains no matching "
            "contact sequence."
        ),
    ),
)


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
    "certified_contact_exclusion_policy": pl.String,
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


def _certified_batter_side_column(frame: pl.DataFrame, source_asset: str) -> str:
    """Return the certified raw batter-side column for this source asset.

    armstjc's parser exports MLB matchup ``batSide.code`` as ``stand``. Some
    audited intermediate/reprocessed files expose the already-normalized
    ``batter_side`` spelling. Both represent the same structured source field;
    no fuzzy aliasing is allowed here.
    """

    if "batter_side" in frame.columns:
        return "batter_side"
    if "stand" in frame.columns:
        return "stand"
    raise ValueError(
        f"{source_asset} missing certified batter-side field: expected 'stand' "
        "or normalized 'batter_side'"
    )


def _raw_key_mask(correction: CertifiedFalsePositiveContact) -> pl.Expr:
    return (
        (_int_expr("game_pk") == correction.game_pk)
        & (_int_expr("at_bat_number") == correction.at_bat_index)
        & (_int_expr("pitch_number") == correction.pitch_number)
    )


def _certified_false_positive_mask(
    frame: pl.DataFrame,
    *,
    source_asset: str,
    season: int | None,
) -> pl.Expr:
    """Return the exact certified false-positive mask, failing on fingerprint drift.

    A correction is inspected only when its natural key is present in the
    supplied source slice. This keeps projection usable on audited subsets while
    preventing a changed row at the certified key from being silently excluded.
    """

    combined = pl.lit(False)
    corrections = [
        correction
        for correction in CERTIFIED_FALSE_POSITIVE_CONTACTS
        if correction.source_asset == str(source_asset)
        and (season is None or correction.season == int(season))
    ]
    for correction in corrections:
        key_mask = _raw_key_mask(correction)
        candidate = frame.filter(key_mask)
        if candidate.is_empty():
            continue
        if candidate.height != 1:
            raise ValueError(
                "certified false-positive contact expected one raw source row: "
                f"asset={source_asset} game={correction.game_pk} "
                f"at_bat={correction.at_bat_index} pitch={correction.pitch_number}, "
                f"rows={candidate.height}"
            )
        row = candidate.row(0, named=True)
        type_code = _optional_text(row, "type")

        observed = {
            "game_date": _optional_text(row, "game_date"),
            "league_id": int(float(row["league_id"])) if row.get("league_id") is not None else None,
            "batter_id": int(float(row["batter"])) if row.get("batter") is not None else None,
            "pitcher_id": int(float(row["pitcher"])) if row.get("pitcher") is not None else None,
            "type_code": type_code.upper() if type_code is not None else None,
            "hit_location": _optional_text(row, "hit_location"),
            "result_description": _optional_text(row, "description"),
            "bb_type": _optional_text(row, "bb_type"),
            "hc_x": row.get("hc_x"),
            "hc_y": row.get("hc_y"),
            "hit_distance_sc": row.get("hit_distance_sc"),
            "launch_speed": row.get("launch_speed"),
            "launch_angle": row.get("launch_angle"),
        }
        expected = {
            "game_date": correction.game_date,
            "league_id": correction.league_id,
            "batter_id": correction.batter_id,
            "pitcher_id": correction.pitcher_id,
            "type_code": correction.type_code,
            "hit_location": correction.hit_location,
            "result_description": correction.result_description,
            "bb_type": None,
            "hc_x": None,
            "hc_y": None,
            "hit_distance_sc": None,
            "launch_speed": None,
            "launch_angle": None,
        }
        if observed != expected:
            raise ValueError(
                "certified false-positive contact source fingerprint drifted: "
                f"asset={source_asset} game={correction.game_pk} "
                f"at_bat={correction.at_bat_index} pitch={correction.pitch_number}; "
                f"observed={observed} expected={expected}"
            )
        combined = combined | key_mask
    return combined


def project_armstjc_contact_observations(
    frame: pl.DataFrame,
    *,
    source_asset: str,
    season: int | None = None,
    game_type: str | None = "R",
) -> pl.DataFrame:
    """Project one raw PBP asset to contact-relevant source observations.

    The raw release uses ``at_bat_number`` for the play-sequence index and
    historically exports batter handedness as ``stand``. A normalized
    ``batter_side`` spelling is accepted only because it is already a certified
    one-to-one alias of the same MLB matchup field.
    """

    required = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "batter",
        "pitcher",
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
    batter_side_column = _certified_batter_side_column(frame, source_asset)

    raw_positive_contact = (
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
    certified_false_positive = _certified_false_positive_mask(
        frame,
        source_asset=source_asset,
        season=season,
    )
    positive_contact = raw_positive_contact & ~certified_false_positive

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
            pl.col(batter_side_column).cast(pl.String).alias("batter_side"),
            positive_contact.alias("source_is_in_play"),
            pl.col("bb_type").cast(pl.String),
            pl.col("hc_x").cast(pl.Float64, strict=False),
            pl.col("hc_y").cast(pl.Float64, strict=False),
            pl.col("description").cast(pl.String).alias("result_description"),
            pl.when(certified_false_positive)
            .then(pl.lit(CERTIFIED_FALSE_POSITIVE_CONTACT_POLICY))
            .otherwise(pl.lit(None, dtype=pl.String))
            .alias("certified_contact_exclusion_policy"),
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

    raw_counts = {
        (int(row["game_pk"]), int(row["at_bat_index"]), int(row["pitch_number"])): int(row["raw_source_row_count"])
        for row in observations.group_by(list(CONTACT_NATURAL_KEY))
        .len(name="raw_source_row_count")
        .to_dicts()
    }
    exact = observations.unique(maintain_order=True)
    rows: list[dict[str, Any]] = []

    for key_values, group in exact.group_by(list(CONTACT_NATURAL_KEY), maintain_order=False):
        game_pk, at_bat_index, pitch_number = key_values
        key = (int(game_pk), int(at_bat_index), int(pitch_number))
        conflicts: list[str] = []
        row: dict[str, Any] = {
            "game_pk": key[0],
            "at_bat_index": key[1],
            "pitch_number": key[2],
            "source_snapshot_count": int(group.get_column("source_asset").n_unique()),
            "source_assets_json": json.dumps(
                sorted(str(v) for v in group.get_column("source_asset").unique().to_list()),
                separators=(",", ":"),
            ),
            "observation_variant_count": int(group.height),
            "raw_source_row_count": raw_counts[key],
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

    result = pl.DataFrame(rows, schema=RESOLVED_CONTACT_SCHEMA).sort(
        list(CONTACT_NATURAL_KEY)
    )
    if contacts_only:
        result = result.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    return result


def contact_resolution_metrics(
    observations: pl.DataFrame,
    resolved: pl.DataFrame,
) -> dict[str, int]:
    """Return compact quality metrics for resolved contact evidence.

    Pass the full resolved pitch-key view (``contacts_only=False``) when contact
    status conflicts themselves must be counted. Passing a contacts-only view
    still reports profile/batter conflicts among accepted contact rows.
    """

    if observations.is_empty():
        return {
            "raw_observation_count": 0,
            "resolved_pitch_key_count": 0,
            "resolved_contact_count": 0,
            "certified_false_positive_contact_key_count": 0,
            "contact_status_conflict_key_count": 0,
            "contact_batter_conflict_count": 0,
            "profile_field_conflict_contact_count": 0,
        }
    if resolved.is_empty():
        return {
            "raw_observation_count": observations.height,
            "resolved_pitch_key_count": 0,
            "resolved_contact_count": 0,
            "certified_false_positive_contact_key_count": 0,
            "contact_status_conflict_key_count": 0,
            "contact_batter_conflict_count": 0,
            "profile_field_conflict_contact_count": 0,
        }

    contacts = resolved.filter(pl.col("source_is_in_play") == True)  # noqa: E712
    conflicts = contacts.filter(pl.col("conflict_field_count") > 0)
    return {
        "raw_observation_count": observations.height,
        "resolved_pitch_key_count": resolved.height,
        "resolved_contact_count": contacts.height,
        "certified_false_positive_contact_key_count": resolved.filter(
            pl.col("certified_contact_exclusion_policy")
            == CERTIFIED_FALSE_POSITIVE_CONTACT_POLICY
        ).height,
        "contact_status_conflict_key_count": resolved.filter(
            pl.col("conflict_fields_json").str.contains('\"source_is_in_play\"')
        ).height,
        "contact_batter_conflict_count": contacts.filter(
            pl.col("conflict_fields_json").str.contains('\"source_batter_id\"')
        ).height,
        "profile_field_conflict_contact_count": conflicts.filter(
            pl.col("conflict_fields_json").str.contains(
                '\"(batter_side|bb_type|hc_x|hc_y|result_description)\"'
            )
        ).height,
    }
