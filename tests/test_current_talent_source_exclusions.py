from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_source_exclusions import (
    CERTIFIED_GAME_EXCLUSION_POLICY,
    HISTORICAL_SOURCE_GAME_EXCLUSIONS,
    apply_certified_historical_game_exclusions,
)


def test_exact_certified_cancelled_game_is_excluded() -> None:
    frame = pl.DataFrame(
        {
            "game_id": [755829, 123],
            "game_date": ["2024-06-16", "2024-06-17"],
            "game_type": ["R", "R"],
        }
    )
    result, evidence = apply_certified_historical_game_exclusions(
        frame,
        season=2024,
        source_kind="player_game",
        game_id_column="game_id",
        game_date_column="game_date",
    )
    assert result.get_column("game_id").to_list() == [123]
    assert evidence[0]["game_id"] == 755829
    assert evidence[0]["policy"] == CERTIFIED_GAME_EXCLUSION_POLICY


def test_certified_exclusion_fails_on_date_drift() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": [774353],
            "game_date": ["2024-07-10"],
            "game_type": ["R"],
        }
    )
    with pytest.raises(ValueError, match="date drifted"):
        apply_certified_historical_game_exclusions(
            frame,
            season=2024,
            source_kind="pbp",
            game_id_column="game_pk",
            game_date_column="game_date",
        )


def test_other_seasons_are_unchanged() -> None:
    frame = pl.DataFrame(
        {"game_id": [755829], "game_date": ["2024-06-16"], "game_type": ["R"]}
    )
    result, evidence = apply_certified_historical_game_exclusions(
        frame,
        season=2023,
        source_kind="player_game",
        game_id_column="game_id",
        game_date_column="game_date",
    )
    assert result.equals(frame)
    assert evidence == []


def test_2024_registry_contains_every_audited_game() -> None:
    assert {row.game_id for row in HISTORICAL_SOURCE_GAME_EXCLUSIONS} == {
        754395,
        755829,
        774039,
        774292,
        774353,
        774458,
        774578,
    }
