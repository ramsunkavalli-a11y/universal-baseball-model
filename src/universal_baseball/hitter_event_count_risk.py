"""Integer event-count risks with exact theoretical offense-mean conservation."""
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import logsumexp

from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.hitter_workload_risk import mixture_pmf

N = np.arange(1, 801, dtype=float)
MASTER_SEED = 88004


def tilt(reference, target):
    target = np.atleast_1d(np.asarray(target, dtype=float))
    ref = np.broadcast_to(np.asarray(reference, dtype=float), (len(target), 8))
    if (ref <= 0).any() or not np.isfinite(ref).all() or not np.allclose(ref.sum(1), 1):
        raise ValueError('Strictly positive eight-event reference required')
    if not np.isfinite(target).all() or (target <= VALUES.min()).any() or (target >= VALUES.max()).any():
        raise ValueError('Event center outside physical support')
    low = np.full(len(target), -80.); high = np.full(len(target), 80.); lam = np.zeros(len(target))
    for _ in range(70):
        logits = np.log(ref)+lam[:, None]*VALUES
        prob = np.exp(logits-logsumexp(logits, axis=1, keepdims=True))
        mean = prob @ VALUES; error = mean-target
        if np.max(np.abs(error)) < 1e-12:
            break
        low = np.where(error < 0, lam, low); high = np.where(error >= 0, lam, high)
        variance = prob @ (VALUES**2)-mean**2
        step = lam-error/np.maximum(variance, 1e-14)
        lam = np.where((step > low) & (step < high), step, (low+high)/2)
    else:
        raise RuntimeError('Mean-preserving exponential tilt did not converge')
    assert np.allclose(prob @ VALUES, target, atol=1e-12, rtol=0)
    return prob


def workload_center(mean, concentration):
    means = np.atleast_1d(np.asarray(mean, dtype=float))
    pmf = mixture_pmf(np.ones(len(means)), means, concentration)[:, 1:]
    center = (pmf @ (N*np.log(N)))/means
    assert np.allclose(pmf @ N, means, atol=1e-6, rtol=0)
    return center, pmf


def rate_variance(prob, n, phi):
    prob, n = np.asarray(prob, dtype=float), np.asarray(n, dtype=float)
    if phi <= 0 or (n <= 0).any():
        raise ValueError('Positive concentration and PA required')
    mu = prob @ VALUES
    event_var = prob @ (VALUES**2)-mu**2
    return UNIT**2*event_var*(n+phi)/(n*(1+phi))


def fit_count_laws(actual_rate, actual_pa, rate, origin_index, reference, center, weights):
    y, n, rate, idx, center, w = [np.asarray(x, dtype=float) for x in
        (actual_rate, actual_pa, rate, origin_index, center, weights)]
    if not len(y) or any(x.shape != y.shape for x in [n, rate, idx, center, w]):
        raise ValueError('Paired nonempty calibration arrays required')
    if not all(np.isfinite(x).all() for x in [y, n, rate, idx, center, w]) or (n <= 0).any() or (w <= 0).any():
        raise ValueError('Invalid count calibration')
    w = w/w.sum(); h = np.log(n)-center

    def loss(logphi, beta):
        mean = rate+beta*h
        prob = tilt(reference, idx+mean/UNIT)
        var = rate_variance(prob, n, float(np.exp(logphi)))
        return .5*float(w @ (np.log(var)+(y-mean)**2/var))

    bounds = (np.log(.1), np.log(1000000))
    scalar = minimize_scalar(lambda v: loss(v, 0), bounds=bounds, method='bounded', options={'xatol': 1e-8})
    if not scalar.success:
        raise RuntimeError('Independent concentration fit failed')
    candidates = [(float(scalar.fun), float(scalar.x)), (loss(bounds[0], 0), bounds[0]), (loss(bounds[1], 0), bounds[1])]
    objective, independent_logphi = min(candidates)
    independent = dict(phi=float(np.exp(independent_logphi)), beta=0., objective=objective)
    fits = []
    for initial_beta in [0., .2, -.2]:
        result = minimize(lambda theta: loss(theta[0], theta[1]), [independent_logphi, initial_beta],
            method='L-BFGS-B', bounds=[bounds, (-1., 1.)], options={'maxiter': 1000, 'ftol': 1e-12, 'gtol': 1e-7})
        if not result.success or not np.isfinite(result.fun):
            raise RuntimeError(f'Associated count calibration failed: {result.message}')
        fits.append(dict(phi=float(np.exp(result.x[0])), beta=float(result.x[1]), objective=float(result.fun),
                         start_beta=initial_beta, iterations=int(result.nit)))
    associated = min(fits, key=lambda x: x['objective'])
    return dict(independent=independent, associated=associated, optimizer_checks=fits,
                residual_bias=float(w @ (y-rate)), associated_residual_bias=float(w @ (y-rate-associated['beta']*h)),
                phi_bounds=[.1, 1000000], beta_bounds=[-1., 1.],
                associated_beta_at_bound=bool(abs(associated['beta']) > .999999))


