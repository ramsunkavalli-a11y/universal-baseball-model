import polars as pl
import pytest

from universal_baseball.prospect_workload_uncertainty import (
    build_nested_workload_uncertainty,
)


def test_nested_workload_distribution_preserves_mean_and_nonarrival_mass() -> None:
    nested = pl.DataFrame(
        {
            "player_id": [1], "model_player_type": ["hitter"],
            "primary_position": ["SS"], "ordered_arrival_probability": [.5],
            "fringe_probability": [.2], "meaningful_only_probability": [.2],
            "established_probability": [.1], "starter_probability": [None],
            "reliever_probability": [None],
            "hitter_six_control_year_war_if_arrived": [6.0],
            "pitcher_six_control_year_war_if_arrived": [None],
            "three_tier_expected_six_year_war": [52.0 * 6.0 / 3300.0],
        }
    )
    paths = pl.DataFrame(
        {
            "player_type": ["hitter"] * 3,
            "outcome_tier_v2": ["fringe", "meaningful_only", "established"],
            "career_role": ["hitter"] * 3,
            "adjusted_total_workload": [10.0, 100.0, 300.0],
        }
    )
    result = build_nested_workload_uncertainty(
        nested, paths, minimum_role_players=1
    ).row(0, named=True)
    assert result["workload_war_mean"] == pytest.approx(
        nested.item(0, "three_tier_expected_six_year_war")
    )
    assert result["workload_war_p10"] == 0.0
    assert result["workload_war_p50"] == 0.0
