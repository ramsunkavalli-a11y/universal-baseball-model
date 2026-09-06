"""Fixed MLB-conditional value calibration with coherent terminal probabilities."""

import numpy as np
from scipy.optimize import minimize
from universal_baseball.hitter_calibration_batch import softmax, validate_inputs
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_WEIGHTS
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES

WEIGHTS = np.array([NEUTRAL_WOBA_WEIGHTS[o] for o in HITTER_TALENT_OUTCOMES])
CENTER = 0.3188


def affine_objective(theta, x, y, w):
    a, b = theta
    error = a + b * x - y
    return float(w @ (error * error) + 0.01 * a * a + 0.0001 * (b - 1) ** 2), np.array(
        [2 * w @ error + 0.02 * a, 2 * w @ (error * x) + 0.0002 * (b - 1)]
    )


def fit_value(p, counts, minor, *, forecast_year, training_years):
    if (
        forecast_year not in (2023, 2024)
        or not training_years
        or any(y < 2022 or y >= forecast_year for y in training_years)
    ):
        raise ValueError("Training outcomes must precede forecast")
    validate_inputs(p, minor.astype(int), counts)
    if minor.dtype != bool:
        raise ValueError("Expected binary minor-origin indicator")
    pa = counts.sum(axis=1)
    x = p @ WEIGHTS - CENTER
    y = counts @ WEIGHTS / pa - CENTER
    parameters = []
    for group in (False, True):
        mask = minor == group
        if not mask.any():
            parameters.append([0.0, 1.0])
            continue
        w = pa[mask] / pa[mask].sum()
        result = minimize(
            affine_objective,
            np.array([0.0, 1.0]),
            args=(x[mask], y[mask], w),
            jac=True,
            method="L-BFGS-B",
            bounds=[(-0.05, 0.05), (0.25, 1.75)],
            options={"maxiter": 1000, "ftol": 1e-12, "gtol": 1e-8},
        )
        if not result.success:
            raise RuntimeError(f"Value calibration failed: {result.message}")
        parameters.append(result.x.tolist())
    return np.array(parameters)


def tilt_to_value(p, target):
    validate_inputs(p, np.zeros(len(p), dtype=int))
    if target.shape != (len(p),) or not np.isfinite(target).all():
        raise ValueError("Invalid target value")
    logp = np.log(p)
    lo = np.full(len(p), -40.0)
    hi = np.full(len(p), 40.0)
    for _ in range(64):
        mid = (lo + hi) / 2
        q = softmax(logp + mid[:, None] * WEIGHTS)
        below = q @ WEIGHTS < target
        lo = np.where(below, mid, lo)
        hi = np.where(below, hi, mid)
    q = softmax(logp + ((lo + hi) / 2)[:, None] * WEIGHTS)
    if np.max(np.abs(q @ WEIGHTS - target)) > 1e-9:
        raise ValueError("Desired wOBA not reached")
    return q


def predict_value(p, minor, parameters):
    selected = parameters[minor.astype(int)]
    desired = CENTER + selected[:, 0] + selected[:, 1] * (p @ WEIGHTS - CENTER)
    clipped = np.clip(desired, 0.10, 0.60)
    return tilt_to_value(p, clipped), int(np.count_nonzero(clipped != desired))
