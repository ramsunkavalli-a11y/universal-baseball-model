import polars as pl
import pytest

from universal_baseball.prospect_mlb_progression import (
    build_post_arrival_progression_rows,
    progression_design,
)


def test_progression_rows_use_latest_snapshot_and_prior_season_workload() -> None:
    transitions = pl.DataFrame(
        {
            "player_id": [1, 1, 2, 4],
            "snapshot_year": [2018, 2019, 2019, 2018],
            "elapsed_year": [3, 2, 2, 2],
            "outcome_year": [2021, 2021, 2021, 2020],
            "from_state": [
                "FRINGE_MLB",
                "FRINGE_MLB",
                "MEANINGFUL_MLB",
                "FRINGE_MLB",
            ],
            "to_state": [
                "FRINGE_MLB",
                "MEANINGFUL_MLB",
                "ESTABLISHED_MLB",
                "MEANINGFUL_MLB",
            ],
            "age_years": [21.0, 22.0, 23.0, 24.0],
        }
    )
    workload = pl.DataFrame(
        {
            "season": [2020, 2020],
            "player_id": [2, 3],
            "mlb_workload": [300.0, 100.0],
        }
    )
    rows = build_post_arrival_progression_rows([transitions], workload)
    assert rows.height == 2
    player_one = rows.filter(pl.col("player_id") == 1)
    player_two = rows.filter(pl.col("player_id") == 2)
    assert player_one.item(0, "snapshot_year") == 2019
    assert player_one.item(0, "advanced") == 1
    assert player_two.item(0, "prior_workload_vs_active_mean") == 1.5
    assert player_two.item(0, "advanced") == 1


def test_progression_design_adds_activity_and_normalized_workload() -> None:
    frame = pl.DataFrame(
        {
            "transition_age_years": [25.0],
            "elapsed_year": [2],
            "prior_mlb_active": [1],
            "prior_workload_vs_active_mean": [1.0],
        }
    )
    assert progression_design(frame, feature_set="age_elapsed").shape == (1, 3)
    assert progression_design(
        frame, feature_set="age_elapsed_prior_workload"
    ).shape == (1, 5)


def test_pitcher_role_is_validated_and_added_to_progression_design() -> None:
    transitions = pl.DataFrame(
        {
            "player_id": [1],
            "snapshot_year": [2019],
            "elapsed_year": [2],
            "outcome_year": [2021],
            "from_state": ["FRINGE_MLB"],
            "to_state": ["MEANINGFUL_MLB"],
            "age_years": [23.0],
        }
    )
    workload = pl.DataFrame(
        {
            "season": [2020, 2020],
            "player_id": [1, 2],
            "mlb_workload": [100.0, 300.0],
            "pitching_games": [10, 20],
            "pitching_starts": [5, 0],
        }
    )
    rows = build_post_arrival_progression_rows([transitions], workload)
    assert rows.item(0, "prior_start_share") == 0.5
    assert rows.item(0, "prior_bf_per_game") == 10.0
    assert progression_design(
        rows, feature_set="age_elapsed_prior_workload_role"
    ).shape == (1, 7)

    with pytest.raises(ValueError, match="requires both"):
        build_post_arrival_progression_rows(
            [transitions], workload.drop("pitching_starts")
        )
