"""V17: certified role evidence and one fractional multinomial conditional mean.

Assignments are not defensive ability. The caller owns held-person chronology,
fixed workloads, unknown-role reserves, native quality and league capacities.
"""
from collections import Counter

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

ROLES = tuple(range(2, 11))
SPORTS = (1, 11, 12, 13, 14, 16)
STAGES = ('Current MLB', 'Upper minors', 'Lower minors', 'Inactive / unknown')


def vector(value):
    a = np.asarray(value, dtype=float)
    if a.shape != (9,) or not np.isfinite(a).all() or (a < 0).any():
        raise ValueError('Invalid nine-role exposure')
    return a


def scaled_counts(value):
    return np.log1p(vector(value)) / np.log(163.)


def names():
    out = []
    for sport in SPORTS:
        out += [f'current_s{sport}_r{p}' for p in ROLES]
        out += [f'current_s{sport}_field_known', f'current_s{sport}_DH_known']
    for scope in ('MLB', 'minor'):
        for period in ('late', 'unplaced'):
            out += [f'{scope}_{period}_r{p}' for p in ROLES]
        out += [f'{scope}_period_field_known', f'{scope}_period_DH_known']
        for lag in (1, 2):
            out += [f'{scope}_lag{lag}_r{p}' for p in ROLES]
            out += [f'{scope}_lag{lag}_known']
        out += [f'{scope}_older_seen_r{p}' for p in ROLES]
        out += [f'{scope}_older_history_known']
    out += [f'roster_r{p}' for p in ROLES]
    out += [f'stage_{s}' for s in STAGES]
    return out + ['stage_other', 'age_centered', 'age_unknown', 'prior_debut']


def features(row, source, bounds, certifications, annual):
    """All counts in starts-equivalent; missing coverage is an explicit flag.

    Source and bounds are already independently certified, not inferred from
    lack of a game-log row. Old annual records supplied here may contain future
    years, which are explicitly excluded before use.
    """
    y, pid = row['origin_year'], row['player_id']
    if (source['origin'], source['player_id'], source['row_id'], source['fold']) != (
            y, pid, row['row_id'], row['outer_fold']):
        raise ValueError('Current source identity mismatch')
    if (bounds['origin'], bounds['player_id'], bounds['row_id'], bounds['fold']) != (
            y, pid, row['row_id'], row['outer_fold']):
        raise ValueError('Period-bound identity mismatch')
    dh = float(row['origin_dh_outs'])
    if not np.isfinite(dh) or dh <= 0:
        raise ValueError('Invalid origin conversion')
    periods = source['current_role_periods']
    if any(p['season'] != y or p['player_id'] != pid or p['sport_id'] not in SPORTS
           for p in periods):
        raise ValueError('Foreign/future current-role observation')
    out, current = {}, np.zeros(9)
    raw_current = {}
    for sport in SPORTS:
        cert = certifications.get((pid, y, sport))
        field_known = bool(cert and cert['measurements']['fielding_outs']['full_year'])
        dh_known = bool(cert and cert['measurements']['reviewed_starts']['full_year'])
        counts = np.zeros(9)
        for p in periods:
            if p['sport_id'] != sport:
                continue
            if p['position_code'] == 1:
                continue  # Pitching appearances are not a hitter-field/DH role.
            index = ROLES.index(p['position_code'])
            if p['position_code'] == 10:
                if dh_known:
                    counts[index] += p['reviewed_starts']
            elif field_known:
                counts[index] += p['fielding_outs'] / dh
        out.update(zip([f'current_s{sport}_r{p}' for p in ROLES], scaled_counts(counts)))
        out[f'current_s{sport}_field_known'] = float(field_known)
        out[f'current_s{sport}_DH_known'] = float(dh_known)
        current += counts
        raw_current[str(sport)] = dict(counts=counts.tolist(), field_known=field_known, DH_known=dh_known)
    older = np.zeros(9)
    past = [a for a in annual if a['season'] < y]
    if any(a['player_id'] != pid for a in past):
        raise ValueError('Foreign annual history')
    for scope in ('MLB', 'minor'):
        field = bounds[f'{scope}_fielding_outs']
        starts = bounds[f'{scope}_reviewed_starts']
        for period, key in [('late', 'August_onward_minimum'), ('unplaced', 'unresolved_period_exposure')]:
            counts = np.zeros(9)
            if field is not None:
                counts[:8] = vector(field[key])[:8] / dh
            if starts is not None:
                counts[8] = vector(starts[key])[8]
            out.update(zip([f'{scope}_{period}_r{p}' for p in ROLES], scaled_counts(counts)))
        out[f'{scope}_period_field_known'] = float(field is not None)
        out[f'{scope}_period_DH_known'] = float(starts is not None)
        history = [a for a in past if a['is_mlb'] == (scope == 'MLB')]
        for lag in (1, 2):
            rows = [a for a in history if a['season'] == y-lag]
            counts = sum((np.array([a[f'outs_{p}'] / dh for p in ROLES[:8]] + [a['starts_10']], float)
                          for a in rows), np.zeros(9))
            out.update(zip([f'{scope}_lag{lag}_r{p}' for p in ROLES], scaled_counts(counts)))
            out[f'{scope}_lag{lag}_known'] = float(bool(rows))
        total = sum((np.array([a[f'outs_{p}'] / dh for p in ROLES[:8]] + [a['starts_10']], float)
                     for a in history), np.zeros(9))
        out.update(zip([f'{scope}_older_seen_r{p}' for p in ROLES], (total > 0).astype(float)))
        out[f'{scope}_older_history_known'] = float(bool(history))
        older += total
    roster = np.array([str(row['source_position']) == str(p) for p in ROLES], float)
    out.update(zip([f'roster_r{p}' for p in ROLES], roster))
    out.update({f'stage_{s}': float(row['stage'] == s) for s in STAGES})
    out['stage_other'] = float(row['stage'] not in STAGES)
    age = row['age']
    out.update(age_centered=(float(age)-27.) / 10 if age is not None else 0.,
               age_unknown=float(age is None), prior_debut=float(row['prior_debut']))
    fallback = current if current.sum() else older if older.sum() else roster
    kind = 'current_own_roles' if current.sum() else 'older_own_roles' if older.sum() else 'roster_or_unknown'
    dominant = ROLES[int(current.argmax())] if current.sum() else 0
    if set(out) != set(names()) or not np.isfinite(list(out.values())).all():
        raise ValueError('Invalid feature schema/values')
    return dict(inputs=out, current_dominant_role=dominant, current_raw=raw_current,
                current_counts=current.tolist(), older_counts=older.tolist(),
                fallback_shares=(fallback / fallback.sum()).tolist() if fallback.sum() else [0.]*9,
                fallback_kind=kind, current_coverage=source['current_source_status'])


