"""Coherent source pooling; shared production coordinates, not source-specific slopes."""
import numpy as np
from universal_baseball.hitter_talent_bridge import EVENTS, clr, translated_probability
from universal_baseball.hitter_evidence_representation import RECENCY, domestic_event_counts, foreign_precision

FEATURES = [f'shared_event_{e}' for e in EVENTS] + [
    'shared_log_exposure', 'shared_reliability', 'shared_missing',
    'shared_minor_share', 'shared_foreign_share', 'shared_supported_fraction']
PRIOR = 1200.


def probability(value):
    p = np.asarray(value, float)
    if p.shape != (8,) or not np.isfinite(p).all() or (p <= 0).any() or not np.isclose(p.sum(), 1):
        raise ValueError('Invalid positive coherent probability')
    return p


def reanchor(p, source_reference, common_reference):
    z = clr(probability(p)) - clr(probability(source_reference)) + clr(probability(common_reference))
    z -= z.max()
    out = np.exp(z); out /= out.sum()
    return probability(out)


def assemble(contributions, reference, observed, *, remove=None):
    ref = probability(reference); numerator = PRIOR * ref.copy(); mass = 0.
    groups = {'MLB': 0., 'minor': 0., 'foreign': 0.}
    for c in contributions:
        if c['source'] == remove:
            continue
        n = float(c['precision_PA'])
        if not np.isfinite(n) or n < 0:
            raise ValueError('Invalid PA precision')
        numerator += n * probability(c['probability']); mass += n; groups[c['source']] += n
    p = numerator / (PRIOR + mass)
    contrast = (p - ref) / .1
    result = dict(zip(FEATURES[:8], map(float, contrast), strict=True))
    result.update(shared_log_exposure=float(np.log1p(mass)/np.log(1201)),
        shared_reliability=mass/(PRIOR+mass), shared_missing=float(mass == 0),
        shared_minor_share=groups['minor']/(PRIOR+mass),
        shared_foreign_share=groups['foreign']/(PRIOR+mass),
        shared_supported_fraction=mass/observed if observed else 0.)
    if not np.isfinite(list(result.values())).all() or abs(contrast.sum()) > 1e-10:
        raise ValueError('Invalid shared profile')
    return result


def profile(history, graph, source, foreign, *, origin, outer_fold, own_fold):
    if graph['cutoff'] != origin or graph['max_source_year'] > origin:
        raise ValueError('Future or wrong domestic graph')
    excluded = set(graph['excluded_folds'])
    if not {outer_fold, own_fold} <= excluded:
        raise ValueError('Domestic fold contamination')
    ref = probability(graph['mlb_reference']); contributions=[]; observed=0.
    for r in history:
        lag=origin-r['season']
        if not 0 <= lag < 3:
            continue
        counts=domestic_event_counts(r); n=RECENCY[lag]*counts.sum(); observed += n
        if n <= 0 or r['bucket'] not in graph['offsets']:
            continue
        p=translated_probability(counts, np.asarray(graph['offsets'][r['bucket']]))
        contributions.append(dict(source='MLB' if r['bucket']=='MLB' else 'minor',
            season=r['season'], bucket=r['bucket'], actual_PA=float(counts.sum()),
            precision_PA=float(n), probability=p.tolist()))
    total, amounts=foreign_precision(source, origin=origin); observed += total
    if source is not None:
        if foreign is None or foreign['candidate_key'] != source['candidate_key'] or foreign['origin_year'] != origin:
            raise ValueError('Missing foreign profile')
        if foreign['outer_fold'] != outer_fold or not {outer_fold, own_fold} <= set(foreign['excluded_folds']):
            raise ValueError('Foreign fold contamination')
        for r in foreign['leagues']:
            n=amounts[r['league']]
            if n <= 0 or r.get('translated_probability') is None:
                continue
            p=reanchor(r['translated_probability'], foreign['MLB_reference'], ref)
            contributions.append(dict(source='foreign', bucket=r['league'], precision_PA=n,
                mover_people=r['mover_people'], probability=p.tolist(),
                original_probability=r['translated_probability']))
    note=dict(reference=ref.tolist(), observed_precision_PA=float(observed), prior_PA=PRIOR,
        contributions=contributions, excluded_folds=sorted(excluded), cutoff=origin)
    return assemble(contributions, ref, observed), note
