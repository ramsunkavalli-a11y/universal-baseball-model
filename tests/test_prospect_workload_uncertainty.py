import polars as pl
import pytest

from universal_baseball.prospect_workload_uncertainty import (
    build_nested_component_uncertainty,
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


def test_component_uncertainty_preserves_point_mean_and_widens_range() -> None:
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
    rates = pl.DataFrame(
        {
            "player_id": [1, 1],
            "event_run_variance": [1.0, 1.0],
            "posterior_run_rate_variance": [.01, .01],
        }
    )
    workload = build_nested_workload_uncertainty(
        nested, paths, minimum_role_players=1
    ).row(0, named=True)
    result = build_nested_component_uncertainty(
        nested,
        paths,
        rates,
        rates.clear(),
        runs_per_win=10.0,
        minimum_role_players=1,
    ).row(0, named=True)
    assert result["component_workload_war_mean"] == pytest.approx(
        nested.item(0, "three_tier_expected_six_year_war"), abs=1e-12
    )
    assert result["component_workload_war_p10"] <= workload["workload_war_p10"]
    assert result["component_workload_war_p90"] > workload["workload_war_p90"]


def test_component_uncertainty_uses_pooled_pitcher_cell_when_role_is_sparse() -> None:
    nested = pl.DataFrame(
        {
            "player_id": [2], "model_player_type": ["pitcher"],
            "primary_position": ["P"], "ordered_arrival_probability": [1.0],
            "fringe_probability": [1.0], "meaningful_only_probability": [0.0],
            "established_probability": [0.0], "starter_probability": [1.0],
            "reliever_probability": [0.0],
            "hitter_six_control_year_war_if_arrived": [None],
            "pitcher_six_control_year_war_if_arrived": [6.0],
            "three_tier_expected_six_year_war": [1.0],
        }
    )
    paths = pl.DataFrame(
        {
            "player_type": ["pitcher", "pitcher"],
            "outcome_tier_v2": ["fringe", "fringe"],
            "career_role": ["starter", "reliever"],
            "adjusted_total_workload": [1000.0, 600.0],
        }
    )
    rates = pl.DataFrame(
        {
            "player_id": [2],
            "event_run_variance": [0.0],
            "posterior_run_rate_variance": [0.0],
        }
    )
    result = build_nested_component_uncertainty(
        nested,
        paths,
        rates.clear(),
        rates,
        runs_per_win=10.0,
        minimum_role_players=2,
    ).row(0, named=True)
    assert result["component_workload_war_mean"] == pytest.approx(1.0)
    assert result["sample_source"] == "fringe_starter_pooled"


def test_component_uncertainty_rejects_negative_variance() -> None:
    nested = pl.DataFrame(
        {
            "player_id": [1], "model_player_type": ["hitter"],
            "primary_position": ["SS"], "ordered_arrival_probability": [1.0],
            "fringe_probability": [1.0], "meaningful_only_probability": [0.0],
            "established_probability": [0.0], "starter_probability": [None],
            "reliever_probability": [None],
            "hitter_six_control_year_war_if_arrived": [1.0],
            "pitcher_six_control_year_war_if_arrived": [None],
            "three_tier_expected_six_year_war": [1.0 / 3300.0],
        }
    )
    paths = pl.DataFrame(
        {
            "player_type": ["hitter"], "outcome_tier_v2": ["fringe"],
            "career_role": ["hitter"], "adjusted_total_workload": [1.0],
        }
    )
    rates = pl.DataFrame(
        {
            "player_id": [1], "event_run_variance": [-1.0],
            "posterior_run_rate_variance": [0.0],
        }
    )
    with pytest.raises(ValueError, match="invalid hitter variance"):
        build_nested_component_uncertainty(
            nested, paths, rates, rates.clear(), runs_per_win=10.0,
            minimum_role_players=1,
        )
