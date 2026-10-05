import numpy as np
from sklearn.linear_model import Ridge

from universal_baseball.hitter_past_direct_value import fit


def test_zero_offset_is_normalized_absolute_rate_learning():
    x = np.array([[0., 0.], [1., 0.], [0., 2.], [2., 2.]])
    y = np.array([-1., 2., 0., 4.]); w = np.array([1., 3., 2., 4.])
    m = fit(x, y, np.zeros(4), w)
    expected = Ridge(alpha=100, solver='cholesky').fit(x, y, sample_weight=w * 4 / w.sum())
    assert np.allclose(m.coef_, expected.coef_) and np.isclose(m.intercept_, expected.intercept_)
    assert np.allclose(m.predict(x), expected.predict(x))


def test_relearning_not_fixed_forecast_baseline_subtraction():
    x = np.arange(5.).reshape(-1, 1); y = np.array([0., 2., 1., 4., 3.]); b = np.array([0., 1., 2., 3., 4.])
    residual = fit(x, y, b, np.ones(5)); absolute = fit(x, y, np.zeros(5), np.ones(5))
    assert not np.allclose(absolute.predict(x), residual.predict(x))
    assert not np.allclose(absolute.predict(x), b + residual.predict(x))
