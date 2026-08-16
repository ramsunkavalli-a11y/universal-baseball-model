from dataclasses import dataclass

import polars as pl

from universal_baseball.current_talent_history import (
    summarize_historical_league_mapping,
    summarize_historical_source_coverage,
)


@dataclass(frozen=True)
class Asset:
    year: int
    filename_period: int
    filename_level: str
    size_bytes: int = 100


def test_historical_inventory_separates_presence_from_period_parity() -> None:
    levels = ("aaa", "aa")
    pbp = [
        Asset(2022, 4, "aaa"),
        Asset(2022, 5, "aaa"),
        Asset(2022, 4, "aa"),
        Asset(2023, 4, "aaa"),
        Asset(2023, 4, "aa"),
    ]
    games = [
        Asset(2022, 4, "aaa"),
        Asset(2022, 6, "aaa"),
        Asset(2022, 4, "aa"),
        Asset(2023, 4, "aaa"),
    ]
    result = summarize_historical_source_coverage(pbp, games, levels=levels)

    # 2022 has both source families at both levels, but AAA period coverage does
    # not match. Presence therefore remains a weaker planning concept.
    assert result["complete_all_level_years"] == [2022]
    assert result["latest_complete_all_level_year"] == 2022
    assert result["period_parity_all_level_years"] == []
    assert result["latest_period_parity_all_level_year"] is None

    aaa_2022 = next(
        row
        for row in result["year_level_cells"]
        if row["year"] == 2022 and row["filename_level"] == "aaa"
    )
    assert aaa_2022["pbp_periods"] == [4, 5]
    assert aaa_2022["player_game_periods"] == [4, 6]
    assert aaa_2022["common_periods"] == [4]
    assert aaa_2022["has_both_source_families"] is True
    assert aaa_2022["period_sets_match"] is False
    assert aaa_2022["common_period_coverage_ratio"] == 1 / 3


def test_historical_inventory_marks_year_with_matching_periods_at_every_level() -> None:
    levels = ("aaa", "aa")
    pbp = [
        Asset(2021, 5, "aaa"),
        Asset(2021, 6, "aaa"),
        Asset(2021, 5, "aa"),
        Asset(2021, 6, "aa"),
    ]
    games = [
        Asset(2021, 5, "aaa"),
        Asset(2021, 6, "aaa"),
        Asset(2021, 5, "aa"),
        Asset(2021, 6, "aa"),
    ]
    result = summarize_historical_source_coverage(pbp, games, levels=levels)

    assert result["complete_all_level_years"] == [2021]
    assert result["period_parity_all_level_years"] == [2021]
    assert result["latest_period_parity_all_level_year"] == 2021
    assert all(row["period_sets_match"] for row in result["year_level_cells"])
    assert all(row["common_period_coverage_ratio"] == 1.0 for row in result["year_level_cells"])


def test_historical_inventory_ignores_levels_outside_requested_surface() -> None:
    result = summarize_historical_source_coverage(
        [Asset(2024, 4, "aaa"), Asset(2024, 4, "a-")],
        [Asset(2024, 4, "aaa"), Asset(2024, 4, "a-")],
        levels=("aaa",),
    )
    assert result["complete_all_level_years"] == [2024]
    assert result["period_parity_all_level_years"] == [2024]
    assert {row["filename_level"] for row in result["year_level_cells"]} == {"aaa"}


def _mapping_rows() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "source_year": [2021, 2021, 2021, 2021],
            "filename_level": ["aaa", "aaa", "aa", "aa"],
            "game_id": [1, 2, 3, 4],
            "game_date": ["2021-05-01", "2021-05-02", "2021-05-01", "2021-05-02"],
            "game_type": ["R", "R", "R", "R"],
            "league_id": [112, 117, 109, 111],
            "player_id": [10, 11, 12, 13],
            "batting_PA": [4, 4, 4, 4],
            "source_asset": ["a.csv", "a.csv", "b.csv", "b.csv"],
        }
    )


def test_historical_league_mapping_accepts_disjoint_year_level_map() -> None:
    result = summarize_historical_league_mapping(
        _mapping_rows(), years=(2021,), levels=("aaa", "aa")
    )

    assert result["accepted_mapping_gate"] is True
    assert result["missing_year_level_cells"] == []
    assert result["cross_level_league_conflicts"] == []
    assert result["date_year_mismatch_count"] == 0
    assert result["player_game_league_identity_conflict_count"] == 0
    aaa = next(row for row in result["year_level_rows"] if row["filename_level"] == "aaa")
    assert aaa["league_ids"] == [112, 117]
    assert aaa["regular_game_count"] == 2
    assert aaa["min_game_date"] == "2021-05-01"
    assert aaa["max_game_date"] == "2021-05-02"


def test_historical_league_mapping_rejects_cross_level_and_identity_conflicts() -> None:
    bad = pl.concat(
        [
            _mapping_rows(),
            pl.DataFrame(
                {
                    "source_year": [2021, 2021],
                    "filename_level": ["aa", "aaa"],
                    "game_id": [5, 1],
                    "game_date": ["2021-05-03", "2021-05-01"],
                    "game_type": ["R", "R"],
                    "league_id": [112, 999],
                    "player_id": [14, 10],
                    "batting_PA": [4, 4],
                    "source_asset": ["b.csv", "c.csv"],
                }
            ),
        ],
        how="vertical",
    )
    result = summarize_historical_league_mapping(
        bad, years=(2021,), levels=("aaa", "aa")
    )

    assert result["accepted_mapping_gate"] is False
    assert result["player_game_league_identity_conflict_count"] == 1
    assert result["cross_level_league_conflicts"] == [
        {"year": 2021, "league_id": 112, "filename_levels": ["aa", "aaa"]}
    ]


def test_historical_league_mapping_rejects_missing_cell_and_wrong_year_date() -> None:
    rows = _mapping_rows().filter(pl.col("filename_level") == "aaa").with_columns(
        pl.when(pl.col("game_id") == 1)
        .then(pl.lit("2020-12-31"))
        .otherwise(pl.col("game_date"))
        .alias("game_date")
    )
    result = summarize_historical_league_mapping(
        rows, years=(2021,), levels=("aaa", "aa")
    )

    assert result["accepted_mapping_gate"] is False
    assert result["missing_year_level_cells"] == [{"year": 2021, "filename_level": "aa"}]
    assert result["date_year_mismatch_count"] == 1
