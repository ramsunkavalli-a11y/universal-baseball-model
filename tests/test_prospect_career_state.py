import polars as pl

from universal_baseball.prospect_career_state import (
    add_career_state,
    build_career_transition_rows,
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
