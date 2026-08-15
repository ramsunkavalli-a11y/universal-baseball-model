from __future__ import annotations

import json

import polars as pl
import pytest

from universal_baseball.canonical_schema import validate_pitch_observation
from universal_baseball.resolution import (
    CROSS_SNAPSHOT_RESOLUTION_POLICY,
    pitch_resolution_conflicts,
    resolve_pitch_observations_across_snapshots,
    resolve_pitch_observations_within_snapshot,
)


NORMALIZATION = "a" * 64
SNAPSHOT = "b" * 64
SECOND_NORMALIZATION = "e" * 64
SECOND_SNAPSHOT = "f" * 64


def _row(payload_hash: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "normalization_id": NORMALIZATION,
        "source_snapshot_id": SNAPSHOT,
        "game_pk": 1,
        "at_bat_index": 2,
        "pitch_number": 3,
        "payload_hash": payload_hash,
        "duplicate_row_count": 1,
        "pitch_code": "X",
        "is_in_play": True,
        "bb_type": "line_drive",
        "hc_x": 120.0,
        "hc_y": 90.0,
        "release_speed": 95.0,
    }
    row.update(overrides)
    return row


def _normalization_definitions(*, second_version: str = "1") -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "normalization_id": NORMALIZATION,
                "source_snapshot_id": SNAPSHOT,
                "normalizer_name": "armstjc_adapter",
                "normalizer_version": "1",
                "canonical_schema_version": "0.1",
            },
            {
                "normalization_id": SECOND_NORMALIZATION,
                "source_snapshot_id": SECOND_SNAPSHOT,
                "normalizer_name": "armstjc_adapter",
                "normalizer_version": second_version,
                "canonical_schema_version": "0.1",
            },
        ]
    )


def test_resolver_accepts_stable_values_across_payload_variants() -> None:
    observations = validate_pitch_observation(
        pl.DataFrame(
            [
                _row("c" * 64, duplicate_row_count=2),
                _row("d" * 64, duplicate_row_count=1),
            ]
        )
    )

    resolved = resolve_pitch_observations_within_snapshot(observations)
    row = resolved.to_dicts()[0]

    assert resolved.height == 1
    assert row["observation_variant_count"] == 2
    assert row["raw_source_row_count"] == 3
    assert row["release_speed"] == 95.0
    assert row["conflict_field_count"] == 0
    assert json.loads(row["conflict_fields_json"]) == []


def test_null_and_one_non_null_value_resolve_to_the_observed_value() -> None:
    observations = validate_pitch_observation(
        pl.DataFrame(
            [
                _row("c" * 64, release_speed=None),
                _row("d" * 64, release_speed=95.0),
            ]
        )
    )

    row = resolve_pitch_observations_within_snapshot(observations).to_dicts()[0]
    assert row["release_speed"] == 95.0
    assert row["conflict_field_count"] == 0


def test_conflicting_non_null_values_become_null_and_explicit_conflict() -> None:
    observations = validate_pitch_observation(
        pl.DataFrame(
            [
                _row("c" * 64, release_speed=95.0, hc_x=120.0),
                _row("d" * 64, release_speed=95.4, hc_x=120.0),
            ]
        )
    )

    resolved = resolve_pitch_observations_within_snapshot(observations)
    row = resolved.to_dicts()[0]

    assert row["release_speed"] is None
    assert row["hc_x"] == 120.0
    assert row["conflict_field_count"] == 1
    assert json.loads(row["conflict_fields_json"]) == ["release_speed"]
    assert pitch_resolution_conflicts(resolved).height == 1


def test_resolver_refuses_to_cross_source_snapshots_or_normalizations() -> None:
    first = _row("c" * 64)
    second = _row("d" * 64)
    second["source_snapshot_id"] = "e" * 64
    observations = validate_pitch_observation(pl.DataFrame([first, second]))
    with pytest.raises(ValueError, match="one source_snapshot_id"):
        resolve_pitch_observations_within_snapshot(observations)

    second = _row("d" * 64)
    second["normalization_id"] = "f" * 64
    observations = validate_pitch_observation(pl.DataFrame([first, second]))
    with pytest.raises(ValueError, match="one normalization_id"):
        resolve_pitch_observations_within_snapshot(observations)


def test_cross_snapshot_resolver_uses_field_consensus_without_row_winner() -> None:
    observations = validate_pitch_observation(
        pl.DataFrame(
            [
                _row("c" * 64, release_speed=None, duplicate_row_count=2),
                _row(
                    "d" * 64,
                    normalization_id=SECOND_NORMALIZATION,
                    source_snapshot_id=SECOND_SNAPSHOT,
                    release_speed=95.0,
                    duplicate_row_count=1,
                ),
            ]
        )
    )

    row = resolve_pitch_observations_across_snapshots(
        observations,
        _normalization_definitions(),
    ).to_dicts()[0]

    assert row["source_snapshot_count"] == 2
    assert row["normalization_count"] == 2
    assert row["observation_variant_count"] == 2
    assert row["raw_source_row_count"] == 3
    assert row["release_speed"] == 95.0
    assert row["conflict_fields"] == []
    assert row["conflict_field_count"] == 0
    assert row["resolution_policy"] == CROSS_SNAPSHOT_RESOLUTION_POLICY
    assert row["source_snapshot_ids"] == sorted([SNAPSHOT, SECOND_SNAPSHOT])


def test_cross_snapshot_resolver_nulls_disagreement_instead_of_inferring_latest() -> None:
    observations = validate_pitch_observation(
        pl.DataFrame(
            [
                _row("c" * 64, release_speed=95.0, hc_x=120.0),
                _row(
                    "d" * 64,
                    normalization_id=SECOND_NORMALIZATION,
                    source_snapshot_id=SECOND_SNAPSHOT,
                    release_speed=95.4,
                    hc_x=120.0,
                ),
            ]
        )
    )

    resolved = resolve_pitch_observations_across_snapshots(
        observations,
        _normalization_definitions(),
    )
    row = resolved.to_dicts()[0]

    assert row["release_speed"] is None
    assert row["hc_x"] == 120.0
    assert row["conflict_fields"] == ["release_speed"]
    assert row["conflict_field_count"] == 1
    assert pitch_resolution_conflicts(resolved).height == 1


def test_cross_snapshot_resolver_preserves_conflict_from_variants_inside_one_snapshot() -> None:
    observations = validate_pitch_observation(
        pl.DataFrame(
            [
                _row("c" * 64, release_speed=95.0),
                _row("d" * 64, release_speed=95.4),
                _row(
                    "1" * 64,
                    normalization_id=SECOND_NORMALIZATION,
                    source_snapshot_id=SECOND_SNAPSHOT,
                    release_speed=95.0,
                ),
            ]
        )
    )

    row = resolve_pitch_observations_across_snapshots(
        observations,
        _normalization_definitions(),
    ).to_dicts()[0]

    assert row["release_speed"] is None
    assert row["conflict_fields"] == ["release_speed"]
    assert row["source_snapshot_count"] == 2
    assert row["observation_variant_count"] == 3


def test_cross_snapshot_resolver_rejects_mixed_normalizer_versions() -> None:
    observations = validate_pitch_observation(
        pl.DataFrame(
            [
                _row("c" * 64),
                _row(
                    "d" * 64,
                    normalization_id=SECOND_NORMALIZATION,
                    source_snapshot_id=SECOND_SNAPSHOT,
                ),
            ]
        )
    )

    with pytest.raises(ValueError, match="cannot mix normalizer/schema versions"):
        resolve_pitch_observations_across_snapshots(
            observations,
            _normalization_definitions(second_version="2"),
        )
