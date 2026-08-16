from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_official_outcomes import (
    apply_official_game_log_outcome_authority,
    project_official_hitting_game_log,
)


OUTCOMES = {
    "batting_PA": [4],
    "batting_AB": [4],
    "batting_BB": [0],
    "batting_HBP": [0],
    "batting_SO": [1],
    "batting_SF": [0],
    "batting_SH": [0],
    "batting_CI": [0],
}


def _source() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [10],
            "player_id": [100],
            "game_date": [date(2022, 5, 2)],
            "game_date_conflict": [True],
            "game_type": ["R"],
            "league_id": [122],
            **OUTCOMES,
            "source_asset_count": [2],
            "outcome_resolution": ["componentwise_dominance"],
        }
    )


def _official(*, pa: int = 4, ab: int = 4, so: int = 1) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_id": [10],
            "player_id": [100],
            "game_date": [date(2022, 5, 1)],
            "game_type": ["R"],
            "league_id": [122],
            "team_id": [1],
            "batting_PA": [pa],
            "batting_AB": [ab],
            "batting_BB": [0],
            "batting_HBP": [0],
            "batting_SO": [so],
            "batting_SF": [0],
            "batting_SH": [0],
            "batting_CI": [0],
        }
    )


def test_official_game_log_projection_maps_full_outcome_vector() -> None:
    payload = {
        "stats": [
            {
                "splits": [
                    {
                        "date": "2022-06-01",
                        "gameType": "R",
                        "game": {"gamePk": 55},
                        "league": {"id": 122},
                        "team": {"id": 9},
                        "sport": {"id": 14},
                        "stat": {
                            "plateAppearances": 5,
                            "atBats": 4,
                            "baseOnBalls": 1,
                            "hitByPitch": 0,
                            "strikeOuts": 2,
                            "sacFlies": 0,
                            "sacBunts": 0,
                            "catchersInterference": 0,
                        },
                    }
                ]
            }
        ]
    }
    row = project_official_hitting_game_log(payload, player_id=100, sport_id=14).row(
        0, named=True
    )
    assert row["game_id"] == 55
    assert row["game_date"] == date(2022, 6, 1)
    assert row["league_id"] == 122
    assert row["batting_PA"] == 5
    assert row["batting_BB"] == 1
    assert row["batting_SO"] == 2


def test_official_confirmation_does_not_mutate_source() -> None:
    corrected, evidence, metrics = apply_official_game_log_outcome_authority(
        _source(), _official(), player_id=100, league_id=122
    )
    row = corrected.row(0, named=True)
    assert row["batting_PA"] == 4
    assert row["outcome_resolution"] == "componentwise_dominance"
    assert row["outcome_authority"] == "player_game_source"
    assert evidence.is_empty()
    assert metrics["classification"] == "official_confirms_source"
    assert metrics["changed_field_count"] == 0


def test_official_overlay_replaces_vector_but_preserves_safe_source_date() -> None:
    corrected, evidence, metrics = apply_official_game_log_outcome_authority(
        _source(), _official(pa=5, ab=5, so=2), player_id=100, league_id=122
    )
    row = corrected.row(0, named=True)
    assert row["batting_PA"] == 5
    assert row["batting_AB"] == 5
    assert row["batting_SO"] == 2
    assert row["game_date"] == date(2022, 5, 2)  # latest-safe reusable source date retained
    assert row["game_date_conflict"] is True
    assert row["outcome_resolution"] == "official_game_log_overlay"
    assert row["outcome_authority"] == "official_game_log"
    assert set(evidence.get_column("field")) == {"batting_PA", "batting_AB", "batting_SO"}
    assert set(evidence.get_column("game_date_authority")) == {
        "player_game_safe_date_retained"
    }
    assert metrics["classification"] == "official_corrects_player_game_source"
    assert metrics["overlay_existing_game_count"] == 1


def test_official_only_positive_pa_game_is_inserted_explicitly() -> None:
    official = pl.concat(
        [
            _official(),
            pl.DataFrame(
                {
                    "game_id": [11],
                    "player_id": [100],
                    "game_date": [date(2022, 5, 3)],
                    "game_type": ["R"],
                    "league_id": [122],
                    "team_id": [1],
                    "batting_PA": [1],
                    "batting_AB": [1],
                    "batting_BB": [0],
                    "batting_HBP": [0],
                    "batting_SO": [1],
                    "batting_SF": [0],
                    "batting_SH": [0],
                    "batting_CI": [0],
                }
            ),
        ],
        how="vertical_relaxed",
    )
    corrected, evidence, metrics = apply_official_game_log_outcome_authority(
        _source(), official, player_id=100, league_id=122
    )
    inserted = corrected.filter(pl.col("game_id") == 11).row(0, named=True)
    assert inserted["batting_PA"] == 1
    assert inserted["batting_SO"] == 1
    assert inserted["source_asset_count"] == 0
    assert inserted["outcome_resolution"] == "official_game_log_insert"
    assert inserted["outcome_authority"] == "official_game_log"
    assert inserted["game_date"] == date(2022, 5, 3)
    assert metrics["insert_official_only_positive_pa_game_count"] == 1
    assert set(evidence.filter(pl.col("game_id") == 11).get_column("action")) == {
        "insert_official_only_positive_pa_game"
    }


def test_source_only_positive_pa_game_fails_closed() -> None:
    empty_other_game = _official().with_columns(pl.lit(99).alias("game_id"))
    with pytest.raises(ValueError, match="source has positive-PA games absent"):
        apply_official_game_log_outcome_authority(
            _source(), empty_other_game, player_id=100, league_id=122
        )


def test_official_only_zero_pa_game_is_not_inserted() -> None:
    zero = _official().with_columns(
        pl.lit(11).alias("game_id"),
        pl.lit(0).alias("batting_PA"),
        pl.lit(0).alias("batting_AB"),
        pl.lit(0).alias("batting_SO"),
    )
    official = pl.concat([_official(), zero], how="vertical_relaxed")
    corrected, _, metrics = apply_official_game_log_outcome_authority(
        _source(), official, player_id=100, league_id=122
    )
    assert corrected.filter(pl.col("game_id") == 11).is_empty()
    assert metrics["insert_official_only_positive_pa_game_count"] == 0
