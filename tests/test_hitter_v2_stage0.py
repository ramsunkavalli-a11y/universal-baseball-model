from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.hitter_v2_stage0 import (
    add_2024_weight_woba,
    require_stage0_seasons,
    validate_official_outcomes,
)


def _official_row() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2024],
            "player_id": [1],
            "player_name": ["Diagnostic Player"],
            "pa": [10],
            "ab": [8],
            "h": [4],
            "double": [1],
            "triple": [1],
            "hr": [1],
            "bb": [1],
            "ibb": [0],
            "hbp": [0],
            "k": [2],
            "sf": [1],
            "sh": [0],
        }
    )


def test_stage0_season_guard_rejects_protected_or_incomplete_outcomes() -> None:
    assert require_stage0_seasons([2024, 2022, 2021, 2023]) == (2021, 2022, 2023, 2024)
    with pytest.raises(ValueError, match="fixed to 2021-2024"):
        require_stage0_seasons([2021, 2022, 2023, 2024, 2025])


def test_woba_uses_unintentional_walks_and_distinct_hit_values() -> None:
    scored = add_2024_weight_woba(validate_official_outcomes(_official_row()))
    row = scored.row(0, named=True)
    expected_numerator = 0.689 + 0.882 + 1.254 + 1.590 + 2.050
    assert row["single"] == 1
    assert row["ubb"] == 1
    assert row["woba_denominator"] == 10
    assert row["woba_2024_weights"] == pytest.approx(expected_numerator / 10)


def test_official_outcome_validation_fails_on_impossible_hit_components() -> None:
    invalid = _official_row().with_columns(pl.lit(5).alias("double"))
    with pytest.raises(ValueError, match="impossible component counts"):
        validate_official_outcomes(invalid)
