"""Score a fixed forecast; non-arrival is zero delivery, not zero talent."""
import numpy as np


def realized(counts, origin, target, values, unit, replacement):
    counts = np.asarray(counts, dtype=float)
    values = np.asarray(values, dtype=float)
    origin = np.asarray(origin, dtype=float)
    target = np.asarray(target, dtype=float)
    if counts.ndim != 2 or counts.shape[1] != 8 or values.shape != (8,):
        raise ValueError('Eight mutually exclusive events required')
    if not np.isfinite(counts).all() or (counts < 0).any():
        raise ValueError('Invalid outcome counts')
    for env in (origin, target):
        if env.shape != (8,) or (env < 0).any() or not np.isfinite(env).all() or not np.isclose(env.sum(), 1):
            raise ValueError('Invalid completed league reference')
    if not np.isfinite(values).all() or not np.isfinite(unit) or unit <= 0 or not np.isfinite(replacement) or replacement <= 0:
        raise ValueError('Invalid frozen units')
    pa = counts.sum(axis=1)
    active = pa > 0
    index = np.divide(counts @ values, pa, out=np.full(len(pa), np.nan), where=active)
    rate = (index - target @ values) * unit
    common = (index - origin @ values) * unit
    return dict(actual_pa=pa, actual_relative_rate=rate, actual_common_rate=common,
                actual_relative_value=np.where(active, pa * (rate / 600 + replacement), 0.),
                actual_common_value=np.where(active, pa * (common / 600 + replacement), 0.))


def error_metrics(pred, actual, weights=None):
    pred = np.asarray(pred, dtype=float)
    actual = np.asarray(actual, dtype=float)
    if pred.shape != actual.shape or not np.isfinite(pred).all() or not np.isfinite(actual).all():
        raise ValueError('Finite aligned outcomes required')
    if len(pred) == 0:
        return dict(n=0, rmse=None, mae=None, bias=None)
    w = np.ones(len(pred)) if weights is None else np.asarray(weights, dtype=float)
    if w.shape != pred.shape or not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError('Positive evaluation weights required')
    err = pred - actual
    return dict(n=len(pred), rmse=float(np.sqrt(np.average(err ** 2, weights=w))),
                mae=float(np.average(abs(err), weights=w)), bias=float(np.average(err, weights=w)))


def score(p, pa, rate, value, actual):
    p = np.asarray(p, dtype=float)
    observed_pa = actual['actual_pa']
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError('Invalid frozen probability')
    active = observed_pa > 0
    clipped = np.clip(p, 1e-15, 1 - 1e-15)
    return dict(players=len(p), actual_participants=int(active.sum()), expected_participants=float(p.sum()),
                brier=float(np.mean((p - active) ** 2)),
                log_loss=float(-np.mean(active * np.log(clipped) + (~active) * np.log1p(-clipped))),
                pa={**error_metrics(pa, observed_pa), 'predicted_total':float(np.sum(pa)), 'actual_total':float(observed_pa.sum())},
                conditional_rate_pa_weighted=error_metrics(np.asarray(rate)[active], actual['actual_relative_rate'][active], observed_pa[active]),
                primary_contribution={**error_metrics(value, actual['actual_relative_value']), 'predicted_total':float(np.sum(value)), 'actual_total':float(actual['actual_relative_value'].sum())},
                secondary_common_origin={**error_metrics(value, actual['actual_common_value']), 'predicted_total':float(np.sum(value)), 'actual_total':float(actual['actual_common_value'].sum())})
