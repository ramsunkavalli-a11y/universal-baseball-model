import polars as pl
import pytest

from universal_baseball.next_season_transitions import build_next_season_transitions


def _hitting(rows=()):
    return pl.DataFrame(rows, schema={"season": pl.Int64, "player_id": pl.Int64, "batting_pa": pl.Int64})


def _pitching(rows=()):
    return pl.DataFrame(rows, schema={"season": pl.Int64, "player_id": pl.Int64, "pitching_bf": pl.Int64})


def test_missing_complete_target_is_observed_inactivity() -> None:
    result = build_next_season_transitions(
        _hitting([{"season": 2020, "player_id": 1, "batting_pa": 100}]),
        _pitching(), complete_seasons={2020, 2021}, source_seasons={2020},
    ).row(0, named=True)
    assert result["target_state"] == "inactive"
    assert result["returned_any"] is False
    assert result["target_batting_pa"] == 0


def test_unfinished_target_is_censored_not_zero() -> None:
    result = build_next_season_transitions(
        _hitting([{"season": 2021, "player_id": 1, "batting_pa": 100}]),
        _pitching(), complete_seasons={2021},
    ).row(0, named=True)
    assert result["target_state"] == "right_censored"
    assert result["returned_any"] is None
    assert result["target_batting_pa"] is None


def test_return_role_can_change_and_two_way_is_preserved() -> None:
    result = build_next_season_transitions(
        _hitting([
            {"season": 2020, "player_id": 1, "batting_pa": 50},
            {"season": 2021, "player_id": 2, "batting_pa": 40},
        ]),
        _pitching([
            {"season": 2020, "player_id": 2, "pitching_bf": 80},
            {"season": 2021, "player_id": 1, "pitching_bf": 90},
            {"season": 2021, "player_id": 2, "pitching_bf": 20},
        ]),
        complete_seasons={2020, 2021}, source_seasons={2020},
    )
    assert result.filter(pl.col("player_id") == 1).item(0, "target_state") == "pitcher_only"
    assert result.filter(pl.col("player_id") == 2).item(0, "target_state") == "both_workloads"


def test_duplicate_source_rows_are_aggregated_once() -> None:
    result = build_next_season_transitions(
        _hitting([
            {"season": 2020, "player_id": 1, "batting_pa": 40},
            {"season": 2020, "player_id": 1, "batting_pa": 60},
        ]),
        _pitching(), complete_seasons={2020, 2021}, source_seasons={2020},
    )
    assert result.height == 1
    assert result.item(0, "source_batting_pa") == 100


def test_complete_seasons_must_be_contiguous() -> None:
    with pytest.raises(ValueError, match="contiguous"):
        build_next_season_transitions(_hitting(), _pitching(), complete_seasons={2019, 2021})
