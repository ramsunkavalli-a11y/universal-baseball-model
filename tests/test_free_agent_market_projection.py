from __future__ import annotations

import polars as pl

from universal_baseball.free_agent_market_projection import (
    _weighted_workload,
    classify_one_year_market_rows,
)


def _market() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "free_agent_year": [2025, 2025, 2025, 2025, 2025],
            "source_row_sequence": [1, 2, 3, 4, 5],
            "fangraphs_id": ["1", "2", "3", "3", "4"],
            "player_id": [101, 102, 103, 103, 104],
            "player_name": ["A", "B", "C", "C", "D"],
            "position": ["SS", "SP", "RF", "RF", "RP"],
            "age": [30, 31, 32, 32, 33],
            "contract_years": [1, 2, 1, 1, 1],
            "contract_effective_total_dollars": [
                5_000_000, 20_000_000, 2_000_000, 114_000, 100_000,
            ],
            "contract_value_status": ["reported_guaranteed_terms"] * 5,
            "identity_status": ["matched_unique"] * 5,
        }
    )


def test_one_year_sample_excludes_multi_year_repeat_and_below_minimum() -> None:
    result = classify_one_year_market_rows(_market())
    assert result.filter(pl.col("sample_eligible")).get_column("player_id").to_list() == [101]
    statuses = set(result.get_column("sample_status"))
    assert statuses == {"eligible", "not_one_year", "multiple_contracts_in_class", "below_major_league_minimum"}


def test_workload_is_fixed_denominator_321_and_normalizes_2020_schedule() -> None:
    history = pl.DataFrame(
        {
            "season": [2019, 2020, 2021],
            "player_id": [1, 1, 1],
            "pa": [600, 200, 300],
        }
    )
    result = _weighted_workload(
        history,
        player_ids=[1, 2],
        target_season=2022,
        workload_column="pa",
    )
    assert result[1] == (600 + 2 * 200 * 2.7 + 3 * 300) / 6
    assert result[2] == 0.0
