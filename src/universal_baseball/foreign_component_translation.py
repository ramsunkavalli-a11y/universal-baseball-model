"""Small forward-mover predictive adjustment, not an unbiased league MLE."""
from collections import Counter, defaultdict

import numpy as np
from scipy.optimize import lsq_linear

from .post_arrival_history import player_fold

EVENTS = ['other', 'K', 'UBB', 'HBP', '1B', '2B', '3B', 'HR']
LEAGUES = ['NPB', 'KBO']
RIDGE = 2.0


def events(row):
    """Other includes IBB, sacrifices and outs; never double-count a PA."""
    known = np.array([row['so'], row['bb'] - row['ibb'], row['hbp'],
                      row['hits'] - row['doubles'] - row['triples'] - row['hr'],
                      row['doubles'], row['triples'], row['hr']], dtype=float)
    result = np.r_[row['pa'] - known.sum(), known]
    if not np.isfinite(result).all() or (result < 0).any() or row['pa'] < 0:
        raise ValueError('Invalid mutually exclusive source counts')
    return result


def probability(counts):
    counts = np.asarray(counts, dtype=float)
    if counts.shape != (8,) or not np.isfinite(counts).all() or (counts < 0).any():
        raise ValueError('Invalid probability counts')
    return (counts + .5) / (counts.sum() + 4)


def clr(p):
    p = np.asarray(p, dtype=float)
    if p.shape != (8,) or (p <= 0).any() or not np.isfinite(p).all() or not np.isclose(p.sum(), 1):
        raise ValueError('Invalid event probabilities')
    z = np.log(p)
    return z - z.mean()


def softmax(z):
    z = np.asarray(z, dtype=float)
    if not np.isfinite(z).all():
        raise ValueError('Invalid predicted event logits')
    q = np.exp(z - z.max())
    return q / q.sum()


class References:
    """All-player league references, subtracting only known held identities."""
    def __init__(self, rows):
        self.totals = defaultdict(lambda: np.zeros(8))
        self.folds = defaultdict(lambda: np.zeros(8))
        self.unmapped = defaultdict(float)
        for r in rows:
            if r['season'] > 2024:
                continue
            key = r['league'], r['season']
            c = events(r)
            self.totals[key] += c
            if r['player_id'] is None:
                self.unmapped[key] += r['pa']
            else:
                self.folds[key, player_fold(r['player_id'])] += c

    def counts(self, league, year, excluded):
        key = league, year
        if key not in self.totals:
            raise ValueError('Missing league reference')
        result = self.totals[key].copy()
        for fold in set(excluded):
            result -= self.folds[key, fold]
        if (result < 0).any() or result.sum() <= 0:
            raise ValueError('Empty or invalid held-player reference')
        return result

    def get(self, league, year, excluded):
        return probability(self.counts(league, year, excluded))


def training_pairs(pairs, cutoff, excluded):
    selected = [p for p in pairs if p['through_year'] <= cutoff
                and p['fold'] not in set(excluded) and p['minimum_pa'] == 30
                and p['mechanism'] == 'consecutive_season'
                and p['a'] in LEAGUES and p['b'] == 'MLB'
                and not p['domestic_2020_exception']
                and p['role_evidence']['supported_hitter']]
    keys = [(p['player_id'], p['a'], p['from_year'], p['through_year']) for p in selected]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate qualified mover')
    for p in selected:
        if p['through_year'] != p['from_year'] + 1 or p['fold'] != player_fold(p['player_id']):
            raise ValueError('Invalid mover chronology or player fold')
        if min(p['from_pa'], p['to_pa']) < 30:
            raise ValueError('Mover below locked PA floor')
        if events(p['from_counts']).sum() != p['from_pa'] or events(p['to_counts']).sum() != p['to_pa']:
            raise ValueError('Mover denominator mismatch')
    return selected