def mixture_terms(positive_values, p, actual):
    values = np.asarray(positive_values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or not 0 <= p <= 1:
        raise ValueError('Finite positive-activity sample and valid probability required')
    grid = np.concatenate((values, [0.]))
    masses = np.concatenate((np.full(len(values), p/len(values)), [1-p]))
    order = np.argsort(grid, kind='stable'); v = grid[order]; w = masses[order]
    cdf = np.cumsum(w); cdf[-1] = 1
    quant = np.array([v[np.searchsorted(cdf, alpha, side='left')] for alpha in [.1, .5, .9]])
    residual = actual-quant; alpha = np.array([.1, .5, .9])
    return dict(q10=float(quant[0]), q50=float(quant[1]), q90=float(quant[2]),
        pinball=float(np.maximum(residual*alpha, residual*(alpha-1)).mean()),
        interval_score=float(quant[2]-quant[0]+10*max(quant[0]-actual, 0)+10*max(actual-quant[2], 0)),
        width=float(quant[2]-quant[0]), coverage=bool(quant[0] <= actual <= quant[2]),
        p_negative=float(p*np.mean(values < 0)), p_two=float(p*np.mean(values >= 2)),
        sampled_expected_value=float(p*np.mean(values)), impossible_mass=0.)


def simulate(reference, rate, index, rep, p, conditional_mean, concentration, phi, beta, *, row_id, draws=4096, replicate=0):
    center, pmf = workload_center([conditional_mean], concentration)
    center = float(center[0]); pmf = pmf[0]
    rng = np.random.default_rng(np.random.SeedSequence([MASTER_SEED, int(row_id), int(replicate)]))
    cdf = np.cumsum(pmf); cdf[-1] = 1
    n = 1+np.searchsorted(cdf, rng.random(draws), side='left')
    unique, inverse = np.unique(n, return_inverse=True)
    rate_at_n = rate+beta*(np.log(unique)-center)
    profile = tilt(reference, index+rate_at_n/UNIT)[inverse]
    latent = rng.gamma(phi*profile, 1.)
    if (latent.sum(1) <= 0).any():
        raise RuntimeError('Degenerate Dirichlet numerical draw')
    latent /= latent.sum(1, keepdims=True)
    counts = rng.multinomial(n, latent)
    assert np.array_equal(counts.sum(1), n) and (counts >= 0).all()
    assert np.issubdtype(counts.dtype, np.integer)
    values = (counts @ VALUES-n*index)*UNIT/600+n*rep
    lower = n*((VALUES.min()-index)*UNIT/600+rep)
    upper = n*((VALUES.max()-index)*UNIT/600+rep)
    assert (values >= lower-1e-10).all() and (values <= upper+1e-10).all()
    theoretical_rates = rate+beta*(np.log(N)-center)
    theoretical = float(p*(pmf @ (N*(theoretical_rates/600+rep))))
    assert np.isclose(theoretical, p*conditional_mean*(rate/600+rep), atol=1e-10, rtol=0)
    return dict(pa=n, counts=counts, values=values, center=center, expected_value=theoretical,
                profile_at_draw=profile, row_id=int(row_id), draws=draws, replicate=replicate)
