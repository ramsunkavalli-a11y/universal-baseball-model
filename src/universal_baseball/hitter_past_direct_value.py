"""Direct-rate residual on the same fixed past profile; no new source transform."""
import numpy as np
from scipy.special import softmax
from sklearn.linear_model import Ridge

from universal_baseball.mlb_event_logit import batting_rate


def baseline(clr, environment):
    clr, environment = np.asarray(clr, float), np.asarray(environment, float)
    if clr.ndim != 2 or clr.shape[1] != 8 or clr.shape != environment.shape:
        raise ValueError('Paired eight-event past profiles and references required')
    if not np.isfinite(clr).all() or not np.isfinite(environment).all() or (environment <= 0).any() or not np.allclose(environment.sum(1), 1):
        raise ValueError('Invalid past profile or environment')
    return batting_rate(softmax(np.log(environment) + clr, axis=1), environment)


def fit(x, actual_rate, past_rate, weights):
    x = np.asarray(x, float)
    a, b, w = [np.asarray(v, float) for v in [actual_rate, past_rate, weights]]
    if x.ndim != 2 or a.shape != b.shape or a.shape != w.shape or a.shape != (len(x),):
        raise ValueError('Paired active training rows required')
    if not all(np.isfinite(v).all() for v in [x, a, b, w]) or (w <= 0).any():
        raise ValueError('Invalid active training inputs')
    w = w * len(w) / w.sum()
    m = Ridge(alpha=100, solver='cholesky')
    m.fit(x, a - b, sample_weight=w)
    if not np.isfinite(m.coef_).all() or not np.isfinite(m.intercept_):
        raise ValueError('Nonfinite fitted rate')
    return m
