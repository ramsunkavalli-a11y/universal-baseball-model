from datetime import date

import polars as pl

from universal_baseball.current_talent_source_residual_quarantine import (
    quarantine_single_source_only_exact_residual,
)


def _source(*, suspect_so: int = 0, extra_source_only: bool = False) -> pl.DataFrame:
    rows = [
        {
            "game_id": 10,
            "player_id": 100,
            "game_date": date(2024, 5, 1),
            "game_type": "R",
            "league_id": 118,
            "batting_PA": 4,
            "batting_AB": 3,
            "batting_BB": 1,
            "batting_HBP": 0,
            "batting_SO": 1,
            "batting_SF": 0,
            "batting_SH": 0,
            "batting_CI": 0,
        },
        {
            "game_id": 11,
            "player_id": 100,
            "game_date": date(2024, 5, 2),
            "game_type": "R",
            "league_id": 118,
            "batting_PA": 1,
            "batting_AB": 1,
            "batting_BB": 0,
            "batting_HBP": 0,
            "batting_SO": suspect_so,
            "batting_SF": 0,
            "batting_SH": 0,
            "batting_CI": 0,
        },
    ]
    if extra_source_only:
        rows.append(
            {
                "game_id": 12,
                "player_id": 100,
                "game_date": date(2024, 5, 3),
                "game_type": "R",
                "league_id": 118,
                "batting_PA": 1,
                "batting_AB": 1,
                "batting_BB": 0,
                "batting_HBP": 0,
                "batting_SO": 0,
                "batting_SF": 0,
                "batting_SH": 0,
                "batting_CI": 0,
            }
        )
    return pl.DataFrame(rows)


def _official(*, so: int = 1) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [10],
            "player_id": [100],
            "game_date": [date(2024, 5, 1)],
            "game_type": ["R"],
            "league_id": [118],
            "team_id": [1],
            "batting_PA": [4],
            "batting_AB": [3],
            "batting_BB": [1],
            "batting_HBP": [0],
            "batting_SO": [so],
            "batting_SF": [0],
            "batting_SH": [0],
            "batting_CI": [0],
        }
    )


def _comparison(*, pa: int = 1, bb: int = 0, hbp: int = 0, so: int = 0) -> dict:
    return {
        "plate_appearances_difference": pa,
        "walks_difference": bb,
        "hit_by_pitch_difference": hbp,
        "strikeouts_difference": so,
    }


def test_exact_single_source_only_residual_is_quarantined() -> None:
    corrected, metrics = quarantine_single_source_only_exact_residual(
        _source(), _official(), _comparison(), player_id=100, league_id=118
    )
    assert corrected.filter(pl.col("game_id") == 11).is_empty()
    assert metrics["applied"] is True
    assert metrics["quarantined_player_game_key"] == [11, 100]
    assert metrics["season_residual_exact"] is True
    assert metrics["official_full_vector_exact_after_removal"] is True


def test_strikeout_source_residual_can_be_quarantined_exactly() -> None:
    corrected, metrics = quarantine_single_source_only_exact_residual(
        _source(suspect_so=1),
        _official(),
        _comparison(so=1),
        player_id=100,
        league_id=118,
    )
    assert corrected.filter(pl.col("game_id") == 11).is_empty()
    assert metrics["applied"] is True


def test_season_residual_disagreement_fails_closed() -> None:
    corrected, metrics = quarantine_single_source_only_exact_residual(
        _source(), _official(), _comparison(pa=2), player_id=100, league_id=118
    )
    assert corrected.height == 2
    assert metrics["applied"] is False
    assert metrics["season_residual_exact"] is False


def test_full_official_vector_disagreement_fails_closed() -> None:
    corrected, metrics = quarantine_single_source_only_exact_residual(
        _source(), _official(so=2), _comparison(), player_id=100, league_id=118
    )
    assert corrected.height == 2
    assert metrics["applied"] is False
    assert metrics["official_full_vector_exact_after_removal"] is False


def test_multiple_source_only_games_are_never_auto_quarantined() -> None:
    corrected, metrics = quarantine_single_source_only_exact_residual(
        _source(extra_source_only=True),
        _official(),
        _comparison(),
        player_id=100,
        league_id=118,
    )
    assert corrected.height == 3
    assert metrics["applied"] is False
    assert metrics["reason"] == "requires_exactly_one_source_only_positive_pa_game"
