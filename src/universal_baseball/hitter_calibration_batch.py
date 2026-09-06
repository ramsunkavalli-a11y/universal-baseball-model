"""One bounded, chronology-checked multinomial calibration experiment."""

from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize

LEVELS = ("RK", "A", "A+", "AA", "AAA", "MLB", "UNKNOWN")


def softmax(logits):
    shifted = logits - logits.max(axis=1, keepdims=True)
    values = np.exp(shifted)
    return values / values.sum(axis=1, keepdims=True)


def validate_inputs(p, groups, counts=None):
    if p.ndim != 2 or p.shape[1] != 12 or not len(p):
        raise ValueError("Expected a nonempty twelve-outcome matrix")
    if (
        not np.isfinite(p).all()
        or (p <= 0).any()
        or not np.allclose(p.sum(axis=1), 1, atol=1e-10, rtol=0)
    ):
        raise ValueError("Invalid probability simplex")
    if (
        groups.shape != (len(p),)
        or not np.issubdtype(groups.dtype, np.integer)
        or (groups < 0).any()
        or (groups >= len(LEVELS)).any()
    ):
        raise ValueError("Invalid source-level groups")
    if counts is not None and (
        counts.shape != p.shape
        or not np.isfinite(counts).all()
        or (counts < 0).any()
        or (counts.sum(axis=1) <= 0).any()
    ):
        raise ValueError("Invalid outcome counts")


def objective(theta, logp, counts, groups, by_origin):
    k = logp.shape[1]
    t, a = theta[0], theta[1 : 1 + k]
    b = (
        theta[1 + k :].reshape(len(LEVELS), k)
        if by_origin
        else np.zeros((len(LEVELS), k))
    )
    logits = t * logp + a + b[groups]
    q = softmax(logits)
    n = counts.sum()
    loss = (
        -(counts * np.log(q)).sum() / n
        + 0.0005 * (a * a).sum()
        + 0.001 * (b * b).sum()
        + 0.01 * (t - 1) ** 2
    )
    residual = (counts.sum(axis=1, keepdims=True) * q - counts) / n
    grad = np.empty_like(theta)
    grad[0] = (residual * logp).sum() + 0.02 * (t - 1)
    grad[1 : 1 + k] = residual.sum(axis=0) + 0.001 * a
    if by_origin:
        gb = 0.002 * b
        np.add.at(gb, groups, residual)
        grad[1 + k :] = gb.ravel()
    return float(loss), grad


@dataclass
class Calibration:
    theta: np.ndarray
    by_origin: bool
    forecast_year: int
    training_years: tuple
    iterations: int

    def predict(self, p, groups):
        validate_inputs(p, groups)
        k = p.shape[1]
        logits = self.theta[0] * np.log(p) + self.theta[1 : 1 + k]
        if self.by_origin:
            logits += self.theta[1 + k :].reshape(len(LEVELS), k)[groups]
        return softmax(logits)


def fit_calibration(p, counts, groups, *, by_origin, forecast_year, training_years):
    if (
        forecast_year not in (2023, 2024)
        or not training_years
        or any(y < 2022 or y >= forecast_year for y in training_years)
    ):
        raise ValueError("Training outcomes must precede the disclosed forecast year")
    validate_inputs(p, groups, counts)
    theta = np.zeros(1 + 12 + (len(LEVELS) * 12 if by_origin else 0))
    theta[0] = 1
    result = minimize(
        objective,
        theta,
        args=(np.log(p), counts, groups, by_origin),
        jac=True,
        method="L-BFGS-B",
        bounds=[(0.5, 1.5)] + [(-1, 1)] * (len(theta) - 1),
        options={"maxiter": 1000, "ftol": 1e-12, "gtol": 1e-8},
    )
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"Calibration did not converge: {result.message}")
    return Calibration(
        result.x, by_origin, forecast_year, tuple(training_years), result.nit
    )


def cluster_rmse_interval(
    ids, pa, candidate_error, reference_error, *, replicates=1000, seed=260906
):
    unique, inverse = np.unique(ids, return_inverse=True)
    weights = np.bincount(inverse, weights=pa, minlength=len(unique))
    ce = np.bincount(inverse, weights=pa * candidate_error**2, minlength=len(unique))
    re = np.bincount(inverse, weights=pa * reference_error**2, minlength=len(unique))
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(replicates):
        sample = rng.integers(0, len(unique), len(unique))
        denominator = weights[sample].sum()
        deltas.append(
            np.sqrt(ce[sample].sum() / denominator)
            - np.sqrt(re[sample].sum() / denominator)
        )
    return {
        "lower": float(np.quantile(deltas, 0.025)),
        "upper": float(np.quantile(deltas, 0.975)),
        "unique_players": len(unique),
        "replicates": replicates,
        "seed": seed,
    }
