from __future__ import annotations

import polars as pl

from universal_baseball.source_comparison import (
    compare_pitch_source_to_official_pas,
    select_diverse_game_ids,
)


def test_compare_pitch_source_to_official_pas_ignores_exact_duplicates_for_comparison() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1", "1", "1", "1"],
            "game_date": ["2025-03-28"] * 6,
            "at_bat_number": ["0", "0", "0", "0", "1", "1"],
            "pitch_number": ["1", "1", "2", "2", "1", "1"],
            "description": [
                "Batter strikes out.",
                "Batter strikes out.",
                "Batter strikes out.",
                "Batter strikes out.",
                "Batter singles.",
                "Batter singles.",
            ],
            "events": [None] * 6,
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "1"],
            "result_type": ["atBat", "atBat"],
            "event": ["Strikeout", "Single"],
            "event_type": ["strikeout", "single"],
            "description": ["Batter strikes out.", "Batter singles."],
            "official_pitch_count": [2, 1],
        }
    )

    result = compare_pitch_source_to_official_pas(source, official)

    assert result["source_rows_raw"] == 6
    assert result["source_rows_after_exact_dedup_for_comparison"] == 3
    assert result["source_pa_count"] == 2
    assert result["official_pa_count"] == 2
    assert result["shared_pa_count"] == 2
    assert result["pitch_count_mismatch_pa_count"] == 0
    assert result["description_mismatch_pa_count"] == 0
    assert result["official_event_type_nonblank_pa_count"] == 2
    assert result["source_events_nonblank_pitch_row_count"] == 0


def test_compare_reports_missing_pa_and_pitch_count_disagreement() -> None:
    source = pl.DataFrame(
        {
            "game_pk": ["1", "1", "1"],
            "at_bat_number": ["0", "0", "2"],
            "pitch_number": ["1", "2", "1"],
            "description": ["A", "A", "C"],
        }
    )
    official = pl.DataFrame(
        {
            "game_pk": ["1", "1"],
            "at_bat_number": ["0", "1"],
            "event": ["Walk", "Single"],
            "event_type": ["walk", "single"],
            "description": ["A", "B"],
            "official_pitch_count": [3, 1],
        }
    )

    result = compare_pitch_source_to_official_pas(source, official)

    assert result["shared_pa_count"] == 1
    assert result["source_only_pa_count"] == 1
    assert result["official_only_pa_count"] == 1
    assert result["pitch_count_mismatch_pa_count"] == 1


def test_select_diverse_game_ids_spans_observed_dates() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["10", "20", "30", "40", "50"],
            "game_date": [
                "2025-03-28",
                "2025-03-29",
                "2025-04-02",
                "2025-04-10",
                "2025-04-23",
            ],
        }
    )

    assert select_diverse_game_ids(frame, limit=3) == [10, 30, 50]
