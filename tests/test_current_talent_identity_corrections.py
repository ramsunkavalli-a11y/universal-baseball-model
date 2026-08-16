from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_identity_corrections import (
    IDENTITY_CORRECTION_POLICY,
    apply_historical_player_game_identity_corrections,
)


def _outcomes(*, pa: int = 4, include_target: bool = False) -> pl.DataFrame:
    rows = [
        {
            "game_id": 660171,
            "player_id": 703595,
            "league_id": 130,
            "game_date": date(2021, 9, 23),
            "batting_PA": pa,
            "batting_AB": 3,
            "batting_BB": 0,
            "batting_HBP": 0,
            "batting_SO": 2,
            "batting_SF": 0,
            "batting_SH": 1,
            "batting_CI": 0,
        },
        {
            "game_id": 660171,
            "player_id": 691553,
            "league_id": 130,
            "game_date": date(2021, 9, 23),
            "batting_PA": 4,
            "batting_AB": 4,
            "batting_BB": 0,
            "batting_HBP": 0,
            "batting_SO": 1,
            "batting_SF": 0,
            "batting_SH": 0,
            "batting_CI": 0,
        },
    ]
    if include_target:
        rows.append(
            {
                "game_id": 660171,
                "player_id": 682770,
                "league_id": 130,
                "game_date": date(2021, 9, 23),
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


def _controls(*, include_target: bool = False) -> pl.DataFrame:
    rows = [
        {"game_id": 660171, "player_id": 703595, "expected_contact_count": 1},
        {"game_id": 660171, "player_id": 691553, "expected_contact_count": 3},
    ]
    if include_target:
        rows.append(
            {"game_id": 660171, "player_id": 682770, "expected_contact_count": 1}
        )
    return pl.DataFrame(rows)


def test_certified_identity_correction_remaps_outcome_and_contact_control() -> None:
    outcomes, controls, evidence, metrics = apply_historical_player_game_identity_corrections(
        _outcomes(),
        _controls(),
        season=2021,
    )

    assert 703595 not in outcomes.get_column("player_id").to_list()
    assert 703595 not in controls.get_column("player_id").to_list()
    corrected = outcomes.filter(pl.col("player_id") == 682770).row(0, named=True)
    assert corrected["game_id"] == 660171
    assert corrected["batting_PA"] == 4
    assert corrected["batting_AB"] == 3
    assert corrected["batting_SO"] == 2
    assert corrected["batting_SH"] == 1
    assert evidence.height == 1
    assert evidence.row(0, named=True)["policy"] == IDENTITY_CORRECTION_POLICY
    assert metrics["applied_correction_count"] == 1


def test_certified_identity_correction_fails_closed_if_source_vector_drifts() -> None:
    with pytest.raises(ValueError, match="source outcome vector drifted"):
        apply_historical_player_game_identity_corrections(
            _outcomes(pa=5),
            _controls(),
            season=2021,
        )


def test_certified_identity_correction_fails_closed_on_target_collision() -> None:
    with pytest.raises(ValueError, match="existing target outcome"):
        apply_historical_player_game_identity_corrections(
            _outcomes(include_target=True),
            _controls(include_target=True),
            season=2021,
        )