def person_weights(people):
    counts = Counter(people)
    return np.array([1. / counts[p] for p in people], float)


def objective(flat, design, targets, weights):
    """Exact gradient; intercept unpenalized, fixed unit L2 on every other term."""
    b = np.asarray(flat).reshape(design.shape[1], 9)
    z = design @ b
    logp = z - logsumexp(z, axis=1, keepdims=True)
    residual = (np.exp(logp)-targets) * weights[:, None]
    gradient = design.T @ residual
    gradient[1:] += b[1:]
    loss = -np.sum(weights[:, None]*targets*logp) + .5*np.sum(b[1:]**2)
    return float(loss), gradient.ravel()


def fit(x, targets, people):
    x, targets = np.asarray(x, float), np.asarray(targets, float)
    if x.ndim != 2 or targets.shape != (len(x), 9) or len(people) != len(x) or not len(x):
        raise ValueError('Invalid training shapes')
    if not np.isfinite(x).all() or not np.isfinite(targets).all() or (targets < 0).any():
        raise ValueError('Invalid training values')
    if not np.allclose(targets.sum(axis=1), 1., atol=1e-12, rtol=0):
        raise ValueError('Fractional labels must sum to one')
    weights = person_weights(people)
    design = np.column_stack([np.ones(len(x)), x])
    start = np.zeros((design.shape[1], 9))
    mean = np.average(targets, axis=0, weights=weights)
    start[0] = np.log(np.maximum(mean, 1e-8))
    start[0] -= start[0].mean()
    result = minimize(objective, start.ravel(), args=(design, targets, weights), jac=True,
                      method='L-BFGS-B', options=dict(maxiter=10000, ftol=1e-13, gtol=1e-7, maxls=100))
    if not result.success or not np.isfinite(result.x).all():
        raise ValueError('Fractional role fit failed: ' + result.message)
    b = result.x.reshape(design.shape[1], 9)
    b[0] -= b[0].mean()
    loss, gradient = objective(b.ravel(), design, targets, weights)
    return dict(coefficients=b.tolist(), objective=loss, iterations=int(result.nit),
                max_gradient=float(np.max(abs(gradient))), optimizer_message=str(result.message),
                training_rows=len(x), training_people=len(set(people)), person_weight_sum=float(weights.sum()),
                coefficient_penalty=1.)


def predict(x, model):
    x = np.asarray(x, float)
    b = np.asarray(model['coefficients'], float)
    if x.ndim != 2 or b.shape != (x.shape[1]+1, 9) or not np.isfinite(x).all():
        raise ValueError('Invalid prediction matrix')
    logits = np.column_stack([np.ones(len(x)), x]) @ b
    p = np.exp(logits-logsumexp(logits, axis=1, keepdims=True))
    if not np.isfinite(p).all() or not np.allclose(p.sum(axis=1), 1., atol=1e-12, rtol=0):
        raise ValueError('Invalid predicted role shares')
    return p


def allowed_shares(learned, fallback, *, unseen, catching, unknown):
    if unknown:
        return np.zeros(9)
    p = vector(fallback if unseen else learned).copy()
    if not catching:
        p[0] = 0.
    if p.sum() <= 0:
        raise ValueError('No allowed role after existing catching guard')
    return p / p.sum()
