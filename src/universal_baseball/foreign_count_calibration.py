"""Count-likelihood repair; all membership/history remains origin/player held out."""
from collections import Counter

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

from .foreign_borrowed_stability import source_coordinates
from .foreign_component_translation import LEAGUES, clr, events, training_pairs
from .foreign_component_translation_v2 import pooled_source
from .post_arrival_history import player_fold

PENALTY = 2.
EFFECTIVE_CAP = 300.


def objective(theta, x, target, environment, weights, *, fixed=None):
    """Convex penalized count likelihood, with an analytic gradient."""
    x, target, environment, weights = map(np.asarray, (x, target, environment, weights))
    if x.shape != target.shape or x.shape != environment.shape or x.ndim != 2 or x.shape[1] != 8:
        raise ValueError('Paired eight-event calibration rows required')
    if weights.shape != (len(x),) or (weights <= 0).any() or not len(weights):
        raise ValueError('Missing positive calibration exposure')
    if any(not np.isfinite(v).all() for v in (x, target, environment, weights, theta)):
        raise ValueError('Nonfinite calibration')
    if (target < 0).any() or not np.allclose(target.sum(1), 1) or (environment <= 0).any() or not np.allclose(environment.sum(1), 1):
        raise ValueError('Invalid frequency or reference')
    if fixed is None:
        if np.shape(theta) != (16,):
            raise ValueError('Sixteen domestic parameters required')
        a, b = theta[:8], theta[8:]
    else:
        if np.shape(theta) != (8,) or np.shape(fixed) != (2, 8):
            raise ValueError('Eight offsets and fixed domestic coefficients required')
        a, b = fixed[0] + theta, fixed[1]
    logits = np.log(environment) + a + x * b
    logp = logits - logsumexp(logits, axis=1, keepdims=True)
    error = weights[:, None] * (np.exp(logp) - target)
    grad = np.r_[error.sum(0), (error * x).sum(0)] if fixed is None else error.sum(0)
    return float(-np.sum(weights[:, None] * target * logp) + PENALTY * (theta @ theta) / 2), grad + PENALTY * theta


def projected_gradient(theta, gradient, bounds):
    g = np.array(gradient, copy=True)
    for j, (lo, hi) in enumerate(bounds):
        if lo is not None and theta[j] <= lo + 1e-8 and g[j] > 0:
            g[j] = 0
        if hi is not None and theta[j] >= hi - 1e-8 and g[j] < 0:
            g[j] = 0
    return g


def solve(x, target, environment, weights, *, fixed=None):
    start = np.zeros(16 if fixed is None else 8)
    bounds = [(None, None)] * 8 + ([(0., 2.)] * 8 if fixed is None else [])
    result = minimize(objective, start, args=(x, target, environment, weights),
        method='L-BFGS-B', jac=True, bounds=bounds,
        options=dict(ftol=1e-15, gtol=1e-7, maxiter=1000, maxls=40)) if fixed is None else minimize(
        lambda z: objective(z, x, target, environment, weights, fixed=fixed), start,
        method='L-BFGS-B', jac=True, bounds=bounds,
        options=dict(ftol=1e-15, gtol=1e-7, maxiter=1000, maxls=40))
    value, grad = objective(result.x, x, target, environment, weights, fixed=fixed)
    pg = projected_gradient(result.x, grad, bounds)
    normalized = float(np.max(abs(pg)) / sum(weights))
    if not result.success or normalized > 1e-7:
        raise ValueError(f'Count optimum failed: {result.message}, per-PA projected gradient {normalized}')
    return result.x, dict(objective=value, iterations=int(result.nit), success=bool(result.success),
        gradient=grad.tolist(), projected_gradient=pg.tolist(), effective_PA=float(sum(weights)),
        projected_gradient_per_effective_PA=normalized)


