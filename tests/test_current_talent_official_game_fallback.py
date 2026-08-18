from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_official_game_fallback import (
    augment_game_log_with_exact_pa_fallback,
    project_official_pa_outcome_vectors,
    source_only_positive_pa_games,
)


def _source(*, bb: int = 1) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [10],
            "player_id": [100],
            "game_date": [date(2024, 6, 12)],
            "game_type": ["R"],
            "league_id": [118],
            "batting_PA": [4],
            "batting_AB": [2],
            "batting_BB": [bb],
            "batting_HBP": [0],
            "batting_SO": [1],
            "batting_SF": [1],
            "batting_SH": [0],
            "batting_CI": [0],
        }
    )


def _game_log_without_source_game() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [99],
            "player_id": [100],
            "game_date": [date(2024, 6, 13)],
            "game_type": ["R"],
            "league_id": [118],
            "team_id": [1],
            "batting_PA": [4],
            "batting_AB": [4],
            "batting_BB": [0],
            "batting_HBP": [0],
            "batting_SO": [2],
            "batting_SF": [0],
            "batting_SH": [0],
            "batting_CI": [0],
        }
    )


def _official_pa() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": ["10", "10", "10", "10"],
            "batter_id": [100, 100, 100, 100],
            "event_type": ["single", "strikeout", "walk", "sac_fly"],
        }
    )


def test_project_official_pa_outcome_vector_uses_true_pa_stat_semantics() -> None:
    row = project_official_pa_outcome_vectors(_official_pa()).row(0, named=True)
    assert row == {
        "game_id": 10,
        "player_id": 100,
        "batting_PA": 4,
        "batting_AB": 2,
        "batting_BB": 1,
        "batting_HBP": 0,
        "batting_SO": 1,
        "batting_SF": 1,
        "batting_SH": 0,
        "batting_CI": 0,
    }


def test_source_only_game_detection_is_narrow_to_player_league_positive_pa() -> None:
    assert source_only_positive_pa_games(
        _source(),
        _game_log_without_source_game(),
        player_id=100,
        league_id=118,
    ) == [10]


def test_matching_exact_game_pbp_can_augment_game_log_without_changing_source() -> None:
    augmented, metrics = augment_game_log_with_exact_pa_fallback(
        _source(),
        _game_log_without_source_game(),
        _official_pa(),
        player_id=100,
        league_id=118,
    )
    fallback = augmented.filter(pl.col("game_id") == 10).row(0, named=True)
    assert fallback["batting_PA"] == 4
    assert fallback["batting_AB"] == 2
    assert fallback["batting_BB"] == 1
    assert fallback["game_date"] == date(2024, 6, 12)
    assert fallback["league_id"] == 118
    assert metrics["exact_game_pbp_confirmed_count"] == 1
    assert metrics["confirmed_game_ids"] == [10]
    assert metrics["source_values_changed"] is False


def test_missing_exact_game_pbp_still_fails_closed() -> None:
    other = _official_pa().with_columns(pl.lit("11").alias("game_pk"))
    with pytest.raises(ValueError, match="lack exact-game official PA evidence"):
        augment_game_log_with_exact_pa_fallback(
            _source(),
            _game_log_without_source_game(),
            other,
            player_id=100,
            league_id=118,
        )


def test_disagreeing_exact_game_pbp_still_fails_closed() -> None:
    with pytest.raises(ValueError, match="disagrees with exact-game official PA vector"):
        augment_game_log_with_exact_pa_fallback(
            _source(bb=0),
            _game_log_without_source_game(),
            _official_pa(),
            player_id=100,
            league_id=118,
        )


def test_unknown_or_non_pa_event_cannot_enter_fallback_vector() -> None:
    bad = _official_pa().with_columns(
        pl.when(pl.arange(0, pl.len()) == 0)
        .then(pl.lit("pickoff_1b"))
        .otherwise(pl.col("event_type"))
        .alias("event_type")
    )
    with pytest.raises(ValueError, match="non-PA/unknown"):
        project_official_pa_outcome_vectors(bad)
