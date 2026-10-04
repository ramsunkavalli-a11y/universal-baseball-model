"""Mean-preserving offense mixtures; Normal batting errors are approximate."""

import numpy as np
from scipy.optimize import minimize
from scipy.special import ndtr

FLOOR = 1e-8
ALPHAS = np.array([.1, .5, .9])


def fit_rate_variances(residual, pa, weights):
    r, n, w = map(lambda x: np.asarray(x, dtype=float), (residual, pa, weights))
    if not (r.shape == n.shape == w.shape) or len(r) == 0:
        raise ValueError('Paired nonempty calibration arrays required')
    if not all(np.isfinite(x).all() for x in (r, n, w)) or (n <= 0).any() or (w <= 0).any():
        raise ValueError('Invalid rate calibration')
    w = w / w.sum()
    constant = max(float(w @ (r*r)), FLOOR)
    design = np.column_stack((np.ones(len(n)), 600/n))

    def objective(theta):
        raw = design @ theta
        var = np.maximum(raw, FLOOR)
        loss = .5 * float(w @ (np.log(var) + r*r/var))
        gradient = design.T @ (.5*w*(1/var-r*r/var**2)*(raw > FLOOR))
        return loss, gradient

    starts = [[constant, 0], [constant/2, constant/2],
              [0, constant/float(w @ (600/n))]]
    options = []
    for start in starts:
        fit = minimize(objective, start, jac=True, method='L-BFGS-B',
                       bounds=[(0, 10000)]*2,
                       options={'ftol': 1e-12, 'gtol': 1e-8, 'maxiter': 2000})
        if not np.isfinite(fit.fun) or not fit.success:
            raise ValueError(f'Variance optimization failed: {fit.message}')
        options.append(dict(a=float(fit.x[0]), b=float(fit.x[1]),
                            objective=float(fit.fun), iterations=int(fit.nit)))
    best = min(options, key=lambda x: x['objective'])
    return dict(constant_variance=constant, sample_dependent=best,
                optimizer_checks=options, residual_bias=float(w @ r),
                minimum_pa=float(n.min()), maximum_pa=float(n.max()),
                variance_floor=FLOOR)


def rate_variance(pa, a, b):
    pa = np.asarray(pa, dtype=float)
    if (pa <= 0).any() or a < 0 or b < 0:
        raise ValueError('Positive PA and nonnegative variances required')
    return np.maximum(a+b*600/pa, FLOOR)


def cdf_normal_mixture(x, pmf, means, sd, *, left=False):
    """CDF or left limit, retaining the nonarrival atom separately."""
    x = np.asarray(x, dtype=float)
    active = (pmf[:, 1:] * ndtr((x[:, None]-means)/sd)).sum(axis=1)
    return active + pmf[:, 0] * ((x > 0) if left else (x >= 0))


def offense_distribution(pmf, rate, replacement, actual, *, a=None, b=0,
                         origin_index=None, unit=None, event_min=None, event_max=None):
    pmf = np.asarray(pmf, dtype=float)
    rate, rep, actual = [np.asarray(v, dtype=float) for v in (rate, replacement, actual)]
    if pmf.ndim != 2 or pmf.shape[1] != 801 or not np.allclose(pmf.sum(1), 1):
        raise ValueError('Complete PA mixture required')
    if len(pmf) != len(rate) or rep.shape != rate.shape or actual.shape != rate.shape:
        raise ValueError('Paired forecast arrays required')
    n = np.arange(1, 801, dtype=float)[None, :]
    means = n*(rate[:, None]/600+rep[:, None])
    expected = (pmf[:, 1:] * means).sum(axis=1)
    if a is None:
        grid = np.column_stack((np.zeros(len(rate)), means))
        order = np.argsort(grid, axis=1, kind='stable')
        sorted_values = np.take_along_axis(grid, order, axis=1)
        cdf = np.cumsum(np.take_along_axis(pmf, order, axis=1), axis=1)
        cdf[:, -1] = 1
        quantiles = np.column_stack([sorted_values[np.arange(len(rate)),
            (cdf >= alpha).argmax(axis=1)] for alpha in ALPHAS])
        negative = (pmf*(grid < 0)).sum(axis=1)
        two = (pmf*(grid >= 2)).sum(axis=1)
        impossible = np.zeros(len(rate))
    else:
        sd = n/600*np.sqrt(rate_variance(n, a, b))
        sd = np.broadcast_to(sd, means.shape)
        quantiles = []
        fleft = cdf_normal_mixture(np.zeros(len(rate)), pmf, means, sd, left=True)
        fright = fleft + pmf[:, 0]
        for alpha in ALPHAS:
            lo = np.minimum(0, (means-12*sd).min(axis=1))
            hi = np.maximum(0, (means+12*sd).max(axis=1))
            for _ in range(48):
                mid = (lo+hi)/2
                below = cdf_normal_mixture(mid, pmf, means, sd) < alpha
                lo = np.where(below, mid, lo)
                hi = np.where(below, hi, mid)
            answer = (lo+hi)/2
            answer[(fleft <= alpha) & (alpha <= fright)] = 0
            quantiles.append(answer)
        quantiles = np.column_stack(quantiles)
        negative = fleft
        two = 1-cdf_normal_mixture(np.full(len(rate), 2.), pmf, means, sd)
        if any(v is None for v in (origin_index, unit, event_min, event_max)):
            raise ValueError('Physical event envelope is required')
        idx = np.asarray(origin_index, dtype=float)[:, None]
        lower = n*((event_min-idx)*unit/600+rep[:, None])
        upper = n*((event_max-idx)*unit/600+rep[:, None])
        impossible = (pmf[:, 1:]*(ndtr((lower-means)/sd)+ndtr((means-upper)/sd))).sum(axis=1)
    residual = actual[:, None]-quantiles
    pinball = np.maximum(residual*ALPHAS, residual*(ALPHAS-1)).mean(axis=1)
    low, med, high = quantiles.T
    interval = high-low+10*np.maximum(low-actual, 0)+10*np.maximum(actual-high, 0)
    return dict(q10=low, q50=med, q90=high, pinball=pinball,
                interval_score=interval, width=high-low,
                coverage=(actual >= low) & (actual <= high),
                p_negative=negative, p_two=two, impossible_mass=impossible,
                expected_value=expected)
