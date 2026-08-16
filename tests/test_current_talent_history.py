from dataclasses import dataclass

from universal_baseball.current_talent_history import summarize_historical_source_coverage


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
