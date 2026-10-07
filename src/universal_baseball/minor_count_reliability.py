"""Count uncertainty calibration; no MLB quality labels or player-value fits."""
import math

import numpy as np
from scipy.optimize import minimize
from scipy.special import betaln, expit, gammaln
from scipy.stats import betabinom, binom, nbinom, poisson

STRENGTH_BOUNDS = (0.001, 1_000_000.)
START_STRENGTHS = (1., 100., 10_000.)


def validate_counts(x, n, binomial):
    x, n = np.asarray(x, dtype=float), np.asarray(n, dtype=float)
    if x.shape != n.shape or not (np.isfinite(x).all() and np.isfinite(n).all()):
        raise ValueError('Missing or mismatched counts')
    if (x < 0).any() or (n < 0).any() or (x != np.floor(x)).any() or (n != np.floor(n)).any():
        raise ValueError('Counts and outs/trials must be nonnegative integers')
    if ((n == 0) & (x != 0)).any() or (binomial and (x > n).any()):
        raise ValueError('Impossible source counts')
    return x, n


def marginal_log_mass(x, n, mean, strength, binomial):
    x, n = validate_counts(x, n, binomial)
    if mean < 0 or (binomial and mean > 1) or not math.isfinite(mean):
        raise ValueError('Invalid prior mean')
    if strength is None or mean == 0 or (binomial and mean == 1):
        return binom.logpmf(x, n, mean) if binomial else poisson.logpmf(x, n * mean)
    if strength <= 0 or not math.isfinite(strength):
        raise ValueError('Invalid prior strength')
    if binomial:
        a, b = mean * strength, (1 - mean) * strength
        result = gammaln(n + 1) - gammaln(x + 1) - gammaln(n - x + 1)
        result += betaln(x + a, n - x + b) - betaln(a, b)
    else:
        a = mean * strength
        result = gammaln(x + a) - gammaln(a) - gammaln(x + 1)
        result += a * np.log(strength / (strength + n))
        result += np.where(n > 0, x * np.log(np.maximum(n, 1) / (strength + n)), 0.)
    return np.where(n == 0, 0., result)


def fit_prior(x, n, binomial, fallback):
    """Each x,n pair is ONE person's pooled source count, not a repeated row."""
    x, n = validate_counts(x, n, binomial)
    if not len(x) or (n <= 0).any():
        raise ValueError('Reference people need positive source exposure')
    pooled_mean = float(x.sum() / n.sum())
    point_loss = -float(marginal_log_mass(x, n, pooled_mean, None, binomial).sum())
    record = dict(people=len(x),pooled_count=int(x.sum()),pooled_exposure=int(n.sum()),
                  people_with_multiple_trials=int((n > 1).sum()),positive_people=int((x > 0).sum()),
                  point_mean=pooled_mean,point_loss=point_loss,starts=[])
    if pooled_mean == 0 or (binomial and pooled_mean == 1) or (binomial and (n == 1).all()):
        return dict(record,mean=pooled_mean,strength=None,status='exact_boundary_point' if pooled_mean in (0.,1.)
                    else 'one_trial_concentration_unidentified',boundary=False)
    mean_bounds = (-20.,20.) if binomial else (-20.,5.)
    bounds = (mean_bounds,tuple(math.log(v) for v in STRENGTH_BOUNDS))
    initial = math.log(pooled_mean / (1 - pooled_mean)) if binomial else math.log(pooled_mean)
    initial = min(max(initial,mean_bounds[0]),mean_bounds[1])

    def objective(z):
        mean = float(expit(z[0])) if binomial else math.exp(z[0])
        return -float(marginal_log_mass(x,n,mean,math.exp(z[1]),binomial).sum()) / len(x)

    candidates = []
    for k in START_STRENGTHS:
        result = minimize(objective,[initial,math.log(k)],method='L-BFGS-B',bounds=bounds,
                          options=dict(maxiter=300,ftol=1e-10))
        mean = float(expit(result.x[0])) if binomial else math.exp(result.x[0])
        strength = float(math.exp(result.x[1]))
        finite = bool(np.isfinite(result.fun) and np.isfinite(result.x).all())
        note = dict(start_mean=pooled_mean,start_strength=k,success=bool(result.success),message=str(result.message),
                    iterations=int(result.nit),mean=mean,strength=strength,
                    average_loss=float(result.fun) if finite else None)
        record['starts'].append(note)
        if result.success and finite:candidates.append((float(result.fun),mean,strength,result.x))
    if not candidates:
        return dict(record,mean=fallback['mean'],strength=fallback['strength'],status='optimization_failure_moment_fallback',boundary=False)
    best, mean, strength, z = min(candidates,key=lambda item:item[0])
    if point_loss / len(x) <= best + 1e-6:
        return dict(record,mean=pooled_mean,strength=None,status='point_likelihood_selected',boundary=False)
    boundary = any(abs(v-lo)<1e-4 or abs(v-hi)<1e-4 for v,(lo,hi) in zip(z,bounds))
    return dict(record,mean=mean,strength=strength,status='count_likelihood',boundary=boundary)


def posterior(x, n, prior, binomial):
    validate_counts([x],[n],binomial)
    mean, k = prior['mean'], prior['strength']
    if k is None or mean == 0 or (binomial and mean == 1):
        return dict(mean=mean,strength=None,weight=0.,latent_variance=0.)
    updated_k = k + n
    updated_mean = (k * mean + x) / updated_k
    variance = updated_mean * (1 - updated_mean) / (updated_k + 1) if binomial else updated_mean / updated_k
    return dict(mean=updated_mean,strength=updated_k,weight=n / updated_k,latent_variance=variance)


def predictive(x, exposure, post, binomial):
    validate_counts([x],[exposure],binomial)
    mean, k = post['mean'], post['strength']
    if exposure == 0:
        return dict(loss=0.,impossible=False,lower=0.,upper=0.,covered=True,predictive_variance=0.)
    if k is None or mean == 0 or (binomial and mean == 1):
        distribution = binom(exposure,mean) if binomial else poisson(exposure * mean)
    elif binomial:
        distribution = betabinom(exposure,mean * k,(1 - mean) * k)
    else:
        distribution = nbinom(mean * k,k / (k + exposure))
    loss = -float(distribution.logpmf(x))
    lo, hi = map(float,distribution.ppf([.05,.95]))
    return dict(loss=loss if math.isfinite(loss) else None,impossible=not math.isfinite(loss),
                lower=lo,upper=hi,covered=lo <= x <= hi,predictive_variance=float(distribution.var()))
