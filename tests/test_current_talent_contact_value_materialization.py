from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.current_talent_contact_value_materialization import (
    materialize_contact_value_target_contacts,
)


def _authorized() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_date": ["2021-06-01", "2021-06-01", "2021-06-02"],
            "game_pk": [10, 10, 11],
            "at_bat_index": [4, 4, 7],
            "pitch_number": [2, 3, 1],
        }
    )


def _profile() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [10, 10, 11],
            "at_bat_index": [4, 4, 7],
            "pitch_number": [2, 3, 1],
            "league_id": [112, 112, 117],
            "batter_mlbam_id": [100, 100, 200],
            "participant_authority": ["source_default"] * 3,
            "core_bin": ["PULL_GB", "CENTER_LD", None],
            "core_profile_eligible": [True, True, False],
        }
    )


def _terminal() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [10, 11],
            "at_bat_index": [4, 7],
            "terminal_pitch_number": [3, 1],
            "terminal_outcome_group": ["1B", "OUT"],
            "terminal_outcome_status": [
                "supported_narrative_fallback",
                "supported_narrative_fallback",
            ],
        }
    )


def test_materialization_keeps_only_terminal_supported_core_contact() -> None:
    target, metrics = materialize_contact_value_target_contacts(
        _authorized(), _profile(), _terminal()
    )
    assert target.height == 1
    row = target.row(0, named=True)
    assert row["event_date"].isoformat() == "2021-06-01"
    assert row["game_pk"] == 10
    assert row["pitch_number"] == 3
    assert row["player_id"] == 100
    assert row["level_group"] == "AAA"
    assert row["contact_bin"] == "CENTER_LD"
    assert row["terminal_outcome_group"] == "1B"
    assert metrics["physical_contact_count"] == 3
    assert metrics["terminal_physical_contact_count"] == 2
    assert metrics["core_terminal_contact_count"] == 1
    assert metrics["supported_target_contact_count"] == 1
    assert metrics["model_scoring"] is False
    assert metrics["accessed_2023"] is False


def test_materialization_excludes_unsupported_terminal_group() -> None:
    terminal = _terminal().with_columns(
        pl.when(pl.col("game_pk") == 10)
        .then(pl.lit(None, dtype=pl.String))
        .otherwise(pl.col("terminal_outcome_group"))
        .alias("terminal_outcome_group")
    )
    target, metrics = materialize_contact_value_target_contacts(
        _authorized(), _profile(), terminal
    )
    assert target.is_empty()
    assert metrics["unsupported_terminal_group_count"] == 1


def test_materialization_rejects_duplicate_physical_keys() -> None:
    duplicated = pl.concat([_authorized(), _authorized().head(1)])
    with pytest.raises(ValueError, match="duplicate physical contact keys"):
        materialize_contact_value_target_contacts(duplicated, _profile(), _terminal())


def test_materialization_rejects_uncertified_league() -> None:
    profile = _profile().with_columns(
        pl.when(pl.col("game_pk") == 10)
        .then(pl.lit(999))
        .otherwise(pl.col("league_id"))
        .alias("league_id")
    )
    with pytest.raises(ValueError, match="uncertified league IDs"):
        materialize_contact_value_target_contacts(_authorized(), profile, _terminal())
