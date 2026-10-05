"""Past-only production pool and symmetric eight-event future count likelihood.

Foreign within-league skill is provisional, not an established MLB equivalency.
The archived future prediction is deliberately never read by this module.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from universal_baseball.hitter_evidence_representation import RECENCY, domestic_event_counts, foreign_precision
from universal_baseball.hitter_talent_bridge import EVENTS, translated_probability
from universal_baseball.foreign_component_translation import events
from universal_baseball.hitter_shared_production import probability, reanchor

PRIOR = 1200.
FEATURES = [f'count_past_{e}' for e in EVENTS] + [
    'count_log_exposure', 'count_reliability', 'count_missing',
    'count_minor_share', 'count_NPB_share', 'count_KBO_share', 'count_supported_fraction']


def assemble(contributions, reference, observed, *, remove=None):
    ref = probability(reference); num = PRIOR * ref.copy(); mass = 0.
    groups = dict(MLB=0., minor=0., NPB=0., KBO=0.)
    for c in contributions:
        if c['source'] == remove or (remove == 'foreign' and c['source'] in {'NPB', 'KBO'}):
            continue
        n = float(c['precision_PA'])
        if not np.isfinite(n) or n < 0:
            raise ValueError('Invalid source mass')
        num += n * probability(c['probability']); mass += n; groups[c['source']] += n
    p = probability(num / (PRIOR + mass))
    z = np.log(p / ref); z -= z.mean()
    out = dict(zip(FEATURES[:8], map(float, z), strict=True))
    out.update(count_log_exposure=float(np.log1p(mass)/np.log(1201)),
        count_reliability=mass/(PRIOR+mass), count_missing=float(mass == 0),
        count_minor_share=groups['minor']/(PRIOR+mass),
        count_NPB_share=groups['NPB']/(PRIOR+mass), count_KBO_share=groups['KBO']/(PRIOR+mass),
        count_supported_fraction=mass/observed if observed else 0.)
    if not np.isfinite(list(out.values())).all() or observed + 1e-8 < mass:
        raise ValueError('Invalid evidence coverage')
    return out, p


def past_profile(history, graph, source, archived, *, origin, outer_fold, own_fold):
    if graph['cutoff'] != origin or graph['max_source_year'] > origin:
        raise ValueError('Future or mismatched graph')
    excluded = set(graph['excluded_folds'])
    if not {outer_fold, own_fold} <= excluded:
        raise ValueError('Domestic source contamination')
    ref = probability(graph['mlb_reference']); contributions=[]; observed=0.
    for r in history:
        lag = origin-r['season']
        if not 0 <= lag < 3:
            continue
        c = domestic_event_counts(r); n = RECENCY[lag]*c.sum(); observed += n
        if n <= 0 or r['bucket'] not in graph['offsets']:
            continue
        p = translated_probability(c, np.asarray(graph['offsets'][r['bucket']]))
        contributions.append(dict(source='MLB' if r['bucket']=='MLB' else 'minor',
            season=r['season'], bucket=r['bucket'], actual_PA=float(c.sum()),
            precision_PA=float(n), counts=c.tolist(), probability=p.tolist(),
            meaning='same-season domestic level equivalency'))
    total, amounts = foreign_precision(source, origin=origin); observed += total
    if source is not None:
        if archived is None or archived['candidate_key'] != source['candidate_key'] or archived['origin_year'] != origin:
            raise ValueError('Missing or mismatched raw foreign archive')
        if archived['outer_fold'] != outer_fold or not {outer_fold, own_fold} <= set(archived['excluded_folds']):
            raise ValueError('Foreign source contamination')
        for league, n in amounts.items():
            if n == 0:
                continue
            piece = next(r for r in archived['leagues'] if r['league'] == league)
            own = np.zeros(8); env = np.zeros(8); audit=[]; mass=0.
            for lag, w in enumerate(RECENCY):
                raw = source['foreign_history_counts'][f'{league}_{lag}']
                c = events(raw['counts'])
                if c.sum() == 0:
                    continue
                season = origin-lag
                a = next(r for r in piece['observed_seasons'] if r['season'] == season)
                p = (c+.5)/(c.sum()+4); reference = probability(a['reference'])
                if not np.array_equal(c, a['counts']) or not np.isclose(c.sum(), a['pa']):
                    raise ValueError('Foreign raw count pairing failed')
                if not np.allclose(p, a['probabilities'], atol=1e-12) or not np.isclose(a['recency'], 5*w):
                    raise ValueError('Foreign raw probability reconstruction failed')
                own += w*c.sum()*p; env += w*c.sum()*reference; mass += w*c.sum()
                audit.append(dict(season=season, counts=c.tolist(), reference=reference.tolist(), recency=w))
            if not np.isclose(mass, n):
                raise ValueError('Foreign exposure mismatch')
            own /= n; env /= n
            if not np.allclose(own, piece['own_pooled_probability'], atol=1e-12) or not np.allclose(env, piece['pooled_reference'], atol=1e-12):
                raise ValueError('Past archive reconstruction failed')
            p = reanchor(own, env, ref)
            contributions.append(dict(source=league, bucket=league, precision_PA=n,
                probability=p.tolist(), own_probability=own.tolist(), local_reference=env.tolist(),
                observed_seasons=audit, archived_mover_people=piece['mover_people'],
                meaning='past within-league relative skill; MLB adaptation not yet learned'))
    out, p = assemble(contributions, ref, observed)
    return out, dict(reference=ref.tolist(), past_probability=p.tolist(),
        observed_precision_PA=float(observed), prior_PA=PRIOR, contributions=contributions,
        excluded_folds=sorted(excluded), cutoff=origin, future_foreign_probabilities_used=False)


def probabilities(beta, x, offset):
    aug = np.column_stack([np.ones(len(x)), x])
    logits = offset + aug @ beta
    return np.exp(logits-logsumexp(logits, axis=1, keepdims=True))


def objective(flat, aug, counts, offset, penalty=.001):
    beta = flat.reshape(aug.shape[1], 8)
    logits = offset + aug @ beta
    logp = logits-logsumexp(logits, axis=1, keepdims=True); p=np.exp(logp)
    scale = counts.sum()
    value = -np.sum(counts*logp)/scale + penalty*np.sum(beta[1:]**2)/2
    grad = aug.T @ (p*counts.sum(1,keepdims=True)-counts)/scale
    grad[1:] += penalty*beta[1:]
    return float(value), grad.ravel()


def fit(x, counts, offset, weights):
    if not np.isfinite(x).all() or not np.isfinite(offset).all() or (counts<0).any():
        raise ValueError('Invalid model inputs')
    if counts.shape != offset.shape or counts.shape[1] != 8 or counts.sum() <= 0:
        raise ValueError('Invalid target counts')
    if not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError('Invalid row weights')
    aug = np.column_stack([np.ones(len(x)), x]); weighted=counts*weights[:,None]
    res = minimize(objective, np.zeros(aug.shape[1]*8), args=(aug,weighted,offset), jac=True,
        method='L-BFGS-B', options={'maxiter':1000,'ftol':1e-10,'gtol':1e-6})
    if not res.success:
        raise RuntimeError(f'Count fit did not converge: {res.message}')
    beta = res.x.reshape(aug.shape[1],8)
    if not np.allclose(beta.sum(1), 0, atol=1e-7):
        raise RuntimeError('Symmetric coefficient identification failed')
    return dict(beta=beta, optimizer=dict(success=True, message=str(res.message),
        iterations=int(res.nit), objective=float(res.fun), maximum_gradient=float(abs(res.jac).max())))
