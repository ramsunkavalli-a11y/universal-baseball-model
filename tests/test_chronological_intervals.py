import polars as pl

from universal_baseball.chronological_intervals import (
    add_player_stage,
    chronological_residual_intervals,
    interval_metrics,
)


def test_intervals_use_only_earlier_residuals() -> None:
    frame = pl.DataFrame(
        {
            "origin_year": [2021, 2021, 2022, 2022],
            "player_id": [1, 2, 3, 4],
            "actual_component_war": [0.0, 2.0, 10.0, 10.0],
            "prediction": [0.0, 0.0, 0.0, 0.0],
            "player_stage": ["all", "all", "all", "all"],
        }
    )
    intervals, calibration = chronological_residual_intervals(
        frame,
        prediction_column="prediction",
        confidence_levels=(0.5,),
        minimum_segment_rows=1,
    )
    assert intervals["lower_50"].to_list() == [0.5, 0.5]
    assert intervals["upper_50"].to_list() == [1.5, 1.5]
    assert calibration["calibration_rows"].to_list() == [2]
    assert interval_metrics(intervals, (0.5,))["50"]["empirical_coverage"] == 0.0


def test_player_stage_is_forecast_time_only() -> None:
    frame = pl.DataFrame(
        {
            "current_mlb_pa": [1, 0, 0],
            "current_highest_level": ["MLB", "AAA", "A"],
        }
    )
    assert add_player_stage(frame)["player_stage"].to_list() == [
        "current_mlb",
        "upper_minors",
        "lower_minors",
    ]
