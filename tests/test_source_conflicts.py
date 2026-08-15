from __future__ import annotations

import polars as pl

from universal_baseball.source_conflicts import profile_natural_key_conflicts


def test_conflict_profiler_separates_exact_duplicates_from_changed_payloads() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1", "1", "1"],
            "at_bat_number": ["0", "0", "0", "0", "0"],
            "pitch_number": ["1", "1", "2", "2", "2"],
            "release_speed": ["94.0", "94.0", "85.0", "85.2", "85.2"],
            "play_end_datetime": ["a", "a", "b", "c", "c"],
            "description": ["Ball", "Ball", "Strike", "Strike", "Strike"],
        }
    )

    result = profile_natural_key_conflicts(frame)

    assert result["available"] is True
    assert result["raw_rows"] == 5
    assert result["exact_unique_rows"] == 3
    assert result["natural_key_unique_rows"] == 2
    assert result["conflicting_key_group_count"] == 1
    assert result["conflicting_key_extra_rows"] == 1
    assert result["variant_count_distribution"] == {"2": 1}
    assert result["changed_column_group_counts"] == {
        "play_end_datetime": 1,
        "release_speed": 1,
    }
    assert result["examples"][0]["pitch_number"] == "2"
    assert set(result["examples"][0]["changed_columns"]) == {
        "play_end_datetime",
        "release_speed",
    }


def test_conflict_profiler_reports_missing_key_columns() -> None:
    result = profile_natural_key_conflicts(pl.DataFrame({"game_pk": ["1"]}))

    assert result["available"] is False
    assert result["missing_key_columns"] == ["at_bat_number", "pitch_number"]
