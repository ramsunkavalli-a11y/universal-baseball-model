from __future__ import annotations

from datetime import UTC, datetime
import json

import polars as pl

from universal_baseball.quality import quality_issues_from_resolution_conflicts


NOW = datetime(2026, 8, 15, 22, tzinfo=UTC)


def test_pitch_resolution_conflict_becomes_one_deterministic_quality_issue() -> None:
    resolved = pl.DataFrame(
        {
            "game_pk": [1, 1],
            "at_bat_index": [2, 2],
            "pitch_number": [3, 4],
            "conflict_field_count": [2, 0],
            "conflict_fields": [["pitcher_hand", "batter_side"], []],
            "source_snapshot_ids": [["b" * 64, "a" * 64], ["a" * 64]],
            "normalization_ids": [["d" * 64, "c" * 64], ["c" * 64]],
        }
    )

    first = quality_issues_from_resolution_conflicts(
        resolved,
        entity_type="pitch",
        detected_at_utc=NOW,
    )
    second = quality_issues_from_resolution_conflicts(
        resolved,
        entity_type="pitch",
        detected_at_utc=datetime(2026, 8, 16, 1, tzinfo=UTC),
    )

    assert first.height == 1
    row = first.to_dicts()[0]
    assert row["game_pk"] == 1
    assert row["at_bat_index"] == 2
    assert row["pitch_number"] == 3
    assert row["entity_type"] == "pitch"
    assert row["source_snapshot_id"] is None
    assert row["normalization_id"] is None
    assert first.get_column("quality_issue_id").to_list() == second.get_column(
        "quality_issue_id"
    ).to_list()
    details = json.loads(row["details_json"])
    assert details["conflict_fields"] == ["batter_side", "pitcher_hand"]
    assert details["source_snapshot_ids"] == ["a" * 64, "b" * 64]


def test_game_resolution_conflict_uses_game_grain() -> None:
    resolved = pl.DataFrame(
        {
            "game_pk": [10],
            "conflict_field_count": [1],
            "conflict_fields": [["home_team"]],
            "source_snapshot_ids": [["a" * 64, "b" * 64]],
            "normalization_ids": [["c" * 64, "d" * 64]],
        }
    )

    row = quality_issues_from_resolution_conflicts(
        resolved,
        entity_type="game",
        detected_at_utc=NOW,
    ).to_dicts()[0]

    assert row["entity_type"] == "game"
    assert row["game_pk"] == 10
    assert row["at_bat_index"] is None
    assert row["pitch_number"] is None
