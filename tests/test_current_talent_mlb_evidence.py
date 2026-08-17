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
            "pitch_result_code": ["B", "S", "X", "B"],
            "bb_type": [None, None, "ground_ball", None],
            "hc_x": [None, None, 140.0, None],
            "hc_y": [None, None, 160.0, None],
            "is_plate_appearance_terminal": [True] * 4,
            "is_contact": [False, False, True, False],
        }
    )


def test_mlb_game_evidence_uses_true_pa_and_separate_contact_denominator() -> None:
    summary, profile, metrics = build_mlb_current_talent_player_game_evidence(_savant())

    assert summary.height == 1
    row = summary.row(0, named=True)
    assert row["batting_plate_appearances"] == 4
    assert row["expected_contact_count"] == 1
    assert row["observed_contact_count"] == 1
    assert row["contact_count_residual"] == 0
    assert row["core_profile_event_count"] == 3
    assert row["bunt_contact_count"] == 0
    assert row["foul_air_excluded_count"] == 0
    assert row["unknown_contact_count"] == 0
    assert row["special_noncontact_count"] == 1
    assert row["pa_accounting_residual"] == 0
    assert row["participant_authority_status"] == "savant_official"
    assert row["source_capability_tier"] == "mlb_savant_result_contact_profile_v2"

    assert profile.get_column("occurrence_count").sum() == 3
    assert {"BB_HBP", "K"}.issubset(set(profile.get_column("core_bin").to_list()))
    assert metrics["true_pa_terminal_count"] == 4
    assert metrics["contact_event_count"] == 1
    assert metrics["total_expected_contacts"] == 1
    assert metrics["total_observed_contacts"] == 1
    assert metrics["outcome_batter_reassignment_count"] == 0
    assert metrics["narrative_interference_error_count"] == 0
    assert metrics["evidence_denominator_policy"] == "separate_pa_expected_contact_observed_contact_v2"


def test_physical_contact_on_interference_pa_is_observed_but_not_expected_result_contact() -> None:
    # A catcher-interference PA can contain a real bat-ball contact even though
    # the official PA result belongs to the special non-contact result family.
    # ADR 024 must preserve that physical observation as a signed contact
    # residual rather than redefining the result-contact denominator.
    savant = _savant().with_columns(
        pl.when(pl.col("events") == "catcher_interf")
        .then(pl.lit(True))
        .otherwise(pl.col("is_contact"))
        .alias("is_contact")
    )

    summary, profile, metrics = build_mlb_current_talent_player_game_evidence(savant)
    row = summary.row(0, named=True)

    assert row["batting_plate_appearances"] == 4
    assert row["expected_contact_count"] == 1
    assert row["observed_contact_count"] == 2
    assert row["contact_count_residual"] == 1
    assert row["special_noncontact_count"] == 1
    assert row["unknown_contact_count"] == 1
    assert row["core_profile_event_count"] == 3
    assert row["pa_accounting_residual"] == 0
    assert profile.get_column("occurrence_count").sum() == 3
    assert metrics["total_expected_contacts"] == 1
    assert metrics["total_observed_contacts"] == 2
    assert metrics["total_contact_count_residual"] == 1


def _substitution_pa(*, strikes_before_substitute: int) -> pl.DataFrame:
    if strikes_before_substitute not in {1, 2}:
        raise ValueError("fixture supports one or two strikes")
    prior_codes = ["S"] * strikes_before_substitute + ["B"] * (3 - strikes_before_substitute)
    return pl.DataFrame(
        {
            "game_date": ["2021-07-05"] * 4,
            "game_year": [2021] * 4,
            "game_pk": [633487] * 4,
            "league_id": [103] * 4,
            "at_bat_index": [43] * 4,
            "pitch_number": [1, 2, 3, 4],
            "batter_mlbam_id": [10, 10, 10, 20],
            "batter_side": ["L", "L", "L", "L"],
            "events": [None, None, None, "strikeout"],
            "result_description": [None, None, None, "Original batter strikes out."],
            "pitch_result_code": [*prior_codes, "S"],
            "bb_type": [None] * 4,
            "hc_x": [None] * 4,
            "hc_y": [None] * 4,
            "is_plate_appearance_terminal": [False, False, False, True],
            "is_contact": [False] * 4,
        },
        schema_overrides={
            "events": pl.String,
            "result_description": pl.String,
            "bb_type": pl.String,
            "hc_x": pl.Float64,
            "hc_y": pl.Float64,
        },
    )


def test_two_strike_mid_pa_substitution_charges_strikeout_to_original_batter() -> None:
    summary, profile, metrics = build_mlb_current_talent_player_game_evidence(
        _substitution_pa(strikes_before_substitute=2)
    )

    assert summary.get_column("player_id").to_list() == [10]
    assert summary.get_column("batting_plate_appearances").to_list() == [1]
    assert profile.filter(pl.col("core_bin") == "K").get_column("player_id").to_list() == [10]
    assert metrics["outcome_batter_reassignment_count"] == 1


def test_one_strike_mid_pa_substitution_keeps_strikeout_with_substitute() -> None:
    summary, profile, metrics = build_mlb_current_talent_player_game_evidence(
        _substitution_pa(strikes_before_substitute=1)
    )

    assert summary.get_column("player_id").to_list() == [20]
    assert profile.filter(pl.col("core_bin") == "K").get_column("player_id").to_list() == [20]
    assert metrics["outcome_batter_reassignment_count"] == 0


def test_interference_error_narrative_is_special_outcome_but_preserves_contact() -> None:
    savant = pl.DataFrame(
        {
            "game_date": ["2021-04-28"],
            "game_year": [2021],
            "game_pk": [634317],
            "league_id": [104],
            "at_bat_index": [9],
            "pitch_number": [2],
            "batter_mlbam_id": [656371],
            "batter_side": ["L"],
            "events": ["field_error"],
            "result_description": [
                "Isan Diaz reaches on an interference error by pitcher Zack Godley."
            ],
            "pitch_result_code": ["X"],
            "bb_type": ["ground_ball"],
            "hc_x": [141.22],
            "hc_y": [179.67],
            "is_plate_appearance_terminal": [True],
            "is_contact": [True],
        }
    )

    summary, _profile, metrics = build_mlb_current_talent_player_game_evidence(savant)
    row = summary.row(0, named=True)
    assert row["batting_plate_appearances"] == 1
    assert row["special_noncontact_count"] == 1
    assert row["expected_contact_count"] == 0
    assert row["observed_contact_count"] == 1
    assert row["contact_count_residual"] == 1
    assert row["pa_accounting_residual"] == 0
    assert metrics["narrative_interference_error_count"] == 1


def test_mlb_game_evidence_rejects_non_mlb_league() -> None:
    bad = _savant().with_columns(pl.lit(117).alias("league_id"))
    with pytest.raises(ValueError, match="non-MLB league"):
        build_mlb_current_talent_player_game_evidence(bad)


def test_mlb_game_evidence_rejects_duplicate_terminal_sequence() -> None:
    duplicate = pl.concat([_savant(), _savant().head(1)], how="vertical_relaxed")
    with pytest.raises(ValueError, match="duplicate true PA"):
        build_mlb_current_talent_player_game_evidence(duplicate)
