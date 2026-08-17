from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_capability import (
    build_player_tracking_capability,
)


def _rows() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "game_date": date(2022, 6, 1),
                "game_pk": 1,
                "player_id": 10,
                "at_bat_number": 1,
                "pitch_number": 2,
                "launch_speed": 95.0,
                "launch_angle": 20.0,
                "sweet_spot": True,
                "season": 2022,
                "league_id": 117,
                "level_group": "AAA",
                "source_family": "MILB_SAVANT_TRACKED",
                "source_capability_tier": "MILB_SAVANT_TRACKED:2022:117:AAA",
            },
            {
                "game_date": date(2022, 6, 2),
                "game_pk": 2,
                "player_id": 10,
                "at_bat_number": 1,
                "pitch_number": 3,
                "launch_speed": 98.0,
                "launch_angle": 10.0,
                "sweet_spot": True,
                "season": 2022,
                "league_id": 117,
                "level_group": "AAA",
                "source_family": "MILB_SAVANT_TRACKED",
                "source_capability_tier": "MILB_SAVANT_TRACKED:2022:117:AAA",
            },
            {
                "game_date": date(2022, 6, 5),
                "game_pk": 3,
                "player_id": 11,
                "at_bat_number": 1,
                "pitch_number": 1,
                "launch_speed": 100.0,
                "launch_angle": 18.0,
                "sweet_spot": True,
                "season": 2022,
                "league_id": 1,
                "level_group": "MLB",
                "source_family": "MLB_SAVANT",
                "source_capability_tier": "MLB_SAVANT:2022:1:MLB",
            },
            {
                "game_date": date(2022, 6, 6),
                "game_pk": 4,
                "player_id": 12,
                "at_bat_number": 1,
                "pitch_number": 1,
                "launch_speed": 90.0,
                "launch_angle": 5.0,
                "sweet_spot": False,
                "season": 2022,
                "league_id": 112,
                "level_group": "AAA",
                "source_family": "MILB_SAVANT_TRACKED",
                "source_capability_tier": "MILB_SAVANT_TRACKED:2022:112:AAA",
            },
            {
                "game_date": date(2022, 6, 7),
                "game_pk": 5,
                "player_id": 12,
                "at_bat_number": 1,
                "pitch_number": 2,
                "launch_speed": 103.0,
                "launch_angle": 25.0,
                "sweet_spot": True,
                "season": 2022,
                "league_id": 1,
                "level_group": "MLB",
                "source_family": "MLB_SAVANT",
                "source_capability_tier": "MLB_SAVANT:2022:1:MLB",
            },
        ]
    )


def test_capability_preserves_observed_milb_tier_without_promoting_level() -> None:
    observed = build_player_tracking_capability(_rows(), cutoff=date(2022, 7, 1))
    row = observed.filter(pl.col("player_id") == 10).row(0, named=True)

    assert row["observed_model_bbe"] == 2
    assert row["observed_tracked_game_count"] == 2
    assert row["observed_mlb_bbe"] == 0
    assert row["observed_milb_bbe"] == 2
    assert row["source_family_group"] == "MILB_ONLY"
    assert row["source_capability_tier_count"] == 1
    assert row["observed_source_capability_tiers"] == "MILB_SAVANT_TRACKED:2022:117:AAA"
    assert row["observed_level_groups"] == "AAA"
    assert row["observed_league_ids"] == "117"


def test_capability_marks_cross_source_player_as_mixed() -> None:
    observed = build_player_tracking_capability(_rows(), cutoff=date(2022, 7, 1))
    row = observed.filter(pl.col("player_id") == 12).row(0, named=True)

    assert row["source_family_group"] == "MLB_MILB_MIXED"
    assert row["source_family_count"] == 2
    assert row["source_capability_tier_count"] == 2
    assert row["observed_mlb_bbe"] == 1
    assert row["observed_milb_bbe"] == 1
    assert row["observed_level_groups"] == "AAA|MLB"
    assert row["observed_league_ids"] == "1|112"


def test_capability_excludes_cutoff_and_future_bbe() -> None:
    rows = pl.concat(
        [
            _rows(),
            _rows().head(1).with_columns(
                pl.lit(date(2022, 7, 1)).alias("game_date"),
                pl.lit(100).alias("game_pk"),
            ),
        ]
    )
    observed = build_player_tracking_capability(rows, cutoff=date(2022, 7, 1))

    row = observed.filter(pl.col("player_id") == 10).row(0, named=True)
    assert row["observed_model_bbe"] == 2
    assert row["observed_tracked_game_count"] == 2


def test_capability_rejects_duplicate_canonical_bbe() -> None:
    duplicated = pl.concat([_rows(), _rows().head(1)])
    with pytest.raises(ValueError, match="canonical pitch-grain"):
        build_player_tracking_capability(duplicated, cutoff=date(2022, 7, 1))
