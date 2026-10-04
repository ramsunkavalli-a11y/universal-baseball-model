"""Exact accounting of a saved forecast, not causal error attribution."""
import numpy as np
from universal_baseball.hitter_compatible_value import UNIT


def miss_terms(expected_pa, predicted_rate, actual_pa, actual_relative_rate,
               replacement_rate, origin_index, target_index):
    arrays = [np.asarray(x, dtype=float) for x in
              (expected_pa, predicted_rate, actual_pa, actual_relative_rate,
               replacement_rate, origin_index, target_index)]
    if len({x.shape for x in arrays}) != 1 or arrays[0].ndim != 1:
        raise ValueError('Paired one-dimensional arrays required')
    if any(not np.isfinite(x).all() for x in arrays):
        raise ValueError('Finite diagnostic inputs required; inactive rates use a masked placeholder')
    phat, rhat, n, r, rep, origin, target = arrays
    if (phat < 0).any() or (n < 0).any() or (rep <= 0).any():
        raise ValueError('Invalid exposure or replacement reference')
    predicted = phat * (rhat / 600 + rep)
    relative_actual = n * (r / 600 + rep)
    opportunity = (n - phat) * (rhat / 600 + rep)
    hitting = n * (r - rhat) / 600
    environment = n * (target - origin) * UNIT / 600
    assert np.allclose(relative_actual - predicted, opportunity + hitting,
                       atol=1e-10, rtol=0)
    return dict(predicted=predicted, relative_actual=relative_actual,
                common_actual=relative_actual + environment,
                opportunity=opportunity, hitting=hitting, environment=environment)


def equal_origin_loss(predicted, actual, origins):
    predicted = np.asarray(predicted, float)
    actual = np.asarray(actual, float)
    origins = np.asarray(origins)
    if predicted.shape != actual.shape or predicted.shape != origins.shape or not len(origins):
        raise ValueError('Nonempty paired forecast/outcome/origin arrays required')
    if not np.isfinite(predicted).all() or not np.isfinite(actual).all():
        raise ValueError('Missing or invalid forecast/outcome')
    err = predicted - actual
    values = np.array([[np.mean(err[origins == y] ** 2),
                        np.mean(np.abs(err[origins == y])),
                        np.mean(err[origins == y])] for y in np.unique(origins)])
    mse, mae, bias = values.mean(axis=0)
    return dict(mse=float(mse), rmse=float(np.sqrt(mse)), mae=float(mae), bias=float(bias))
