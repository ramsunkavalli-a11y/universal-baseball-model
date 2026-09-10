import numpy as np
import polars as pl
import pytest

from universal_baseball.prospect_career_state import (
    add_career_state,
    build_career_transition_rows,
    career_state_losses,
)


def test_add_career_state_is_exhaustive_and_ordered() -> None:
    frame = pl.DataFrame({
        "arrived_within_horizon": [0, 1, 1, 1],
        "meaningful_role_within_horizon": [0, 0, 1, 1],
        "established_role_within_horizon": [0, 0, 0, 1],
    })
    assert add_career_state(frame).get_column("career_state").to_list() == [
        "NO_MLB", "FRINGE_MLB", "MEANINGFUL_MLB", "ESTABLISHED_MLB"
    ]


def test_add_career_state_rejects_impossible_order() -> None:
    frame = pl.DataFrame({
        "arrived_within_horizon": [0],
        "meaningful_role_within_horizon": [1],
        "established_role_within_horizon": [0],
    })
    try:
        add_career_state(frame)
    except ValueError as error:
        assert "not ordered" in str(error)
    else:
        raise AssertionError("impossible outcome order should fail")


def test_career_state_losses_preserve_player_grain() -> None:
    frame = pl.DataFrame(
        {
            "player_id": [10, 20],
            "arrived_within_horizon": [0, 1],
            "meaningful_role_within_horizon": [0, 1],
            "established_role_within_horizon": [0, 0],
            "p_no_mlb": [0.8, 0.1],
            "p_fringe_mlb": [0.1, 0.2],
            "p_meaningful_mlb": [0.05, 0.6],
            "p_established_mlb": [0.05, 0.1],
        }
    )
    losses = career_state_losses(frame)
    assert losses.get_column("player_id").to_list() == [10, 20]
    assert losses.get_column("multiclass_log_loss").to_list() == pytest.approx(
        [-np.log(0.8), -np.log(0.6)]
    )


def test_build_career_transition_rows_tracks_monotone_path() -> None:
    def cohort(arrived: int, meaningful: int, established: int) -> pl.DataFrame:
        return pl.DataFrame({
            "player_id": [1], "arrived_within_horizon": [arrived],
            "meaningful_role_within_horizon": [meaningful],
            "established_role_within_horizon": [established],
        })
    rows = build_career_transition_rows(
        {1: cohort(1, 0, 0), 2: cohort(1, 1, 0), 3: cohort(1, 1, 1)},
        snapshot_year=2018,
    )
    assert rows.select("from_state", "to_state").rows() == [
        ("NO_MLB", "FRINGE_MLB"),
        ("FRINGE_MLB", "MEANINGFUL_MLB"),
        ("MEANINGFUL_MLB", "ESTABLISHED_MLB"),
    ]