def fit(pairs, references, cutoff, excluded):
    excluded = sorted(set(excluded))
    selected = training_pairs(pairs, cutoff, excluded)
    repetitions = Counter(p['player_id'] for p in selected)
    weights, xs, ys = [], [], []
    for p in selected:
        x = clr(probability(events(p['from_counts']))) - clr(references.get(p['a'], p['from_year'], excluded))
        y = clr(probability(events(p['to_counts']))) - clr(references.get('MLB', p['through_year'], excluded))
        harmonic = 2 / (1 / p['from_pa'] + 1 / p['to_pa'])
        weights.append(min(harmonic / 300, 1) / repetitions[p['player_id']])
        xs.append(x); ys.append(y)
    x = np.asarray(xs).reshape((-1, 8)); y = np.asarray(ys).reshape((-1, 8))
    w = np.asarray(weights)
    coefficients = np.zeros((8, 3))
    gradients = []
    for j in range(8):
        design = np.array([[float(p['a'] == 'NPB'), float(p['a'] == 'KBO'), x[i, j]]
                           for i, p in enumerate(selected)]).reshape((-1, 3))
        a = np.vstack([design * np.sqrt(w)[:, None], np.eye(3) * np.sqrt(RIDGE)])
        b = np.r_[y[:, j] * np.sqrt(w), np.zeros(3)]
        result = lsq_linear(a, b, bounds=([-np.inf, -np.inf, 0], [np.inf, np.inf, 2]),
                            tol=1e-12, max_iter=200)
        if not result.success:
            raise ValueError('Translation optimizer failed')
        coefficients[j] = result.x
        gradient = a.T @ (a @ result.x - b)
        if np.max(np.abs(gradient[:2])) > 1e-7:
            raise ValueError('Translation intercept optimum failed')
        slope = result.x[2]
        if slope < 1e-6:
            valid = gradient[2] >= -1e-7
        elif slope > 2 - 1e-6:
            valid = gradient[2] <= 1e-7
        else:
            valid = abs(gradient[2]) < 1e-7
        if not valid:
            raise ValueError('Translation constrained slope optimum failed')
        gradients.append(gradient.tolist())
    return dict(cutoff=cutoff, excluded_folds=excluded, coefficients=coefficients.tolist(),
                people=len(repetitions), people_by_league={l: len({p['player_id'] for p in selected if p['a'] == l}) for l in LEAGUES},
                max_target_year=max((p['through_year'] for p in selected), default=None),
                pairs=[dict(player_id=p['player_id'], league=p['a'], from_year=p['from_year'],
                            target_year=p['through_year'], weight=weights[i], source_relative_clr=x[i].tolist(),
                            target_relative_clr=y[i].tolist()) for i, p in enumerate(selected)],
                optimizer_gradients=gradients,
                slope_lower_bound_events=[EVENTS[j] for j in range(8) if coefficients[j, 2] < 1e-6],
                slope_upper_bound_events=[EVENTS[j] for j in range(8) if coefficients[j, 2] > 2 - 1e-6],
                park_neutral=False, unbiased_league_strength=False)


def profile(origin_input, model, references):
    origin = origin_input['origin_year']
    if model['cutoff'] != origin:
        raise ValueError('Mismatched translation cutoff')
    excluded = model['excluded_folds']
    coef = np.asarray(model['coefficients'])
    pieces, total, supported, weighted = [], 0., 0., np.zeros(8)
    mlb_reference = references.get('MLB', origin, excluded)
    for league in LEAGUES:
        observed, own, environment, exposure = [], np.zeros(8), np.zeros(8), 0.
        for lag, recency in enumerate([5., 4., 3.]):
            s = origin_input['foreign_history_counts'][f'{league}_{lag}']
            if s['season'] != origin - lag:
                raise ValueError('Foreign lag mismatch')
            if not s['player_identity_and_stat_observed'] or s['counts']['pa'] <= 0:
                continue
            c = events(s['counts']); weight = recency * c.sum()
            p = probability(c); env = references.get(league, s['season'], excluded)
            own += weight * p; environment += weight * env; exposure += weight
            observed.append(dict(season=s['season'], recency=recency, pa=float(c.sum()),
                                 counts=c.tolist(), probabilities=p.tolist(), reference=env.tolist()))
        if not exposure:
            continue
        total += exposure
        own /= exposure; environment /= exposure
        league_people = model['people_by_league'][league]
        predicted = None; source = clr(own) - clr(environment)
        if league_people:
            intercept = coef[:, LEAGUES.index(league)]
            relative = intercept + coef[:, 2] * source
            predicted = softmax(clr(mlb_reference) + relative - relative.mean())
            supported += exposure; weighted += exposure * predicted
        pieces.append(dict(league=league, recency_weighted_exposure=exposure,
                           mover_people=league_people, sparse_warning=league_people < 20,
                           own_pooled_probability=own.tolist(), pooled_reference=environment.tolist(),
                           source_relative_clr=source.tolist(), observed_seasons=observed,
                           translated_probability=predicted.tolist() if predicted is not None else None))
    translated = weighted / supported if supported else None
    if translated is not None and (not np.isclose(translated.sum(), 1) or (translated <= 0).any()):
        raise ValueError('Invalid coherent foreign profile')
    return dict(candidate_key=origin_input['candidate_key'], player_id=origin_input['player_id'],
                origin_year=origin, original_source_origin=origin_input['original_source_origin'],
                excluded_folds=excluded, raw_recent_foreign_pa=origin_input['recent_foreign_pa'],
                total_weighted_exposure=total, supported_weighted_exposure=supported,
                supported_fraction=supported / total if total else 0,
                MLB_reference=mlb_reference.tolist(), leagues=pieces,
                translated_probability=translated.tolist() if translated is not None else None,
                missing_translation=translated is None, forecast_eligibility_approved=False,
                new_workload_forecast=None, new_player_value_forecast=None)
