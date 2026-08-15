"""Typed canonical observation schemas and invariant validation.

These are intentionally small foundation contracts, not a claim that every
future baseball field is already known. Natural keys, provenance, identity
semantics, and source conflict behavior are the hard parts to freeze first.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import polars as pl


CANONICAL_SCHEMA_VERSION = "0.1"
UTC_DATETIME = pl.Datetime(time_unit="us", time_zone="UTC")

SOURCE_SNAPSHOT_SCHEMA: dict[str, pl.DataType] = {
    "source_snapshot_id": pl.String,
    "source_name": pl.String,
    "source_role": pl.String,
    "upstream_locator": pl.String,
    "upstream_version": pl.String,
    "content_sha256": pl.String,
    "source_published_at_utc": UTC_DATETIME,
    "retrieved_at_utc": UTC_DATETIME,
    "knowledge_available_at_utc": UTC_DATETIME,
    "license_id": pl.String,
    "raw_object_key": pl.String,
}

NORMALIZATION_DEFINITION_SCHEMA: dict[str, pl.DataType] = {
    "normalization_id": pl.String,
    "source_snapshot_id": pl.String,
    "normalizer_name": pl.String,
    "normalizer_version": pl.String,
    "canonical_schema_version": pl.String,
}

PLAY_SEQUENCE_OBSERVATION_SCHEMA: dict[str, pl.DataType] = {
    "normalization_id": pl.String,
    "source_snapshot_id": pl.String,
    "game_pk": pl.Int64,
    "at_bat_index": pl.Int64,
    "payload_hash": pl.String,
    "duplicate_row_count": pl.Int64,
    "classification_status": pl.String,
    "result_event_type": pl.String,
    "result_event": pl.String,
    "result_description": pl.String,
    "is_plate_appearance": pl.Boolean,
    "event_semantics_snapshot_id": pl.String,
    "batter_mlbam_id": pl.Int64,
    "pitcher_mlbam_id": pl.Int64,
    "batter_side": pl.String,
    "pitcher_hand": pl.String,
    "inning": pl.Int64,
    "half_inning": pl.String,
    "sequence_start_time": UTC_DATETIME,
    "sequence_end_time": UTC_DATETIME,
    "official_physical_pitch_count": pl.Int64,
}

PITCH_OBSERVATION_SCHEMA: dict[str, pl.DataType] = {
    "normalization_id": pl.String,
    "source_snapshot_id": pl.String,
    "game_pk": pl.Int64,
    "at_bat_index": pl.Int64,
    "pitch_number": pl.Int64,
    "payload_hash": pl.String,
    "duplicate_row_count": pl.Int64,
    "source_batter_mlbam_id": pl.Int64,
    "source_pitcher_mlbam_id": pl.Int64,
    "batter_side": pl.String,
    "pitcher_hand": pl.String,
    "pitch_code": pl.String,
    "is_in_play": pl.Boolean,
    "bb_type": pl.String,
    "hit_location": pl.Int64,
    "hc_x": pl.Float64,
    "hc_y": pl.Float64,
    "pitch_type": pl.String,
    "pitch_name": pl.String,
    "release_speed": pl.Float64,
    "release_pos_x": pl.Float64,
    "release_pos_y": pl.Float64,
    "release_pos_z": pl.Float64,
    "plate_x": pl.Float64,
    "plate_z": pl.Float64,
    "pfx_x": pl.Float64,
    "pfx_z": pl.Float64,
    "release_spin_rate": pl.Float64,
    "spin_axis": pl.Float64,
    "release_extension": pl.Float64,
    "launch_speed": pl.Float64,
    "launch_angle": pl.Float64,
    "hit_distance": pl.Float64,
}

PLAYER_CROSSWALK_OBSERVATION_SCHEMA: dict[str, pl.DataType] = {
    "normalization_id": pl.String,
    "source_snapshot_id": pl.String,
    "mlbam_id": pl.Int64,
    "chadwick_uuid": pl.String,
    "chadwick_person": pl.String,
    "fangraphs_id": pl.String,
    "bbref_id": pl.String,
    "bbref_minors_id": pl.String,
    "retrosheet_id": pl.String,
    "name_first": pl.String,
    "name_last": pl.String,
    "birth_year": pl.Int64,
    "birth_month": pl.Int64,
    "birth_day": pl.Int64,
    "pro_played_first": pl.Int64,
    "pro_played_last": pl.Int64,
    "mlb_played_first": pl.Int64,
    "mlb_played_last": pl.Int64,
}

QUALITY_ISSUE_SCHEMA: dict[str, pl.DataType] = {
    "quality_issue_id": pl.String,
    "issue_code": pl.String,
    "severity": pl.String,
    "entity_type": pl.String,
    "game_pk": pl.Int64,
    "at_bat_index": pl.Int64,
    "pitch_number": pl.Int64,
    "mlbam_id": pl.Int64,
    "source_snapshot_id": pl.String,
    "normalization_id": pl.String,
    "check_name": pl.String,
    "check_version": pl.String,
    "detected_at_utc": UTC_DATETIME,
    "details_json": pl.String,
}

SOURCE_SNAPSHOT_REQUIRED = {
    "source_snapshot_id",
    "source_name",
    "source_role",
    "upstream_locator",
    "content_sha256",
    "retrieved_at_utc",
    "raw_object_key",
}
NORMALIZATION_REQUIRED = set(NORMALIZATION_DEFINITION_SCHEMA)
PLAY_SEQUENCE_REQUIRED = {
    "normalization_id",
    "source_snapshot_id",
    "game_pk",
    "at_bat_index",
    "payload_hash",
    "duplicate_row_count",
    "classification_status",
}
PITCH_REQUIRED = {
    "normalization_id",
    "source_snapshot_id",
    "game_pk",
    "at_bat_index",
    "pitch_number",
    "payload_hash",
    "duplicate_row_count",
}
PLAYER_CROSSWALK_REQUIRED = {
    "normalization_id",
    "source_snapshot_id",
    "mlbam_id",
}
QUALITY_ISSUE_REQUIRED = {
    "quality_issue_id",
    "issue_code",
    "severity",
    "entity_type",
    "check_name",
    "check_version",
    "detected_at_utc",
    "details_json",
}

_ALLOWED_SEQUENCE_STATUS = {
    "official_true_pa",
    "official_non_pa",
    "unclassified_source_sequence",
}
_ALLOWED_SEVERITY = {"info", "warning", "error", "quarantine"}
_ALLOWED_ENTITY_TYPE = {
    "source_snapshot",
    "game",
    "play_sequence",
    "pitch",
    "player_crosswalk",
}
_HEX64_PATTERN = r"^[0-9a-f]{64}$"


def conform_to_schema(
    frame: pl.DataFrame,
    *,
    schema: Mapping[str, pl.DataType],
    required_columns: Iterable[str],
    table_name: str,
    allow_extra: bool = False,
) -> pl.DataFrame:
    """Return an exact typed canonical frame or fail on ambiguous structure.

    Missing optional columns are added as typed nulls. Missing required columns
    fail. Extra columns fail by default so a source adapter cannot accidentally
    discard newly appearing evidence while claiming to emit a canonical table.
    Casting is strict: invalid source strings must be cleaned/flagged in the
    source adapter rather than silently becoming null here.
    """

    expected = set(schema)
    required = set(required_columns)
    missing_required = sorted(required - set(frame.columns))
    if missing_required:
        raise ValueError(
            f"{table_name} missing required columns: {missing_required}"
        )

    extra = sorted(set(frame.columns) - expected)
    if extra and not allow_extra:
        raise ValueError(f"{table_name} has undeclared columns: {extra}")

    result = frame
    missing_optional = [column for column in schema if column not in result.columns]
    if missing_optional:
        result = result.with_columns(
            [
                pl.lit(None, dtype=schema[column]).alias(column)
                for column in missing_optional
            ]
        )

    result = result.select(list(schema)).cast(dict(schema), strict=True)
    return result


def _assert_non_null(frame: pl.DataFrame, columns: Iterable[str], table_name: str) -> None:
    columns = list(columns)
    if not columns:
        return
    null_rows = frame.filter(
        pl.any_horizontal([pl.col(column).is_null() for column in columns])
    )
    if not null_rows.is_empty():
        raise ValueError(
            f"{table_name} has {null_rows.height} rows with null required key values "
            f"in {columns}"
        )


def _assert_unique(frame: pl.DataFrame, columns: Iterable[str], table_name: str) -> None:
    columns = list(columns)
    duplicates = (
        frame.group_by(columns)
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise ValueError(
            f"{table_name} has {duplicates.height} duplicate key groups for {columns}"
        )


def _assert_hex64(frame: pl.DataFrame, column: str, table_name: str) -> None:
    invalid = frame.filter(
        pl.col(column).is_null()
        | ~pl.col(column).str.contains(_HEX64_PATTERN)
    )
    if not invalid.is_empty():
        raise ValueError(
            f"{table_name}.{column} contains {invalid.height} invalid SHA-256-like IDs"
        )


def _assert_positive_duplicate_counts(frame: pl.DataFrame, table_name: str) -> None:
    invalid = frame.filter(pl.col("duplicate_row_count") < 1)
    if not invalid.is_empty():
        raise ValueError(
            f"{table_name} has {invalid.height} rows with duplicate_row_count < 1"
        )


def validate_source_snapshot(frame: pl.DataFrame) -> pl.DataFrame:
    result = conform_to_schema(
        frame,
        schema=SOURCE_SNAPSHOT_SCHEMA,
        required_columns=SOURCE_SNAPSHOT_REQUIRED,
        table_name="source_snapshot",
    )
    _assert_non_null(result, SOURCE_SNAPSHOT_REQUIRED, "source_snapshot")
    _assert_unique(result, ["source_snapshot_id"], "source_snapshot")
    _assert_hex64(result, "source_snapshot_id", "source_snapshot")
    _assert_hex64(result, "content_sha256", "source_snapshot")
    impossible = result.filter(
        pl.col("knowledge_available_at_utc").is_not_null()
        & (pl.col("knowledge_available_at_utc") > pl.col("retrieved_at_utc"))
    )
    if not impossible.is_empty():
        raise ValueError(
            "source_snapshot contains knowledge_available_at_utc after retrieval"
        )
    return result


def validate_normalization_definition(frame: pl.DataFrame) -> pl.DataFrame:
    result = conform_to_schema(
        frame,
        schema=NORMALIZATION_DEFINITION_SCHEMA,
        required_columns=NORMALIZATION_REQUIRED,
        table_name="normalization_definition",
    )
    _assert_non_null(result, NORMALIZATION_REQUIRED, "normalization_definition")
    _assert_unique(result, ["normalization_id"], "normalization_definition")
    _assert_hex64(result, "normalization_id", "normalization_definition")
    _assert_hex64(result, "source_snapshot_id", "normalization_definition")
    return result


def validate_play_sequence_observation(frame: pl.DataFrame) -> pl.DataFrame:
    result = conform_to_schema(
        frame,
        schema=PLAY_SEQUENCE_OBSERVATION_SCHEMA,
        required_columns=PLAY_SEQUENCE_REQUIRED,
        table_name="play_sequence_observation",
    )
    key = [
        "normalization_id",
        "game_pk",
        "at_bat_index",
        "payload_hash",
    ]
    _assert_non_null(result, PLAY_SEQUENCE_REQUIRED, "play_sequence_observation")
    _assert_unique(result, key, "play_sequence_observation")
    _assert_hex64(result, "normalization_id", "play_sequence_observation")
    _assert_hex64(result, "source_snapshot_id", "play_sequence_observation")
    _assert_hex64(result, "payload_hash", "play_sequence_observation")
    _assert_positive_duplicate_counts(result, "play_sequence_observation")

    invalid_status = result.filter(
        ~pl.col("classification_status").is_in(sorted(_ALLOWED_SEQUENCE_STATUS))
    )
    if not invalid_status.is_empty():
        raise ValueError("play_sequence_observation contains invalid classification_status")

    true_pa_mismatch = result.filter(
        (pl.col("classification_status") == "official_true_pa")
        & (pl.col("is_plate_appearance") != True)  # noqa: E712
    )
    non_pa_mismatch = result.filter(
        (pl.col("classification_status") == "official_non_pa")
        & (pl.col("is_plate_appearance") != False)  # noqa: E712
    )
    unclassified_has_boolean = result.filter(
        (pl.col("classification_status") == "unclassified_source_sequence")
        & pl.col("is_plate_appearance").is_not_null()
    )
    if not true_pa_mismatch.is_empty() or not non_pa_mismatch.is_empty() or not unclassified_has_boolean.is_empty():
        raise ValueError(
            "play_sequence_observation classification_status disagrees with is_plate_appearance"
        )
    return result


def validate_pitch_observation(frame: pl.DataFrame) -> pl.DataFrame:
    result = conform_to_schema(
        frame,
        schema=PITCH_OBSERVATION_SCHEMA,
        required_columns=PITCH_REQUIRED,
        table_name="pitch_observation",
    )
    key = [
        "normalization_id",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "payload_hash",
    ]
    _assert_non_null(result, PITCH_REQUIRED, "pitch_observation")
    _assert_unique(result, key, "pitch_observation")
    _assert_hex64(result, "normalization_id", "pitch_observation")
    _assert_hex64(result, "source_snapshot_id", "pitch_observation")
    _assert_hex64(result, "payload_hash", "pitch_observation")
    _assert_positive_duplicate_counts(result, "pitch_observation")
    invalid_pitch_numbers = result.filter(pl.col("pitch_number") < 1)
    if not invalid_pitch_numbers.is_empty():
        raise ValueError("pitch_observation contains pitch_number < 1")
    return result


def validate_player_crosswalk_observation(frame: pl.DataFrame) -> pl.DataFrame:
    result = conform_to_schema(
        frame,
        schema=PLAYER_CROSSWALK_OBSERVATION_SCHEMA,
        required_columns=PLAYER_CROSSWALK_REQUIRED,
        table_name="player_crosswalk_observation",
    )
    _assert_non_null(result, PLAYER_CROSSWALK_REQUIRED, "player_crosswalk_observation")
    _assert_unique(
        result,
        ["normalization_id", "mlbam_id"],
        "player_crosswalk_observation",
    )
    _assert_hex64(result, "normalization_id", "player_crosswalk_observation")
    _assert_hex64(result, "source_snapshot_id", "player_crosswalk_observation")
    return result


def validate_quality_issue(frame: pl.DataFrame) -> pl.DataFrame:
    result = conform_to_schema(
        frame,
        schema=QUALITY_ISSUE_SCHEMA,
        required_columns=QUALITY_ISSUE_REQUIRED,
        table_name="quality_issue",
    )
    _assert_non_null(result, QUALITY_ISSUE_REQUIRED, "quality_issue")
    _assert_unique(result, ["quality_issue_id"], "quality_issue")
    _assert_hex64(result, "quality_issue_id", "quality_issue")

    invalid_severity = result.filter(~pl.col("severity").is_in(sorted(_ALLOWED_SEVERITY)))
    if not invalid_severity.is_empty():
        raise ValueError("quality_issue contains invalid severity")
    invalid_entity = result.filter(~pl.col("entity_type").is_in(sorted(_ALLOWED_ENTITY_TYPE)))
    if not invalid_entity.is_empty():
        raise ValueError("quality_issue contains invalid entity_type")
    return result
