from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_materialization import (
    combine_reconciled_tracked_bbe,
    materialize_reconciled_tracked_bbe,
)


def _raw() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "game_date": "2022-06-01",
                "game_pk": "1",
                "batter": "10",
                "at_bat_number": "1",
                "pitch_number": "2",
                "events": None,
                "type": "S",
                "des": "Batter hits a foul ball.",
                "description": "foul",
                "bb_type": None,
                "launch_speed": "70.0",
                "launch_angle": "-15.0",
            },
            {
                "game_date": "2022-06-01",
                "game_pk": "1",
                "batter": "10",
                "at_bat_number": "1",
                "pitch_number": "4",
                "events": "double",
                "type": "X",
                "des": "Batter doubles on a line drive to center field.",
                "description": "hit_into_play",
                "bb_type": "line_drive",
                "launch_speed": "101.0",
                "launch_angle": "18.0",
            },
        ]
    )


def _certified(*, level: str, league_id: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1],
            "player_id": [10],
            "season": [2022],
            "league_id": [league_id],
            "level_group": [level],
        }
    )


def test_raw_materialization_reuses_canonical_projection_and_environment_join() -> None:
    observed = materialize_reconciled_tracked_bbe(
        _raw(),
        _certified(level="AAA", league_id=117),
        source_family="MILB_SAVANT_TRACKED",
    )

    assert observed.height == 1
    row = observed.row(0, named=True)
    assert row["pitch_number"] == 4
    assert row["launch_speed"] == pytest.approx(101.0)
    assert row["level_group"] == "AAA"
    assert row["source_capability_tier"] == "MILB_SAVANT_TRACKED:2022:117:AAA"


def _reconciled(*, source: str, player_id: int, game_pk: int, league_id: int, level: str) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_date": [date(2022, 6, 1)],
            "game_pk": [game_pk],
            "player_id": [player_id],
            "at_bat_number": [1],
            "pitch_number": [3],
            "launch_speed": [98.0],
            "launch_angle": [20.0],
            "sweet_spot": [True],
            "season": [2022],
            "league_id": [league_id],
            "level_group": [level],
            "source_family": [source],
            "source_capability_tier": [f"{source}:2022:{league_id}:{level}"],
        }
    )


def test_combine_reconciled_tracking_preserves_source_families() -> None:
    milb = _reconciled(
        source="MILB_SAVANT_TRACKED",
        player_id=10,
        game_pk=1,
        league_id=117,
        level="AAA",
    )
    mlb = _reconciled(
        source="MLB_SAVANT",
        player_id=11,
        game_pk=2,
        league_id=1,
        level="MLB",
    )

    observed = combine_reconciled_tracked_bbe([milb, mlb], expected_season=2022)

    assert observed.height == 2
    assert set(observed.get_column("source_family")) == {
        "MLB_SAVANT",
        "MILB_SAVANT_TRACKED",
    }


def test_combine_reconciled_tracking_rejects_overlap_and_wrong_season() -> None:
    milb = _reconciled(
        source="MILB_SAVANT_TRACKED",
        player_id=10,
        game_pk=1,
        league_id=117,
        level="AAA",
    )
    duplicate_key = milb.with_columns(
        pl.lit("MLB_SAVANT").alias("source_family"),
        pl.lit("MLB_SAVANT:2022:1:MLB").alias("source_capability_tier"),
        pl.lit(1).alias("league_id"),
        pl.lit("MLB").alias("level_group"),
    )

    with pytest.raises(ValueError, match="overlaps"):
        combine_reconciled_tracked_bbe([milb, duplicate_key], expected_season=2022)

    with pytest.raises(ValueError, match="season mismatch"):
        combine_reconciled_tracked_bbe([milb], expected_season=2021)
