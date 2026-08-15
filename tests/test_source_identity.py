from __future__ import annotations

import polars as pl

from universal_baseball.source_identity import compare_source_mlbam_ids


def test_source_identity_matches_official_true_pas_and_ignores_duplicate_rows() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1", "1"],
            "at_bat_number": ["0", "0", "0", "1"],
            "pitch_number": ["1", "1", "2", "1"],
            "batter": ["101", "101", "101", "102"],
            "pitcher": ["201", "201", "201", "202"],
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "1"],
            "batter_id": [101, 102],
            "pitcher_id": [201, 202],
            "event_type": ["strikeout", "single"],
        }
    )

    result = compare_source_mlbam_ids(source, official)

    assert result["shared_sequence_true_pa_count"] == 2
    assert result["identity_comparison_count"] == 4
    assert result["identity_match_count"] == 4
    assert result["identity_mismatch_count"] == 0
    assert result["source_identity_conflict_count"] == 0
    assert result["certification_clean_on_shared_true_pas"] is True


def test_source_identity_reports_conflict_mismatch_and_non_pa_sequence_separately() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1", "1"],
            "at_bat_number": ["0", "0", "1", "2"],
            "pitch_number": ["1", "2", "1", "1"],
            "batter": ["101", "999", "102", "103"],
            "pitcher": ["201", "201", "777", "203"],
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "1"],
            "batter_id": [101, 102],
            "pitcher_id": [201, 202],
            "event_type": ["strikeout", "single"],
        }
    )

    result = compare_source_mlbam_ids(source, official)

    assert result["source_identity_conflict_count"] == 1
    assert result["identity_mismatch_count"] == 1
    assert result["source_only_pitch_sequence_count"] == 1
    assert result["source_only_pitch_sequence_examples"] == [
        {"game_pk": "1", "at_bat_number": "2"}
    ]
    assert result["certification_clean_on_shared_true_pas"] is False
