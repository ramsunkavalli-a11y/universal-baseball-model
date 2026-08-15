from __future__ import annotations

from datetime import UTC, datetime

import polars as pl
import pytest

from universal_baseball.canonical_schema import (
    CANONICAL_SCHEMA_VERSION,
    validate_normalization_definition,
    validate_pitch_observation,
    validate_play_sequence_observation,
    validate_provenance_links,
    validate_quality_issue,
    validate_source_snapshot,
)
from universal_baseball.provenance import NormalizationDefinition, SourceSnapshot


NOW = datetime(2026, 8, 15, 20, tzinfo=UTC)
SNAPSHOT_HASH = "a" * 64
PAYLOAD_HASH = "b" * 64
ISSUE_HASH = "c" * 64


def _snapshot() -> SourceSnapshot:
    return SourceSnapshot.build(
        source_name="test_source",
        source_role="historical_bootstrap",
        upstream_locator="test://asset",
        content_sha256=SNAPSHOT_HASH,
        retrieved_at_utc=NOW,
        raw_object_key="quarantine/test.csv",
    )


def _normalization() -> NormalizationDefinition:
    return NormalizationDefinition.build(
        source_snapshot_id=_snapshot().source_snapshot_id,
        normalizer_name="test_adapter",
        normalizer_version="1",
        canonical_schema_version=CANONICAL_SCHEMA_VERSION,
    )


def _provenance_frames() -> tuple[pl.DataFrame, pl.DataFrame]:
    snapshot = validate_source_snapshot(pl.DataFrame([_snapshot().as_record()]))
    normalization = validate_normalization_definition(
        pl.DataFrame([_normalization().as_record()])
    )
    return snapshot, normalization


def test_source_and_normalization_tables_add_typed_optional_columns() -> None:
    source_frame, normalized = _provenance_frames()
    assert source_frame.schema["knowledge_available_at_utc"] == pl.Datetime(
        time_unit="us", time_zone="UTC"
    )
    assert normalized.get_column("source_snapshot_id").to_list() == [
        _snapshot().source_snapshot_id
    ]


def test_canonical_table_rejects_undeclared_columns() -> None:
    row = _snapshot().as_record()
    row["surprise_source_field"] = "do not silently drop me"
    with pytest.raises(ValueError, match="undeclared columns"):
        validate_source_snapshot(pl.DataFrame([row]))


def test_play_sequence_supports_true_pa_non_pa_and_unclassified() -> None:
    normalization = _normalization()
    rows = [
        {
            "normalization_id": normalization.normalization_id,
            "source_snapshot_id": normalization.source_snapshot_id,
            "game_pk": 1,
            "at_bat_index": 1,
            "payload_hash": PAYLOAD_HASH,
            "duplicate_row_count": 1,
            "classification_status": "official_true_pa",
            "is_plate_appearance": True,
            "result_event_type": "single",
        },
        {
            "normalization_id": normalization.normalization_id,
            "source_snapshot_id": normalization.source_snapshot_id,
            "game_pk": 1,
            "at_bat_index": 2,
            "payload_hash": "d" * 64,
            "duplicate_row_count": 1,
            "classification_status": "official_non_pa",
            "is_plate_appearance": False,
            "result_event_type": "caught_stealing_2b",
        },
        {
            "normalization_id": normalization.normalization_id,
            "source_snapshot_id": normalization.source_snapshot_id,
            "game_pk": 1,
            "at_bat_index": 3,
            "payload_hash": "e" * 64,
            "duplicate_row_count": 1,
            "classification_status": "unclassified_source_sequence",
            "is_plate_appearance": None,
        },
    ]

    frame = validate_play_sequence_observation(pl.DataFrame(rows))
    assert frame.height == 3
    assert frame.get_column("result_description").null_count() == 3


def test_play_sequence_rejects_status_boolean_disagreement_including_null() -> None:
    normalization = _normalization()
    base = {
        "normalization_id": normalization.normalization_id,
        "source_snapshot_id": normalization.source_snapshot_id,
        "game_pk": 1,
        "at_bat_index": 1,
        "payload_hash": PAYLOAD_HASH,
        "duplicate_row_count": 1,
    }
    for status, value in [
        ("unclassified_source_sequence", True),
        ("official_true_pa", None),
        ("official_non_pa", None),
    ]:
        row = {**base, "classification_status": status, "is_plate_appearance": value}
        with pytest.raises(ValueError, match="classification_status"):
            validate_play_sequence_observation(pl.DataFrame([row]))


def test_pitch_observation_allows_payload_variants_but_not_duplicate_variant_keys() -> None:
    normalization = _normalization()
    base = {
        "normalization_id": normalization.normalization_id,
        "source_snapshot_id": normalization.source_snapshot_id,
        "game_pk": 1,
        "at_bat_index": 1,
        "pitch_number": 1,
        "duplicate_row_count": 1,
        "pitch_code": "X",
        "is_in_play": True,
        "bb_type": "line_drive",
        "hc_x": 110.0,
        "hc_y": 90.0,
    }
    first = {**base, "payload_hash": PAYLOAD_HASH}
    second = {**base, "payload_hash": "d" * 64, "hc_x": 111.0}

    frame = validate_pitch_observation(pl.DataFrame([first, second]))
    assert frame.height == 2
    with pytest.raises(ValueError, match="duplicate key groups"):
        validate_pitch_observation(pl.DataFrame([first, first]))


def test_pitch_observation_rejects_nonphysical_pitch_number_and_zero_duplicate_count() -> None:
    normalization = _normalization()
    base = {
        "normalization_id": normalization.normalization_id,
        "source_snapshot_id": normalization.source_snapshot_id,
        "game_pk": 1,
        "at_bat_index": 1,
        "pitch_number": 0,
        "payload_hash": PAYLOAD_HASH,
        "duplicate_row_count": 1,
    }
    with pytest.raises(ValueError, match="pitch_number < 1"):
        validate_pitch_observation(pl.DataFrame([base]))

    base["pitch_number"] = 1
    base["duplicate_row_count"] = 0
    with pytest.raises(ValueError, match="duplicate_row_count < 1"):
        validate_pitch_observation(pl.DataFrame([base]))


def test_observation_provenance_must_match_normalization_source_snapshot() -> None:
    snapshots, definitions = _provenance_frames()
    normalization = _normalization()
    observation = pl.DataFrame(
        {
            "normalization_id": [normalization.normalization_id],
            "source_snapshot_id": [normalization.source_snapshot_id],
        }
    )
    validate_provenance_links(
        observation,
        definitions,
        snapshots,
        table_name="fixture_observation",
    )

    bad = observation.with_columns(pl.lit("f" * 64).alias("source_snapshot_id"))
    with pytest.raises(ValueError, match="different source snapshot"):
        validate_provenance_links(
            bad,
            definitions,
            snapshots,
            table_name="fixture_observation",
        )


def test_quality_issue_enforces_controlled_severity_and_entity_type() -> None:
    valid = {
        "quality_issue_id": ISSUE_HASH,
        "issue_code": "crosswalk_pending",
        "severity": "warning",
        "entity_type": "player_crosswalk",
        "check_name": "chadwick_coverage",
        "check_version": "1",
        "detected_at_utc": NOW,
        "details_json": "{}",
    }
    assert validate_quality_issue(pl.DataFrame([valid])).height == 1

    invalid = {**valid, "quality_issue_id": "d" * 64, "severity": "maybe"}
    with pytest.raises(ValueError, match="invalid severity"):
        validate_quality_issue(pl.DataFrame([invalid]))
