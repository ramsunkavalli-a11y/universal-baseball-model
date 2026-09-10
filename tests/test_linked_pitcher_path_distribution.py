import numpy as np

from scripts.audit_linked_pitcher_path_replay import _arrival_path_distribution


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
