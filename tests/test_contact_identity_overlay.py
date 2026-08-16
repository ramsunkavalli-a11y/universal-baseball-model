from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.contact_identity_overlay import (
    apply_contact_identity_authority,
    contact_identity_residuals,
    exception_games_from_residuals,
)


def _contacts() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 1, 2],
            "at_bat_index": [0, 1, 0],
            "pitch_number": [1, 1, 1],
            "source_batter_id": [101, 999, 201],
            "bb_type": ["ground_ball", "fly_ball", "line_drive"],
        }
    )


def _player_games() -> pl.DataFrame:
    # Game 1 source wrongly owns one contact to 999 instead of 102. Game 2 is clean.
    return pl.DataFrame(
        {
            "game_id": [1, 1, 1, 2],
            "player_id": [101, 102, 999, 201],
            "expected_contact_count": [1, 1, 0, 1],
        }
    )


def _official_game_one() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 1],
            "at_bat_index": [0, 1],
            "pitch_number": [1, 1],
            "official_batter_id": [101, 102],
        }
    )


def test_residuals_flag_only_games_with_player_attribution_difference() -> None:
    residuals = contact_identity_residuals(_contacts(), _player_games())
    assert exception_games_from_residuals(residuals) == [1]
    by_key = {
        (row["game_id"], row["player_id"]): row["contact_count_difference"]
        for row in residuals.to_dicts()
    }
    assert by_key[(1, 102)] == -1
    assert by_key[(1, 999)] == 1
    assert by_key[(2, 201)] == 0


def test_overlay_uses_official_authority_for_entire_flagged_game() -> None:
    output, metrics = apply_contact_identity_authority(
        _contacts(), _player_games(), _official_game_one()
    )
    rows = {
        (row["game_pk"], row["at_bat_index"]): row for row in output.to_dicts()
    }
    assert rows[(1, 0)]["batter_mlbam_id"] == 101
    assert rows[(1, 0)]["participant_authority"] == "official_exception_overlay"
    assert rows[(1, 1)]["source_batter_id"] == 999
    assert rows[(1, 1)]["batter_mlbam_id"] == 102
    assert rows[(1, 1)]["participant_authority"] == "official_exception_overlay"
    assert rows[(2, 0)]["batter_mlbam_id"] == 201
    assert rows[(2, 0)]["participant_authority"] == "source_default"

    assert metrics["exception_game_ids"] == [1]
    assert metrics["official_overlay_contact_count"] == 2
    assert metrics["source_default_contact_count"] == 1
    assert metrics["changed_batter_contact_count"] == 1


def test_exact_physical_key_equality_is_required_for_exception_game() -> None:
    incomplete = _official_game_one().head(1)
    with pytest.raises(ValueError, match="exact physical contact-key equality"):
        apply_contact_identity_authority(_contacts(), _player_games(), incomplete)


def test_official_authority_must_cover_exact_exception_game_set() -> None:
    extra = pl.concat(
        [
            _official_game_one(),
            pl.DataFrame(
                {
                    "game_pk": [2],
                    "at_bat_index": [0],
                    "pitch_number": [1],
                    "official_batter_id": [201],
                }
            ),
        ]
    )
    with pytest.raises(ValueError, match="game set"):
        apply_contact_identity_authority(_contacts(), _player_games(), extra)


def test_clean_games_need_no_official_rows() -> None:
    contacts = _contacts().filter(pl.col("game_pk") == 2)
    player_games = _player_games().filter(pl.col("game_id") == 2)
    empty_official = pl.DataFrame(
        schema={
            "game_pk": pl.Int64,
            "at_bat_index": pl.Int64,
            "pitch_number": pl.Int64,
            "official_batter_id": pl.Int64,
        }
    )
    output, metrics = apply_contact_identity_authority(
        contacts, player_games, empty_official
    )
    assert output.to_dicts()[0]["participant_authority"] == "source_default"
    assert metrics["exception_game_count"] == 0


def test_unresolved_player_game_control_is_not_silently_ignored() -> None:
    player_games = _player_games().with_columns(
        pl.when((pl.col("game_id") == 1) & (pl.col("player_id") == 102))
        .then(pl.lit(None, dtype=pl.Int64))
        .otherwise(pl.col("expected_contact_count"))
        .alias("expected_contact_count")
    )
    with pytest.raises(ValueError, match="unresolved expected contact"):
        contact_identity_residuals(_contacts(), player_games)
