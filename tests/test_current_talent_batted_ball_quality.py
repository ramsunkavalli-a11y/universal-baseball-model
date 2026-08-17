from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_quality import (
    build_batted_ball_quality_features,
    project_complete_tracked_bbe,
)


def _raw(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows).with_columns(
        pl.col("game_pk").cast(pl.String),
        pl.col("batter").cast(pl.String),
        pl.col("at_bat_number").cast(pl.String),
        pl.col("launch_speed").cast(pl.String),
        pl.col("launch_angle").cast(pl.String),
    )


def test_project_complete_tracked_bbe_keeps_only_complete_measurements() -> None:
    raw = _raw(
        [
            {
                "game_date": "2023-06-01",
                "game_pk": 1,
                "batter": 10,
                "at_bat_number": 1,
                "launch_speed": 101.5,
                "launch_angle": 20.0,
            },
            {
                "game_date": "2023-06-01",
                "game_pk": 1,
                "batter": 10,
                "at_bat_number": 2,
                "launch_speed": 88.0,
                "launch_angle": None,
            },
            {
                "game_date": "2023-06-01",
                "game_pk": 1,
                "batter": 11,
                "at_bat_number": 1,
                "launch_speed": 90.0,
                "launch_angle": 40.0,
            },
        ]
    )

    observed = project_complete_tracked_bbe(raw)

    assert observed.height == 2
    assert observed.get_column("player_id").to_list() == [10, 11]
    assert observed.get_column("sweet_spot").to_list() == [True, False]


def test_project_complete_tracked_bbe_rejects_ambiguous_duplicate_contact() -> None:
    raw = _raw(
        [
            {
                "game_date": "2023-06-01",
                "game_pk": 1,
                "batter": 10,
                "at_bat_number": 1,
                "launch_speed": 100.0,
                "launch_angle": 20.0,
            },
            {
                "game_date": "2023-06-01",
                "game_pk": 1,
                "batter": 10,
                "at_bat_number": 1,
                "launch_speed": 99.0,
                "launch_angle": 19.0,
            },
        ]
    )

    with pytest.raises(ValueError, match="multiple complete EV\+LA rows"):
        project_complete_tracked_bbe(raw)


def test_features_exclude_cutoff_and_future_rows_and_apply_threshold() -> None:
    raw = _raw(
        [
            {
                "game_date": "2023-06-01",
                "game_pk": 1,
                "batter": 10,
                "at_bat_number": 1,
                "launch_speed": 100.0,
                "launch_angle": 20.0,
            },
            {
                "game_date": "2023-06-20",
                "game_pk": 2,
                "batter": 10,
                "at_bat_number": 1,
                "launch_speed": 90.0,
                "launch_angle": 0.0,
            },
            {
                "game_date": "2023-07-01",
                "game_pk": 3,
                "batter": 10,
                "at_bat_number": 1,
                "launch_speed": 120.0,
                "launch_angle": 25.0,
            },
            {
                "game_date": "2023-07-02",
                "game_pk": 4,
                "batter": 10,
                "at_bat_number": 1,
                "launch_speed": 120.0,
                "launch_angle": 25.0,
            },
        ]
    )
    tracked = project_complete_tracked_bbe(raw)

    features = build_batted_ball_quality_features(
        tracked,
        cutoff=date(2023, 7, 1),
        min_complete_tracked_bbe=2,
    )

    row = features.row(0, named=True)
    assert row["raw_complete_tracked_bbe"] == 2
    assert row["last_tracked_bbe_date"] == date(2023, 6, 20)
    assert row["tracked_bbe_eligible"] is True
    assert 90.0 < row["recency_weighted_mean_exit_velocity"] < 100.0
    assert 0.0 < row["recency_weighted_sweet_spot_share"] < 1.0


def test_features_use_raw_count_for_primary_eligibility() -> None:
    raw = _raw(
        [
            {
                "game_date": f"2023-06-{day:02d}",
                "game_pk": day,
                "batter": 10,
                "at_bat_number": 1,
                "launch_speed": 95.0,
                "launch_angle": 20.0,
            }
            for day in range(1, 21)
        ]
    )
    tracked = project_complete_tracked_bbe(raw)

    features = build_batted_ball_quality_features(tracked, cutoff=date(2023, 7, 1))

    row = features.row(0, named=True)
    assert row["raw_complete_tracked_bbe"] == 20
    assert row["effective_complete_tracked_bbe"] < 20.0
    assert row["tracked_bbe_eligible"] is True
