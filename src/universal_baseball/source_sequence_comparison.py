"""Semantic wrapper for reusable pitch-sequence versus official true-PA audits.

The earliest source POC called every source ``game_pk + atBatIndex`` group a
"source PA." Later certification proved that a physical pitch can belong to a
sequence that never becomes an official plate appearance. The legacy helper is
kept only so old generated reports remain reproducible; new code should use this
module's terminology.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.source_comparison import (
    compare_pitch_source_to_official_pas as _legacy_compare,
    select_diverse_game_ids,
)


_TOP_LEVEL_RENAMES = {
    "official_pa_rows": "official_true_pa_rows",
    "source_pa_count": "source_pitch_sequence_count",
    "official_pa_count": "official_true_pa_count",
    "shared_pa_count": "shared_sequence_true_pa_count",
    "source_only_pa_count": "source_only_pitch_sequence_count",
    "official_only_pa_count": "official_only_true_pa_count",
    "official_only_zero_pitch_pa_count": "official_only_zero_pitch_true_pa_count",
    "official_only_positive_pitch_pa_count": "official_only_positive_pitch_true_pa_count",
    "official_only_pa_examples": "official_only_true_pa_examples",
    "official_only_zero_pitch_pa_examples": "official_only_zero_pitch_true_pa_examples",
    "official_only_positive_pitch_pa_examples": "official_only_positive_pitch_true_pa_examples",
    "pitch_count_mismatch_pa_count": "pitch_count_mismatch_sequence_count",
    "description_mismatch_pa_count": "description_mismatch_sequence_count",
    "official_event_type_nonblank_pa_count": "official_event_type_nonblank_true_pa_count",
    "official_event_nonblank_pa_count": "official_event_nonblank_true_pa_count",
}

_PER_GAME_RENAMES = {
    "source_pa_count": "source_pitch_sequence_count",
    "official_pa_count": "official_true_pa_count",
    "shared_pa_count": "shared_sequence_true_pa_count",
    "source_only_pa_count": "source_only_pitch_sequence_count",
    "official_only_pa_count": "official_only_true_pa_count",
    "official_only_zero_pitch_pa_count": "official_only_zero_pitch_true_pa_count",
    "official_only_positive_pitch_pa_count": "official_only_positive_pitch_true_pa_count",
    "pitch_count_mismatch_pa_count": "pitch_count_mismatch_sequence_count",
}


def _rename_keys(row: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    return {mapping.get(key, key): value for key, value in row.items()}


def compare_pitch_source_to_official_true_pas(
    source: pl.DataFrame,
    official_true_pas: pl.DataFrame,
    official_pitch_events: pl.DataFrame | None = None,
) -> dict[str, Any]:
    """Compare source pitch-bearing sequences with official true plate appearances.

    The source side is grouped by ``game_pk + at_bat_number`` because that is the
    parent available in a pitch-grain historical table. A source group is called
    a **pitch-bearing sequence**, not a PA. The official frame has already been
    filtered through versioned MLB event semantics and therefore contains only
    true PAs.

    This wrapper intentionally returns no legacy ``source_pa_*`` keys. Any new
    consumer using the wrong terminology should fail loudly rather than silently
    perpetuating the POC naming error.
    """

    legacy = _legacy_compare(source, official_true_pas, official_pitch_events)
    result = _rename_keys(legacy, _TOP_LEVEL_RENAMES)
    result["per_game"] = [
        _rename_keys(row, _PER_GAME_RENAMES) for row in legacy.get("per_game", [])
    ]
    return result


__all__ = [
    "compare_pitch_source_to_official_true_pas",
    "select_diverse_game_ids",
]
