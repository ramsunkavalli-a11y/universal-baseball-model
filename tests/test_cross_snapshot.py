from __future__ import annotations

import polars as pl

from universal_baseball.canonical_adapters import normalize_armstjc_pitch_observations
from universal_baseball.cross_snapshot import compare_resolved_pitch_snapshots
from universal_baseball.resolution import resolve_pitch_observations_within_snapshot


LEFT_SNAPSHOT = "a" * 64
LEFT_NORMALIZATION = "b" * 64
RIGHT_SNAPSHOT = "c" * 64
RIGHT_NORMALIZATION = "d" * 64


def _resolved(raw_rows: list[dict[str, object]], *, left: bool) -> pl.DataFrame:
    observations = normalize_armstjc_pitch_observations(
        pl.DataFrame(raw_rows),
        source_snapshot_id=LEFT_SNAPSHOT if left else RIGHT_SNAPSHOT,
        normalization_id=LEFT_NORMALIZATION if left else RIGHT_NORMALIZATION,
    )
    return resolve_pitch_observations_within_snapshot(observations)


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "game_pk": "1",
        "at_bat_number": "2",
        "pitch_number": "3",
        "type": "X",
        "batter": "100",
        "pitcher": "200",
        "stand": "R",
        "p_throws": "L",
        "bb_type": "ground_ball",
        "hit_location": "5",
        "hc_x": "120.0",
        "hc_y": "90.0",
        "release_speed": "95.0",
    }
    row.update(overrides)
    return row


def test_representation_drift_disappears_after_canonical_normalization() -> None:
    left = _resolved([_row(hit_location="5.0")], left=True)
    right = _resolved([_row(hit_location="5")], left=False)

    report = compare_resolved_pitch_snapshots(left, right)

    assert report["shared_pitch_key_count"] == 1
    assert report["shared_keys_with_non_null_conflict"] == 0
    assert report["field_stats"]["hit_location"]["equal_non_null"] == 1


def test_one_sided_evidence_is_not_called_a_conflict() -> None:
    left = _resolved([_row(release_speed=None)], left=True)
    right = _resolved([_row(release_speed="95.0")], left=False)

    report = compare_resolved_pitch_snapshots(left, right)

    assert report["shared_keys_with_non_null_conflict"] == 0
    assert report["shared_keys_with_one_sided_evidence"] == 1
    assert report["field_stats"]["release_speed"]["right_only_non_null"] == 1


def test_two_different_non_null_values_are_substantive_conflict() -> None:
    left = _resolved([_row(release_speed="95.0")], left=True)
    right = _resolved([_row(release_speed="96.0")], left=False)

    report = compare_resolved_pitch_snapshots(left, right)

    assert report["shared_keys_with_non_null_conflict"] == 1
    assert report["shared_key_non_null_conflict_rate"] == 1.0
    assert report["fields_with_non_null_conflict"] == {"release_speed": 1}
    assert report["non_null_conflict_examples"][0]["conflicts"]["release_speed"] == {
        "left": 95.0,
        "right": 96.0,
    }


def test_within_snapshot_conflict_remains_distinct_from_cross_snapshot_conflict() -> None:
    left = _resolved(
        [
            _row(release_speed="95.0"),
            _row(release_speed="96.0"),
        ],
        left=True,
    )
    right = _resolved([_row(release_speed="95.0")], left=False)

    report = compare_resolved_pitch_snapshots(left, right)

    assert report["shared_keys_with_non_null_conflict"] == 0
    assert report["shared_keys_with_within_snapshot_conflict"] == 1
    assert report["field_stats"]["release_speed"]["left_within_snapshot_conflict"] == 1
    assert report["field_stats"]["release_speed"]["right_only_non_null"] == 1