def fit(domestic, pairs, history, references, cutoff, excluded, coordinate_cache=None):
    excluded = sorted(set(excluded))
    selected = [p for p in domestic if p['target_year'] <= cutoff and p['fold'] not in excluded]
    if not selected or any(p['target_year'] != p['source_year'] + 1 or p['fold'] != player_fold(p['player_id']) for p in selected):
        raise ValueError('Invalid domestic chronology or fold')
    reps = Counter(p['player_id'] for p in selected)
    coordinate_cache = {} if coordinate_cache is None else coordinate_cache
    xs = []
    for p in selected:
        key = p['player_id'], p['source_year'], tuple(excluded)
        if key not in coordinate_cache:
            coordinate_cache[key] = source_coordinates(p, references, excluded)
        xs.append(coordinate_cache[key])
    x = np.asarray(xs)
    target = np.array([np.asarray(p['target_counts']) / p['target_pa'] for p in selected])
    env = np.array([references.get('MLB', p['target_year'], excluded) for p in selected])
    weights = np.array([min(2*p['source_pa']*p['target_pa']/(p['source_pa']+p['target_pa']), EFFECTIVE_CAP) / reps[p['player_id']] for p in selected])
    theta, optimum = solve(x, target, env, weights)
    a, b = theta[:8], theta[8:]
    movers = training_pairs(pairs, cutoff, excluded)
    repetitions = Counter(p['player_id'] for p in movers)
    foreign = []
    for p in movers:
        if not np.array_equal(history[p['player_id'], p['a'], p['from_year']], events(p['from_counts'])):
            raise ValueError('Foreign history mismatch')
        z, note = pooled_source(p['player_id'], p['a'], p['from_year'], history, references, excluded)
        c = events(p['to_counts'])
        foreign.append(dict(player_id=p['player_id'], league=p['a'], from_year=p['from_year'],
            target_year=p['through_year'], source_relative_clr=z.tolist(), source_history=note,
            target_frequency=(c / c.sum()).tolist(), target_reference=references.get('MLB', p['through_year'], excluded).tolist(),
            weight=min(2*p['from_pa']*p['to_pa']/(p['from_pa']+p['to_pa']), EFFECTIVE_CAP) / repetitions[p['player_id']],
            age=p['foreign_age'], contact=p['foreign_contact_band'], power=p['foreign_power_band']))
    coefficients = np.zeros((8, 3)); coefficients[:, 2] = b
    offsets, offset_optima = {}, {}
    for j, league in enumerate(LEAGUES):
        group = [p for p in foreign if p['league'] == league]
        if group:
            d, opt = solve(np.array([p['source_relative_clr'] for p in group]),
                np.array([p['target_frequency'] for p in group]), np.array([p['target_reference'] for p in group]),
                np.array([p['weight'] for p in group]), fixed=np.array([a, b]))
        else:
            d, opt = np.zeros(8), dict(unsupported=True, effective_PA=0)
        offsets[league] = d.tolist(); offset_optima[league] = opt
        coefficients[:, j] = a + d
    return dict(cutoff=cutoff, excluded_folds=excluded, coefficients=coefficients.tolist(),
        domestic_intercepts=a.tolist(), domestic_slopes=b.tolist(), domestic_optimum=optimum,
        foreign_offsets=offsets, foreign_optima=offset_optima, foreign_pairs=foreign,
        people_by_league={l: len({p['player_id'] for p in movers if p['a'] == l}) for l in LEAGUES},
        domestic_keys=[[p['player_id'], p['source_year']] for p in selected],
        domestic_people=len(reps), domestic_pairs=len(selected),
        domestic_x_min=x.min(0).tolist(), domestic_x_max=x.max(0).tolist(),
        max_target_year=max(p['target_year'] for p in selected),
        park_neutral=False, unbiased_league_strength=False,
        count_likelihood_calibration=True, effective_count_cap=EFFECTIVE_CAP, penalty=PENALTY)


def fresh_foreign_route(source, domestic_rows, origin):
    """Origin-only evidence ordering, not an employment or arrival rule."""
    years = []
    if source is not None:
        if source['origin_year'] != origin:
            raise ValueError('Wrong source origin')
        for league in LEAGUES:
            for lag in range(3):
                r = source['foreign_history_counts'][f'{league}_{lag}']
                if r['season'] != origin - lag:
                    raise ValueError('Future or mismatched source season')
                if r['player_identity_and_stat_observed'] and r['counts']['pa'] >= 30:
                    years.append(r['season'])
    totals = {}
    for row in domestic_rows:
        if row['season'] <= origin:
            totals[row['season']] = totals.get(row['season'], 0) + row['plate_appearances']
    latest_domestic = max((y for y, n in totals.items() if n >= 30), default=None)
    latest_foreign = max(years, default=None)
    used = latest_foreign is not None and (latest_domestic is None or latest_foreign > latest_domestic)
    return dict(eligible=used, latest_substantial_foreign=latest_foreign,
                latest_substantial_domestic=latest_domestic,
                same_year_ambiguous=latest_foreign is not None and latest_foreign == latest_domestic)
