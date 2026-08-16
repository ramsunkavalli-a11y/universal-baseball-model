from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.contact_identity_overlay import (
    apply_contact_identity_authority,
    apply_contact_identity_authority_by_sequence,
    contact_identity_residuals,
    exception_games_from_residuals,
    project_official_contact_authority,
    project_official_sequence_authority,
)


def _contacts() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 1, 2],
            "at_bat_index": [0, 1, 0],
            "pitch_number": [1, 7, 1],
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
            "pitch_number": [1, 7],
            "official_batter_id": [101, 102],
        }
    )


def _official_sequences_game_one() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 1],
            "at_bat_index": [0, 1],
            "official_batter_id": [101, 102],
        }
    )


def test_official_sequence_projection_uses_top_level_matchup_batter() -> None:
    pa = pl.DataFrame(
        {
            "game_pk": [1, 1, 1],
            "at_bat_number": [0, 1, 1],
            "batter_id": [101, 102, 102],
        }
    )
    authority = project_official_sequence_authority(pa)
    assert authority.to_dicts() == [
        {"game_pk": 1, "at_bat_index": 0, "official_batter_id": 101},
        {"game_pk": 1, "at_bat_index": 1, "official_batter_id": 102},
    ]


def test_official_sequence_projection_rejects_conflicting_matchup_batters() -> None:
    pa = pl.DataFrame(
        {
            "game_pk": [1, 1],
            "at_bat_number": [0, 0],
            "batter_id": [101, 999],
        }
    )
    with pytest.raises(ValueError, match="conflicting matchup batter"):
        project_official_sequence_authority(pa)


def test_official_contact_projection_uses_pa_matchup_batter_only_on_in_play_pitches() -> None:
    pa = pl.DataFrame(
        {
            "game_pk": [1, 1],
            "at_bat_number": [0, 1],
            "batter_id": [101, 102],
        }
    )
    pitch = pl.DataFrame(
        {
            "game_pk": [1, 1, 1],
            "at_bat_number": [0, 0, 1],
            "pitch_number": [1, 2, 1],
            "is_in_play": [False, True, True],
        }
    )
    authority = project_official_contact_authority(pa, pitch)
    assert authority.to_dicts() == [
        {
            "game_pk": 1,
            "at_bat_index": 0,
            "pitch_number": 2,
            "official_batter_id": 101,
        },
        {
            "game_pk": 1,
            "at_bat_index": 1,
            "pitch_number": 1,
            "official_batter_id": 102,
        },
    ]


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


def test_sequence_overlay_preserves_source_pitch_key_and_uses_matchup_batter() -> None:
    output, metrics = apply_contact_identity_authority_by_sequence(
        _contacts(), _player_games(), _official_sequences_game_one()
    )
    rows = {
        (row["game_pk"], row["at_bat_index"]): row for row in output.to_dicts()
    }
    assert rows[(1, 1)]["pitch_number"] == 7
    assert rows[(1, 1)]["source_batter_id"] == 999
    assert rows[(1, 1)]["batter_mlbam_id"] == 102
    assert rows[(1, 1)]["participant_authority"] == "official_exception_overlay"
    assert rows[(2, 0)]["batter_mlbam_id"] == 201
    assert rows[(2, 0)]["participant_authority"] == "source_default"
    assert metrics["authority_grain"] == "play_sequence"
    assert metrics["source_exception_sequence_count"] == 2
    assert metrics["covered_source_exception_sequence_count"] == 2
    assert metrics["missing_source_exception_sequence_count"] == 0


def test_sequence_overlay_allows_multiple_source_contacts_in_one_sequence() -> None:
    contacts = pl.concat(
        [
            _contacts(),
            pl.DataFrame(
                {
                    "game_pk": [1],
                    "at_bat_index": [1],
                    "pitch_number": [8],
                    "source_batter_id": [999],
                    "bb_type": ["fly_ball"],
                }
            ),
        ]
    )
    # Keep the player-game control aligned with the source residual pattern.
    player_games = _player_games().with_columns(
        pl.when((pl.col("game_id") == 1) & (pl.col("player_id") == 102))
        .then(pl.lit(2))
        .when((pl.col("game_id") == 1) & (pl.col("player_id") == 999))
        .then(pl.lit(0))
        .otherwise(pl.col("expected_contact_count"))
        .alias("expected_contact_count")
    )
    output, _ = apply_contact_identity_authority_by_sequence(
        contacts, player_games, _official_sequences_game_one()
    )
    sequence_rows = output.filter(
        (pl.col("game_pk") == 1) & (pl.col("at_bat_index") == 1)
    )
    assert sequence_rows.height == 2
    assert sequence_rows.get_column("batter_mlbam_id").to_list() == [102, 102]


def test_sequence_overlay_requires_every_source_contact_sequence_to_have_authority() -> None:
    incomplete = _official_sequences_game_one().head(1)
    with pytest.raises(ValueError, match="does not cover every reusable source contact sequence"):
        apply_contact_identity_authority_by_sequence(
            _contacts(), _player_games(), incomplete
        )


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
    assert metrics["authority_grain"] == "physical_contact_pitch"


def test_exact_physical_key_equality_is_required_for_strict_pitch_overlay() -> None:
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
