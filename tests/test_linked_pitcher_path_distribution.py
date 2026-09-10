import numpy as np

from scripts.audit_linked_pitcher_path_replay import (
    _arrival_path_distribution,
    _incumbent_workload_distribution,
    _incumbent_workload_rate_distribution,
)


def test_arrival_path_distribution_keeps_exact_zero_mass_and_timing() -> None:
    values, weights = _arrival_path_distribution(
        0.75,
        {1: np.array([1.0, 3.0]), 2: np.array([2.0, 4.0])},
        horizon=2,
    )
    assert np.isclose(weights.sum(), 1.0)
    assert values[0] == 0.0
    assert weights[0] == 0.25
    assert np.allclose(weights[1:3], 0.25)
    assert np.allclose(weights[3:], 0.125)


def test_zero_arrival_is_a_zero_point_distribution() -> None:
    values, weights = _arrival_path_distribution(
        0.0, {1: np.array([2.0])}, horizon=1
    )
    assert values.tolist() == [0.0]
    assert weights.tolist() == [1.0]


def test_incumbent_distribution_preserves_arrival_tier_and_annual_rates() -> None:
    row = {
        "four_year_arrival_probability": 1.0,
        "four_year_nested_meaningful_probability": 0.6,
        "four_year_nested_established_probability": 0.2,
    }
    paths = {
        "fringe": np.array([[10.0, 20.0]]),
        "meaningful_only": np.array([[30.0, 40.0]]),
        "established": np.array([[50.0, 60.0]]),
    }
    values, weights = _incumbent_workload_distribution(
        row, paths, {2022: 80.0, 2023: 160.0}, horizon=2
    )
    assert np.isclose(weights.sum(), 1.0)
    assert np.allclose(values[weights > 0], [5.0, 11.0, 17.0])
    assert np.allclose(weights[weights > 0], [0.4, 0.4, 0.2])

    uncertain_values, uncertain_weights = _incumbent_workload_rate_distribution(
        row,
        paths,
        {2022: 80.0, 2023: 160.0},
        {2022: (0.0, 0.0), 2023: (0.0, 0.0)},
        horizon=2,
        runs_per_win=10.0,
        normal_nodes=3,
    )
    assert np.isclose(uncertain_weights.sum(), 1.0)
    assert np.isclose(
        np.sum(uncertain_values * uncertain_weights), np.sum(values * weights)
    )
