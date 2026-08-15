from __future__ import annotations

import polars as pl

from universal_baseball.partition_audit import compare_adjacent_partitions


def test_adjacent_partition_audit_separates_overlap_from_new_rows() -> None:
    left = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1", "1", "2"],
            "at_bat_number": ["0", "0", "0", "0", "0"],
            "pitch_number": ["1", "1", "2", "2", "1"],
            "game_date": ["2025-03-28", "2025-03-28", "2025-03-28", "2025-03-28", "2025-04-02"],
            "game_month": ["3", "3", "3", "3", "4"],
            "value": ["a", "a", "b", "b", "c"],
        }
    )
    right = pl.DataFrame(
        {
            "game_pk": ["2", "3"],
            "at_bat_number": ["0", "0"],
            "pitch_number": ["1", "1"],
            "game_date": ["2025-04-02", "2025-04-03"],
            "game_month": ["4", "4"],
            "value": ["c", "d"],
        }
    )

    result = compare_adjacent_partitions(left, right)

    assert result["left"]["raw_rows"] == 5
    assert result["left"]["exact_unique_rows"] == 3
    assert result["left"]["exact_duplicate_extra_rows"] == 2
    assert result["overlap"]["natural_key_count"] == 1
    assert result["overlap"]["identical_full_row_key_count"] == 1
    assert result["overlap"]["changed_full_row_key_count"] == 0
    assert result["overlap"]["left_only_natural_key_count"] == 2
    assert result["overlap"]["right_only_natural_key_count"] == 1
    assert result["overlap"]["natural_keys_by_game_date"] == [
        {"game_date": "2025-04-02", "len": 1}
    ]


def test_adjacent_partition_audit_flags_changed_overlap() -> None:
    left = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": ["1"],
            "game_date": ["2025-04-01"],
            "game_month": ["4"],
            "value": ["old"],
        }
    )
    right = pl.DataFrame(
        {
            "game_pk": ["1"],
            "at_bat_number": ["0"],
            "pitch_number": ["1"],
            "game_date": ["2025-04-01"],
            "game_month": ["4"],
            "value": ["new"],
        }
    )

    result = compare_adjacent_partitions(left, right)

    assert result["overlap"]["natural_key_count"] == 1
    assert result["overlap"]["identical_full_row_key_count"] == 0
    assert result["overlap"]["changed_full_row_key_count"] == 1
