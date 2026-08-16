import polars as pl
import pytest

from universal_baseball.current_talent_milb_source import (
    classify_milb_current_talent_contacts,
    validate_expected_actual_leagues,
)


def test_expected_actual_leagues_match_exactly() -> None:
    frame = pl.DataFrame({"league_id": [112, 117, 112]})
    metrics = validate_expected_actual_leagues(
        frame,
        league_column="league_id",
        expected_league_ids=frozenset({112, 117}),
        label="historical AAA contacts",
    )
    assert metrics["exact_actual_league_coverage"] is True
    assert metrics["observed_league_ids"] == [112, 117]

    with pytest.raises(ValueError, match="actual-league coverage mismatch"):
        validate_expected_actual_leagues(
            frame,
            league_column="league_id",
            expected_league_ids=frozenset({112}),
            label="mismatch",
        )


def test_historical_contact_classification_derives_event_season() -> None:
    contacts = pl.DataFrame(
        {
            "game_date": ["2022-06-10"],
            "league_id": [112],
            "game_pk": [1],
            "at_bat_index": [2],
            "pitch_number": [4],
            "batter_mlbam_id": [100],
            "participant_authority": ["source_default"],
            "batter_side": ["R"],
            "bb_type": ["ground_ball"],
            "hc_x": [125.42],
            "hc_y": [100.0],
            "result_description": ["Batter grounds out to shortstop."],
        }
    )
    row = classify_milb_current_talent_contacts(contacts).to_dicts()[0]
    assert row["season"] == 2022
    assert row["trajectory_family"] == "GB"
    assert row["core_profile_eligible"] is True
    assert row["core_bin"] is not None
    assert row["result_description_authority"] == "source_certified_mirror"
