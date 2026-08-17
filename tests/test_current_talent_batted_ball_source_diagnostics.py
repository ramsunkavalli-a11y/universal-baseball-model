from datetime import date

import polars as pl
import pytest

from universal_baseball.current_talent_batted_ball_source_diagnostics import (
    build_tracking_completeness_diagnostics,
    project_savant_bbe_tracking_observations,
)


def _raw(rows: list[dict[str, object]]) -> pl.DataFrame:
    return pl.DataFrame(rows).with_columns(
        pl.col("game_pk").cast(pl.String),
        pl.col("batter").cast(pl.String),
        pl.col("at_bat_number").cast(pl.String),
        pl.col("pitch_number").cast(pl.String),
        pl.col("launch_speed").cast(pl.String),
        pl.col("launch_angle").cast(pl.String),
    )


def _row(
    *,
    game_date: str,
    game_pk: int,
    batter: int,
    at_bat_number: int,
    pitch_number: int,
    bb_type: str | None = "line_drive",
    description: str = "hit_into_play",
    launch_speed: float | None = 100.0,
    launch_angle: float | None = 20.0,
) -> dict[str, object]:
    return {
        "game_date": game_date,
        "game_pk": game_pk,
        "batter": batter,
        "at_bat_number": at_bat_number,
        "pitch_number": pitch_number,
        "bb_type": bb_type,
        "description": description,
        "launch_speed": launch_speed,
        "launch_angle": launch_angle,
    }


def test_tracking_diagnostics_report_bbe_like_completeness_and_game_counts() -> None:
    raw = _raw(
        [
            _row(
                game_date="2022-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=2,
                launch_speed=101.0,
                launch_angle=20.0,
            ),
            _row(
                game_date="2022-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=2,
                pitch_number=1,
                bb_type="ground_ball",
                launch_speed=None,
                launch_angle=None,
            ),
            _row(
                game_date="2022-06-15",
                game_pk=2,
                batter=10,
                at_bat_number=1,
                pitch_number=4,
                bb_type=None,
                launch_speed=94.0,
                launch_angle=12.0,
            ),
            _row(
                game_date="2022-07-01",
                game_pk=3,
                batter=10,
                at_bat_number=1,
                pitch_number=3,
                bb_type="fly_ball",
                launch_speed=110.0,
                launch_angle=28.0,
            ),
            _row(
                game_date="2022-06-10",
                game_pk=4,
                batter=11,
                at_bat_number=1,
                pitch_number=2,
                bb_type="ground_ball",
                launch_speed=None,
                launch_angle=5.0,
            ),
        ]
    )

    observations = project_savant_bbe_tracking_observations(raw)
    diagnostics = build_tracking_completeness_diagnostics(
        observations,
        cutoff=date(2022, 7, 1),
    )

    player_10 = diagnostics.filter(pl.col("player_id") == 10).row(0, named=True)
    assert player_10["bbe_like_observations"] == 3
    assert player_10["complete_ev_la_observations"] == 2
    assert player_10["complete_ev_la_share"] == pytest.approx(2 / 3)
    assert player_10["tracked_game_count"] == 2
    assert player_10["complete_tracked_game_count"] == 2
    assert player_10["ambiguous_multiple_complete_ev_la_observations"] == 0

    player_11 = diagnostics.filter(pl.col("player_id") == 11).row(0, named=True)
    assert player_11["bbe_like_observations"] == 1
    assert player_11["complete_ev_la_observations"] == 0
    assert player_11["complete_ev_la_share"] == pytest.approx(0.0)
    assert player_11["tracked_game_count"] == 1
    assert player_11["complete_tracked_game_count"] == 0


def test_tracking_observation_keeps_multiple_contacts_in_same_pa_separate() -> None:
    raw = _raw(
        [
            _row(
                game_date="2022-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=2,
                description="foul",
                launch_speed=75.0,
                launch_angle=-10.0,
            ),
            _row(
                game_date="2022-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=5,
                description="hit_into_play",
                launch_speed=99.0,
                launch_angle=19.0,
            ),
        ]
    )

    observations = project_savant_bbe_tracking_observations(raw)

    assert observations.height == 2
    assert observations.get_column("pitch_number").to_list() == [2, 5]
    assert observations.get_column("has_complete_ev_la").to_list() == [True, True]


def test_tracking_observation_surfaces_duplicate_raw_pitch_as_ambiguity() -> None:
    row = _row(
        game_date="2022-06-01",
        game_pk=1,
        batter=10,
        at_bat_number=1,
        pitch_number=4,
        launch_speed=101.0,
        launch_angle=20.0,
    )
    raw = _raw([row, {**row, "launch_speed": 99.0, "launch_angle": 19.0}])

    observations = project_savant_bbe_tracking_observations(raw)

    assert observations.height == 1
    observed = observations.row(0, named=True)
    assert observed["bbe_like_source_rows"] == 2
    assert observed["complete_ev_la_rows"] == 2
    assert observed["has_complete_ev_la"] is True
    assert observed["ambiguous_multiple_complete_ev_la"] is True

    diagnostics = build_tracking_completeness_diagnostics(
        observations,
        cutoff=date(2022, 7, 1),
    )
    assert diagnostics.row(0, named=True)["ambiguous_multiple_complete_ev_la_observations"] == 1


def test_tracking_completeness_excludes_cutoff_and_future_rows() -> None:
    raw = _raw(
        [
            _row(
                game_date="2022-06-30",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=1,
            ),
            _row(
                game_date="2022-07-01",
                game_pk=2,
                batter=10,
                at_bat_number=1,
                pitch_number=1,
                launch_speed=101.0,
            ),
            _row(
                game_date="2022-07-02",
                game_pk=3,
                batter=10,
                at_bat_number=1,
                pitch_number=1,
                launch_speed=102.0,
            ),
        ]
    )

    diagnostics = build_tracking_completeness_diagnostics(
        project_savant_bbe_tracking_observations(raw),
        cutoff=date(2022, 7, 1),
    )

    row = diagnostics.row(0, named=True)
    assert row["bbe_like_observations"] == 1
    assert row["complete_ev_la_observations"] == 1
    assert row["tracked_game_count"] == 1


def test_tracking_observation_rejects_conflicting_dates_at_pitch_key() -> None:
    raw = _raw(
        [
            _row(
                game_date="2022-06-01",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=3,
                launch_speed=101.0,
                launch_angle=20.0,
            ),
            _row(
                game_date="2022-06-02",
                game_pk=1,
                batter=10,
                at_bat_number=1,
                pitch_number=3,
                launch_speed=None,
                launch_angle=None,
            ),
        ]
    )

    with pytest.raises(ValueError, match="conflicting game dates"):
        project_savant_bbe_tracking_observations(raw)
