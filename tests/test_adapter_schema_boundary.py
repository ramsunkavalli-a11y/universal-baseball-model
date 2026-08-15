from __future__ import annotations

import polars as pl

from universal_baseball.canonical_adapters import normalize_armstjc_pitch_observations


SNAPSHOT = "a" * 64
NORMALIZATION = "b" * 64


def test_armstjc_adapter_uses_canonical_types_before_sparse_late_values() -> None:
    """A late valid float must not depend on Polars' schema-inference window."""

    row_count = 120
    raw = pl.DataFrame(
        {
            "game_pk": ["1"] * row_count,
            "at_bat_number": [str(index) for index in range(row_count)],
            "pitch_number": ["1"] * row_count,
            "type": ["B"] * row_count,
            "release_spin_rate": [None] * (row_count - 1) + ["2302.0"],
            "release_speed": [None] * (row_count - 1) + ["94.7"],
        },
        schema_overrides={
            "release_spin_rate": pl.String,
            "release_speed": pl.String,
        },
    )

    result = normalize_armstjc_pitch_observations(
        raw,
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )

    assert result.schema["release_spin_rate"] == pl.Float64
    assert result.schema["release_speed"] == pl.Float64
    last = result.filter(pl.col("at_bat_index") == row_count - 1).to_dicts()[0]
    assert last["release_spin_rate"] == 2302.0
    assert last["release_speed"] == 94.7
