import polars as pl

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
