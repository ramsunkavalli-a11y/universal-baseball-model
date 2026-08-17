from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_reconciliation import (
    reconcile_tracked_bbe_to_certified_environment,
)


def _tracked() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_date": [date(2022, 6, 1), date(2022, 6, 1)],
            "game_pk": [100, 100],
            "player_id": [10, 10],
            "at_bat_number": [1, 2],
            "pitch_number": [4, 3],
            "launch_speed": [95.0, 101.0],
            "launch_angle": [10.0, 25.0],
            "sweet_spot": [True, True],
        }
    )


def _certified(*, level: str = "AAA") -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [100],
            "player_id": [10],
            "season": [2022],
            "league_id": [117],
            "level_group": [level],
        }
    )


def test_minor_tracking_is_labeled_from_observed_certified_game_environment() -> None:
    observed = reconcile_tracked_bbe_to_certified_environment(
        _tracked(),
        _certified(),
        source_family="MILB_SAVANT_TRACKED",
    )

    assert observed.height == 2
    assert observed.get_column("pitch_number").to_list() == [4, 3]
    assert set(observed.get_column("source_family")) == {"MILB_SAVANT_TRACKED"}
    assert set(observed.get_column("source_capability_tier")) == {
        "MILB_SAVANT_TRACKED:2022:117:AAA"
    }
    assert set(observed.get_column("level_group")) == {"AAA"}


def test_duplicate_identical_certified_rows_collapse_but_conflicting_environments_fail() -> None:
    duplicate_same = pl.concat([_certified(), _certified()])
    observed = reconcile_tracked_bbe_to_certified_environment(
        _tracked(),
        duplicate_same,
        source_family="MILB_SAVANT_TRACKED",
    )
    assert observed.height == 2

    conflicting = pl.concat(
        [
            _certified(),
            _certified().with_columns(
                pl.lit(118).alias("league_id"),
                pl.lit("AA").alias("level_group"),
            ),
        ]
    )
    with pytest.raises(ValueError, match="ambiguous game/player environment"):
        reconcile_tracked_bbe_to_certified_environment(
            _tracked(),
            conflicting,
            source_family="MILB_SAVANT_TRACKED",
        )


def test_duplicate_pitch_grain_tracking_fails_closed() -> None:
    duplicated = pl.concat([_tracked(), _tracked().head(1)])
    with pytest.raises(ValueError, match="pitch-grain"):
        reconcile_tracked_bbe_to_certified_environment(
            duplicated,
            _certified(),
            source_family="MILB_SAVANT_TRACKED",
        )


def test_unmatched_complete_tracking_fails_closed() -> None:
    with pytest.raises(ValueError, match="unmatched rows"):
        reconcile_tracked_bbe_to_certified_environment(
            _tracked(),
            _certified().with_columns(pl.lit(999).alias("player_id")),
            source_family="MILB_SAVANT_TRACKED",
        )


def test_source_family_cannot_cross_mlb_milb_boundary() -> None:
    with pytest.raises(ValueError, match="non-MLB"):
        reconcile_tracked_bbe_to_certified_environment(
            _tracked(),
            _certified(level="AAA"),
            source_family="MLB_SAVANT",
        )

    with pytest.raises(ValueError, match="MLB environment"):
        reconcile_tracked_bbe_to_certified_environment(
            _tracked(),
            _certified(level="MLB"),
            source_family="MILB_SAVANT_TRACKED",
        )
