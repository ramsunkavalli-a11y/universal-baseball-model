"""Coherent expected event accounting; not a full season distribution."""
from types import SimpleNamespace
import numpy as np
from universal_baseball.hitter_compatible_value import UNIT, envelope
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.mlb_event_logit import VALUES


def contribution(counts, origin_index, replacement):
    x = np.asarray(counts, dtype=float)
    index, rep = np.asarray(origin_index, float), np.asarray(replacement, float)
    if x.ndim != 2 or x.shape[1] != 8 or index.shape != (len(x),) or rep.shape != (len(x),):
        raise ValueError('Paired eight-event means and origin references required')
    if not np.isfinite(x).all() or (x < 0).any() or not np.isfinite(index).all() or not np.isfinite(rep).all() or (rep <= 0).any():
        raise ValueError('Invalid event means or origin references')
    pa = x.sum(axis=1)
    value = (x @ VALUES - pa * index) * UNIT / 600 + pa * rep
    return pa, value


def count_forecast(raw, hard, origin_index, replacement):
    x = np.asarray(raw, dtype=float).copy()
    pa, _ = contribution(x, origin_index, replacement)
    scale = np.minimum(1., 800. / np.maximum(pa, 1e-300))
    x *= scale[:, None]
    unavailable = np.asarray(hard, bool)
    if unavailable.shape != (len(x),):
        raise ValueError('Availability mask mismatch')
    x[unavailable] = 0.
    pa, value = contribution(x, origin_index, replacement)
    low, high = envelope(pa, origin_index, replacement)
    if (pa > 800 + 1e-8).any() or (value < low - 1e-8).any() or (value > high + 1e-8).any():
        raise ValueError('Incoherent count forecast')
    return dict(counts=x, pa=pa, value=value, capped=(scale < 1), scale=scale)


def restricted_weights(full_weights, active):
    """Restrict the full cohort measure; do not rebalance active origins."""
    w = np.asarray(full_weights, float)[np.asarray(active, bool)].copy()
    if not len(w) or not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError('Invalid conditional weights')
    return w * len(w) / w.sum()


def poisson_trace(model, x, names):
    """Exact tree paths on log-mean scale, then the inverse log link."""
    proxy = SimpleNamespace(_baseline_prediction=model._baseline_prediction,
                            _predictors=model._predictors,
                            predict=lambda z: np.log(model.predict(z)))
    result = trace(proxy, x, names)
    result['log_mean'] = result.pop('raw_prediction')
    result['mean'] = float(np.exp(result['log_mean']))
    assert np.isclose(result['mean'], model.predict(np.asarray(x)[None, :])[0], atol=1e-8)
    result['interpretation'] += ' Effects are additive in log mean, not event counts; exponentiate the complete sum.'
    return result
