import polars as pl
import pytest

from universal_baseball.current_talent_mlb_evidence import (
    build_mlb_current_talent_player_game_evidence,
)


def _savant() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_date": ["2024-04-10"] * 4,
            "game_year": [2024] * 4,
            "game_pk": [100] * 4,
            "league_id": [103] * 4,
            "at_bat_index": [0, 1, 2, 3],
            "pitch_number": [4, 3, 2, 1],
            "batter_mlbam_id": [10] * 4,
            "batter_side": ["R"] * 4,
            "events": ["walk", "strikeout", "field_out", "catcher_interf"],
            "result_description": [
                "Batter walks.",
                "Batter strikes out.",
                "Batter grounds out.",
                "Catcher interference.",
            ],
            "bb_type": [None, None, "ground_ball", None],
            "hc_x": [None, None, 140.0, None],
            "hc_y": [None, None, 160.0, None],
            "is_plate_appearance_terminal": [True] * 4,
            "is_contact": [False, False, True, False],
        }
    )


def test_mlb_game_evidence_uses_true_pa_and_contact_profile() -> None:
    summary, profile, metrics = build_mlb_current_talent_player_game_evidence(_savant())

    assert summary.height == 1
    row = summary.row(0, named=True)
    assert row["batting_plate_appearances"] == 4
    assert row["core_profile_event_count"] == 3
    assert row["non_core_event_count"] == 1
    assert row["unknown_event_count"] == 0
    assert row["participant_authority_status"] == "savant_official"
    assert row["source_capability_tier"] == "mlb_savant_result_contact_profile_v1"

    assert profile.get_column("occurrence_count").sum() == 3
    assert {"BB_HBP", "K"}.issubset(set(profile.get_column("core_bin").to_list()))
    assert metrics["true_pa_terminal_count"] == 4
    assert metrics["contact_event_count"] == 1


def test_mlb_game_evidence_rejects_non_mlb_league() -> None:
    bad = _savant().with_columns(pl.lit(117).alias("league_id"))
    with pytest.raises(ValueError, match="non-MLB league"):
        build_mlb_current_talent_player_game_evidence(bad)


def test_mlb_game_evidence_rejects_duplicate_terminal_sequence() -> None:
    duplicate = pl.concat([_savant(), _savant().head(1)], how="vertical_relaxed")
    with pytest.raises(ValueError, match="duplicate true PA"):
        build_mlb_current_talent_player_game_evidence(duplicate)
