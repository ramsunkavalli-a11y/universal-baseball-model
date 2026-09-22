import polars as pl

from universal_baseball.projection_ensemble import (
    chronological_greedy_equal_ensemble,
    greedy_equal_subset,
)


def test_greedy_subset_drops_harmful_member() -> None:
    frame = pl.DataFrame(
        {
            "actual": [0.0, 1.0, 2.0, 3.0],
            "good": [0.0, 1.0, 2.0, 3.0],
            "bad": [4.0, 4.0, 4.0, 4.0],
        }
    )

    selected = greedy_equal_subset(
        frame,
        ("good", "bad"),
        actual_column="actual",
        minimum_rmse_gain=0.0,
    )

    assert selected == ("good",)


def test_chronological_ensemble_never_uses_current_fold_for_selection() -> None:
    frame = pl.DataFrame(
        {
            "origin_year": [2021, 2021, 2022, 2022],
            "player_id": [1, 2, 1, 2],
            "actual_component_war": [0.0, 1.0, 0.0, 1.0],
            "first": [0.0, 1.0, 10.0, 10.0],
            "second": [2.0, 2.0, 0.0, 1.0],
        }
    )

    predictions, selections = chronological_greedy_equal_ensemble(
        frame,
        ("first", "second"),
        minimum_rmse_gain=0.0,
    )

    assert selections[0]["selected_members"] == ["first", "second"]
    assert selections[1]["selected_members"] == ["first"]
    assert predictions.filter(pl.col("origin_year") == 2022)[
        "prediction_chronology_pruned_equal"
    ].to_list() == [10.0, 10.0]
