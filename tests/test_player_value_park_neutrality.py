import pytest

from universal_baseball.player_value_park_neutrality import (
    centered_rate_rows,
    harmonic_exposure,
    one_sided_permutation_p_value,
    weighted_slope,
)


def test_harmonic_exposure_requires_both_splits() -> None:
    assert harmonic_exposure(100, 100) == 100
    assert harmonic_exposure(100, 0) == 0
    with pytest.raises(ValueError):
        harmonic_exposure(-1, 10)


def test_weighted_slope_recovers_line_and_fitted_spread() -> None:
    result = weighted_slope([0, 1, 2], [1, 3, 5], [1, 1, 1])
    assert result.intercept == pytest.approx(1)
    assert result.slope == pytest.approx(2)
    assert result.fitted_weighted_sd == pytest.approx((8 / 3) ** 0.5)


def test_centered_rates_have_exposure_weighted_zero() -> None:
    rates = centered_rate_rows([(10, 100), (10, 200)])
    assert 100 * rates[0] + 200 * rates[1] == pytest.approx(0)


def test_permutation_p_value_is_deterministic_and_one_sided() -> None:
    x = list(range(8))
    y = list(range(8))
    weights = [1] * 8
    first = one_sided_permutation_p_value(x, y, weights, iterations=1_000, seed=7)
    second = one_sided_permutation_p_value(x, y, weights, iterations=1_000, seed=7)
    assert first == second
    assert first < 0.01
