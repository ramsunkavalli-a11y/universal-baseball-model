"""Shared, same-horizon event evidence with separated exposure information."""
import numpy as np

from .hitter_talent_bridge import EVENTS, translated_probability
from .hitter_evidence_representation import RECENCY, domestic_event_counts, foreign_precision
from .foreign_component_translation import clr, softmax

PROFILE = [f'shared_{e}' for e in EVENTS] + [
    'shared_log_exposure', 'shared_supported_fraction', 'shared_reliability', 'shared_missing']


def rebase(probability, old_reference, new_reference):
    """Preserve the relative log fingerprint, not a potentially negative delta."""
    return softmax(clr(new_reference) + clr(probability) - clr(old_reference))


def profile(history, graph, calibration, foreign_source, foreign_profile, *, origin, outer_fold, own_fold):
    excluded = {outer_fold, own_fold}
    if graph['cutoff'] != origin or graph['held_fold'] != outer_fold or graph['max_source_year'] > origin:
        raise ValueError('Wrong domestic graph cutoff or fold')
    if calibration['cutoff'] != origin or calibration['max_target_year'] > origin or not excluded <= set(calibration['excluded_folds']):
        raise ValueError('Future or held-player persistence fit')
    reference = np.asarray(graph['mlb_reference'], float)
    clr(reference)  # validate reference
    total_us = supported_us = 0.
    pooled = np.zeros(8)
    pieces = []
    for r in history:
        lag = origin - r['season']
        if not 0 <= lag < 3:
            continue
        counts = domestic_event_counts(r)
        mass = RECENCY[lag] * counts.sum()
        total_us += mass
        if mass <= 0 or r['bucket'] not in graph['offsets']:
            continue
        p = translated_probability(counts, np.asarray(graph['offsets'][r['bucket']]))
        supported_us += mass
        pooled += mass * p
        pieces.append(dict(season=r['season'], bucket=r['bucket'], actual_PA=float(counts.sum()),
                           precision_PA=float(mass), probability=p.tolist()))
    past = pooled / supported_us if supported_us else reference.copy()
    a = np.asarray(calibration['domestic_intercepts'])
    b = np.asarray(calibration['domestic_slopes'])
    domestic = softmax(clr(reference) + a + b * (clr(past) - clr(reference))) if supported_us else reference.copy()
    observed_foreign, by_league = foreign_precision(foreign_source, origin=origin)
    supported_foreign = 0.
    foreign_sum = np.zeros(8)
    foreign_pieces = []
    if foreign_source is not None:
        if foreign_profile is None or foreign_profile['candidate_key'] != foreign_source['candidate_key'] or foreign_profile['origin_year'] != origin:
            raise ValueError('Missing or wrong foreign profile')
        if foreign_profile['outer_fold'] != outer_fold or not excluded <= set(foreign_profile['excluded_folds']):
            raise ValueError('Foreign held-player contamination')
        for r in foreign_profile['leagues']:
            mass = by_league[r['league']]
            if mass <= 0 or r['translated_probability'] is None:
                continue
            aligned = rebase(r['translated_probability'], foreign_profile['MLB_reference'], reference)
            supported_foreign += mass
            foreign_sum += mass * aligned
            foreign_pieces.append(dict(league=r['league'], precision_PA=mass, mover_people=r['mover_people'],
                native_probability=r['translated_probability'], aligned_probability=aligned.tolist()))
    elif foreign_profile is not None:
        raise ValueError('Foreign profile without source')
    supported = supported_us + supported_foreign
    observed = total_us + observed_foreign
    combined = (supported_us * domestic + foreign_sum) / supported if supported else reference.copy()
    controls = dict(shared_log_exposure=float(np.log1p(supported)/np.log(1201)),
        shared_supported_fraction=supported/observed if observed else 0.,
        shared_reliability=supported/(supported+1200), shared_missing=float(supported == 0))
    arms = {}
    for name, p in [('domestic', domestic), ('foreign', combined)]:
        clr(p)
        d = (p-reference)/.1
        assert abs(d.sum()) < 1e-10
        arms[name] = {**dict(zip(PROFILE[:8], map(float,d), strict=True)), **controls}
    note = dict(reference=reference.tolist(), US_observed_PA=total_us, US_supported_PA=supported_us,
        foreign_observed_PA=observed_foreign, foreign_supported_PA=supported_foreign,
        foreign_share=supported_foreign/supported if supported else 0., source_pieces=pieces,
        past_US_probability=past.tolist(), future_US_probability=domestic.tolist(),
        future_shared_probability=combined.tolist(), foreign_pieces=foreign_pieces,
        persistence_intercepts=a.tolist(), persistence_slopes=b.tolist(),
        persistence_excluded_folds=calibration['excluded_folds'],
        persistence_people=calibration['domestic_people'],
        interpretation='Shared predicted next-year events; conditional persistence transport, not park-neutral latent talent')
    return arms, note
