import polars as pl
import pytest

from universal_baseball.current_talent_milb_source import (
    classify_milb_current_talent_contacts,
    derive_player_game_league_map,
    enrich_historical_pbp_league_id,
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


def _player_game_league_rows() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [1, 1, 2, 2],
            "league_id": [112, 112, 117, 117],
            "game_type": ["R", "R", "R", "R"],
        }
    )


def test_historical_pbp_can_fill_missing_league_from_unique_same_game_source() -> None:
    mapping, map_metrics = derive_player_game_league_map(_player_game_league_rows())
    assert mapping.to_dicts() == [
        {"game_pk": 1, "league_id": 112},
        {"game_pk": 2, "league_id": 117},
    ]
    assert map_metrics["league_id_authority"] == "player_game_same_game_structured"

    pbp = pl.DataFrame(
        {
            "game_pk": [1, 2],
            "game_type": ["R", "R"],
            "batter": [10, 11],
        }
    )
    enriched, metrics = enrich_historical_pbp_league_id(
        pbp,
        mapping,
        source_asset="2022_6_aaa_pbp.csv",
    )
    assert enriched.get_column("league_id").to_list() == [112, 117]
    assert metrics["native_league_id_column_present"] is False
    assert metrics["filled_league_id_row_count"] == 2
    assert metrics["league_id_authority"] == "player_game_same_game_structured"


def test_historical_pbp_native_league_must_agree_with_same_game_source() -> None:
    mapping, _ = derive_player_game_league_map(_player_game_league_rows())
    good = pl.DataFrame(
        {"game_pk": [1, 2], "game_type": ["R", "R"], "league_id": [112, 117]}
    )
    enriched, metrics = enrich_historical_pbp_league_id(
        good,
        mapping,
        source_asset="native.csv",
    )
    assert enriched.get_column("league_id").to_list() == [112, 117]
    assert metrics["league_id_authority"] == "pbp_native_validated_against_player_game_same_game"

    conflicting = good.with_columns(
        pl.when(pl.col("game_pk") == 2)
        .then(pl.lit(999))
        .otherwise(pl.col("league_id"))
        .alias("league_id")
    )
    with pytest.raises(ValueError, match="disagree"):
        enrich_historical_pbp_league_id(
            conflicting,
            mapping,
            source_asset="conflicting.csv",
        )


def test_player_game_league_map_rejects_conflicting_same_game_identity() -> None:
    rows = pl.DataFrame(
        {
            "game_id": [1, 1],
            "league_id": [112, 117],
            "game_type": ["R", "R"],
        }
    )
    with pytest.raises(ValueError, match="conflicting actual-league IDs"):
        derive_player_game_league_map(rows)
