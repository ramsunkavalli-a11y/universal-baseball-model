"""Mean-preserving positive-count law with a separate nonparticipation atom."""
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import betabinom, binom

MAX_PA = 800
LOG_FLOOR = np.log(1e-15)


def positive_logpmf(actual, mean, concentration):
    actual, mean = np.asarray(actual), np.asarray(mean)
    assert ((actual >= 1) & (actual <= MAX_PA)).all()
    assert ((mean >= 1) & (mean <= MAX_PA)).all()
    out = np.full(len(mean), -np.inf)
    interior = (mean > 1) & (mean < MAX_PA)
    mu = (mean[interior] - 1) / (MAX_PA - 1)
    out[interior] = betabinom.logpmf(actual[interior]-1, MAX_PA-1, mu*concentration, (1-mu)*concentration)
    boundary_match = ~interior & (actual == mean)
    out[boundary_match] = 0
    return out


def fit_concentration(actual, mean, weights):
    weights = np.asarray(weights, dtype=float)
    assert np.isfinite(weights).all() and (weights > 0).all()
    def objective(log_k):
        return float(np.average(-np.maximum(positive_logpmf(actual, mean, np.exp(log_k)), LOG_FLOOR), weights=weights))
    result = minimize_scalar(objective, bounds=(np.log(.1), np.log(1000)), method='bounded', options={'xatol':1e-8})
    assert result.success and np.isfinite(result.fun)
    # Explicit bound comparison is constrained optimization, not held-out tuning.
    options = [(result.fun, float(np.exp(result.x))), (objective(np.log(.1)), .1), (objective(np.log(1000)), 1000.)]
    loss, concentration = min(options)
    logs = positive_logpmf(actual, mean, concentration)
    return dict(concentration=concentration, negative_log_likelihood=loss,
        scoring_floor=1e-15, floored_labels=int((logs < LOG_FLOOR).sum()),
        boundary_means=int(((mean==1)|(mean==MAX_PA)).sum()), optimizer_success=bool(result.success),
        optimizer_evaluations=int(result.nfev))


def mixture_pmf(p, mean, concentration=None):
    p, mean = np.asarray(p, dtype=float), np.asarray(mean, dtype=float)
    assert np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
    assert np.isfinite(mean).all() and ((mean >= 1) & (mean <= MAX_PA)).all()
    positive = np.zeros((len(p), MAX_PA))
    interior = (mean > 1) & (mean < MAX_PA)
    mu = (mean[interior]-1)/(MAX_PA-1)
    grid = np.arange(MAX_PA)[None,:]
    if concentration is None:
        positive[interior] = binom.pmf(grid, MAX_PA-1, mu[:,None])
    else:
        positive[interior] = betabinom.pmf(grid, MAX_PA-1, mu[:,None]*concentration, (1-mu[:,None])*concentration)
    positive[mean == 1,0] = 1
    positive[mean == MAX_PA,-1] = 1
    sums = positive.sum(axis=1)
    assert np.allclose(sums,1,rtol=0,atol=1e-8)
    positive /= sums[:,None]  # numerical normalization only
    assert np.allclose(positive @ np.arange(1,MAX_PA+1), mean, rtol=0, atol=1e-6)
    pmf = np.column_stack((1-p,p[:,None]*positive))
    assert np.allclose(pmf.sum(axis=1),1,rtol=0,atol=1e-12)
    assert np.allclose(pmf @ np.arange(MAX_PA+1), p*mean,rtol=0,atol=1e-6)
    return pmf


def distribution_terms(pmf, actual):
    cdf = np.cumsum(pmf,axis=1)
    cdf[:,-1] = 1
    quantiles = np.column_stack([(cdf >= alpha).argmax(axis=1) for alpha in [.1,.5,.9]])
    residual = np.asarray(actual)[:,None] - quantiles
    pinball = np.maximum(residual*np.array([.1,.5,.9]), residual*(np.array([.1,.5,.9])-1)).mean(axis=1)
    lo,med,hi = quantiles.T
    interval = hi-lo+10*np.maximum(lo-actual,0)+10*np.maximum(actual-hi,0)
    crps = ((cdf[:,:MAX_PA]-(np.arange(MAX_PA)[None,:] >= actual[:,None]))**2).sum(axis=1)
    return dict(q10=lo,q50=med,q90=hi,pinball=pinball,interval_score=interval,
        coverage=(actual>=lo)&(actual<=hi),width=hi-lo,crps=crps,
        p400=pmf[:,400:].sum(axis=1))
