from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.authority_overlay import build_pitch_authority_view


def _pitch(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "game_pk": 1,
        "at_bat_index": 2,
        "pitch_number": 1,
        "source_batter_mlbam_id": 100,
        "source_pitcher_mlbam_id": 200,
        "batter_side": "L",
        "pitcher_hand": "R",
        "release_speed": 95.0,
    }
    row.update(overrides)
    return row


def _sequence(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "game_pk": 1,
        "at_bat_index": 2,
        "classification_status": "official_true_pa",
        "batter_mlbam_id": 100,
        "pitcher_mlbam_id": 200,
        "batter_side": "L",
        "pitcher_hand": "R",
    }
    row.update(overrides)
    return row


def test_official_matchup_supplies_working_identity_without_erasing_source() -> None:
    result = build_pitch_authority_view(
        pl.DataFrame([_pitch()]),
        pl.DataFrame([_sequence()]),
    ).to_dicts()[0]

    assert result["source_batter_mlbam_id"] == 100
    assert result["official_batter_mlbam_id"] == 100
    assert result["working_batter_mlbam_id"] == 100
    assert result["working_pitcher_mlbam_id"] == 200
    assert result["source_consensus_batter_side"] == "L"
    assert result["official_batter_side"] == "L"
    assert result["working_batter_side"] == "L"
    assert result["working_identity_authority"] == "official_matchup"
    assert result["working_handedness_authority"] == "official_matchup"
    assert result["batter_id_mismatch"] is False
    assert result["pitcher_hand_mismatch"] is False


def test_official_values_adjudicate_source_disagreement_but_preserve_mismatch() -> None:
    result = build_pitch_authority_view(
        pl.DataFrame(
            [
                _pitch(
                    source_batter_mlbam_id=999,
                    batter_side=None,
                    pitcher_hand="R",
                )
            ]
        ),
        pl.DataFrame(
            [
                _sequence(
                    batter_mlbam_id=100,
                    batter_side="L",
                    pitcher_hand="L",
                )
            ]
        ),
    ).to_dicts()[0]

    assert result["source_batter_mlbam_id"] == 999
    assert result["working_batter_mlbam_id"] == 100
    assert result["batter_id_mismatch"] is True
    assert result["source_consensus_batter_side"] is None
    assert result["working_batter_side"] == "L"
    assert result["source_consensus_pitcher_hand"] == "R"
    assert result["working_pitcher_hand"] == "L"
    assert result["pitcher_hand_mismatch"] is True
    assert result["working_handedness_authority"] == "official_matchup"


def test_source_only_fallback_is_explicit_when_official_sequence_missing() -> None:
    official = pl.DataFrame(
        schema={
            "game_pk": pl.Int64,
            "at_bat_index": pl.Int64,
            "classification_status": pl.String,
            "batter_mlbam_id": pl.Int64,
            "pitcher_mlbam_id": pl.Int64,
            "batter_side": pl.String,
            "pitcher_hand": pl.String,
        }
    )
    result = build_pitch_authority_view(
        pl.DataFrame([_pitch()]),
        official,
    ).to_dicts()[0]

    assert result["official_sequence_found"] is False
    assert result["working_batter_mlbam_id"] == 100
    assert result["working_pitcher_mlbam_id"] == 200
    assert result["working_batter_side"] == "L"
    assert result["working_pitcher_hand"] == "R"
    assert result["working_identity_authority"] == "reusable_source_only"
    assert result["working_handedness_authority"] == "reusable_source_only"


def test_overlay_accepts_official_non_pa_sequence_for_physical_pitch() -> None:
    result = build_pitch_authority_view(
        pl.DataFrame([_pitch()]),
        pl.DataFrame([_sequence(classification_status="official_non_pa")]),
    ).to_dicts()[0]

    assert result["official_sequence_found"] is True
    assert result["official_classification_status"] == "official_non_pa"
    assert result["working_identity_authority"] == "official_matchup"


def test_overlay_rejects_ambiguous_official_sequence_key() -> None:
    with pytest.raises(ValueError, match="official sequence view is not unique"):
        build_pitch_authority_view(
            pl.DataFrame([_pitch()]),
            pl.DataFrame([_sequence(), _sequence(batter_side="R")]),
        )
