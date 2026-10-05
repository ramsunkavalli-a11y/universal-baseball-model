"""Count-aware hitter inputs in fixed units, with no supervised fitted inputs.

Precision shares are a declared regularization design, not exact posterior
probabilities or empirically proven stabilization thresholds. Translation support
and observed PA are different quantities and are retained separately.
"""
from datetime import date

import numpy as np

from universal_baseball.hitter_talent_bridge import EVENTS, translated_probability

RECENCY = (1., .8, .6)
PRIOR_PA = 1200.
MINOR_FEATURES = [f'evidence_minor_{e}' for e in EVENTS[1:]] + [
    'evidence_minor_share', 'evidence_minor_supported_fraction', 'evidence_minor_missing']
FOREIGN_CONTROL_FEATURES = ['evidence_foreign_share', 'evidence_foreign_supported_fraction',
                            'evidence_foreign_missing', 'evidence_foreign_source_present']
FOREIGN_TALENT_FEATURES = [f'evidence_foreign_{e}' for e in EVENTS[1:]]
JOB_FEATURES = [f'professional_work_{lag}' for lag in range(3)] + [
    'professional_stat_gap', 'last_MLB_work', 'last_MLB_quality', 'last_MLB_lag',
    'last_MLB_known', 'last_first_team_work', 'last_first_team_lag',
    'last_first_team_known', 'returner_MLB_work', 'signed_first_team_work',
    'position_outfield_unspecified']


def _probability(value):
    p = np.asarray(value, dtype=float)
    if p.shape != (8,) or not np.isfinite(p).all() or (p < 0).any() or not np.isclose(p.sum(), 1):
        raise ValueError('Invalid coherent eight-event probability')
    return p


def information_share(exposure, mlb_exposure, other_exposure=0., *, prior_pa=PRIOR_PA):
    a = np.asarray([exposure, mlb_exposure, other_exposure, prior_pa], float)
    if not np.isfinite(a).all() or (a < 0).any() or prior_pa <= 0:
        raise ValueError('Invalid evidence mass')
    return float(exposure / a.sum())


def domestic_event_counts(row):
    n = float(row['plate_appearances'])
    known = np.array([row['strike_outs'], row['unintentional_walks'], row['hit_by_pitch'],
                      row['babip_hits'] - row['doubles'] - row['triples'],
                      row['doubles'], row['triples'], row['home_runs']], float)
    counts = np.r_[n - known.sum(), known]
    if not np.isfinite(counts).all() or (counts < 0).any() or not np.isclose(counts.sum(), n):
        raise ValueError('Invalid mutually exclusive domestic counts')
    return counts


def minor_evidence(history, graph, *, origin, mlb_exposure, foreign_exposure=0.):
    """Only translated non-MLB production; no duplicated raw lower-level rates."""
    if graph['cutoff'] != origin or graph['max_source_year'] > origin:
        raise ValueError('Wrong or future translation graph')
    ref = _probability(graph['mlb_reference'])
    weighted = np.zeros(8)
    observed = supported = 0.
    contributions = []
    for r in history:
        lag = origin - r['season']
        if not 0 <= lag < 3 or r['bucket'] == 'MLB':
            continue
        counts = domestic_event_counts(r)
        n = RECENCY[lag] * counts.sum()
        observed += n
        if n == 0 or r['bucket'] not in graph['offsets']:
            continue
        p = translated_probability(counts, np.asarray(graph['offsets'][r['bucket']]))
        weighted += n * p
        supported += n
        contributions.append(dict(season=r['season'], bucket=r['bucket'], actual_PA=float(counts.sum()),
                                  recency=RECENCY[lag], precision_PA=float(n), translated_probability=p.tolist()))
    share = information_share(supported, mlb_exposure, foreign_exposure)
    p = weighted / supported if supported else ref
    deviations = share * (p - ref) / .1
    result = dict(zip(MINOR_FEATURES[:7], map(float, deviations[1:]), strict=True))
    result.update(evidence_minor_share=share,
                  evidence_minor_supported_fraction=supported / observed if observed else 0.,
                  evidence_minor_missing=float(supported == 0))
    return result, dict(observed_precision_PA=observed, supported_precision_PA=supported,
                       MLB_precision_PA=mlb_exposure, foreign_precision_PA=foreign_exposure,
                       prior_PA=PRIOR_PA, information_share=share, contributions=contributions,
                       interpretation='Sample-share regularization; selected-mover translation, not full park/opponent adjustment')


def foreign_precision(source, *, origin):
    """Decode real PA with normalized recency, never use 5/4/3 units as precision."""
    if source is None:
        return 0., {l: 0. for l in ['NPB', 'KBO']}
    if source['origin_year'] != origin:
        raise ValueError('Wrong foreign source origin')
    amounts = {}
    for league in ['NPB', 'KBO']:
        n = 0.
        for lag, weight in enumerate(RECENCY):
            r = source['foreign_history_counts'][f'{league}_{lag}']
            if r['season'] != origin - lag:
                raise ValueError('Future or mismatched foreign history')
            pa = float(r['counts']['pa'])
            if not np.isfinite(pa) or pa < 0:
                raise ValueError('Invalid foreign counts')
            if pa > 0 and not r['player_identity_and_stat_observed']:
                raise ValueError('Positive foreign PA without observed identity')
            n += weight * pa
        amounts[league] = n
    return sum(amounts.values()), amounts


def foreign_evidence(source, profile, *, origin, outer_fold, own_fold, mlb_exposure, minor_exposure):
    result = {n: 0. for n in FOREIGN_CONTROL_FEATURES + FOREIGN_TALENT_FEATURES}
    total, by_league = foreign_precision(source, origin=origin)
    if source is None:
        if profile is not None:
            raise ValueError('Foreign profile without source')
        return result, dict(observed_precision_PA=0., supported_precision_PA=0., prior_PA=PRIOR_PA)
    result['evidence_foreign_source_present'] = 1.
    if profile is None or profile['candidate_key'] != source['candidate_key'] or profile['origin_year'] != origin:
        raise ValueError('Missing or mismatched foreign profile')
    if profile['outer_fold'] != outer_fold or not {own_fold, outer_fold} <= set(profile['excluded_folds']):
        raise ValueError('Foreign held-player contamination')
    ref = _probability(profile['MLB_reference'])
    weighted = np.zeros(8)
    supported = 0.
    used = []
    for r in profile['leagues']:
        n = by_league[r['league']]
        p = r.get('translated_probability')
        if n == 0 or p is None:
            continue
        weighted += n * _probability(p)
        supported += n
        used.append(dict(league=r['league'], precision_PA=n, mover_people=r['mover_people']))
    share = information_share(supported, mlb_exposure, minor_exposure)
    p = weighted / supported if supported else ref
    deviations = share * (p - ref) / .1
    result.update(dict(zip(FOREIGN_TALENT_FEATURES, map(float, deviations[1:]), strict=True)))
    result.update(evidence_foreign_share=share, evidence_foreign_supported_fraction=supported / total if total else 0.,
                  evidence_foreign_missing=float(supported == 0))
    return result, dict(observed_precision_PA=total, supported_precision_PA=supported,
                       MLB_precision_PA=mlb_exposure, minor_precision_PA=minor_exposure,
                       prior_PA=PRIOR_PA, information_share=share, source_leagues=used,
                       translated_probability=p.tolist() if supported else None,
                       interpretation='Normalized actual-count precision, not certainty of foreign translation')


def job_evidence(row, source):
    """Professional activity and old MLB role, not relabeled foreign MLB ability."""
    origin = row['origin_year']
    foreign_precision(source, origin=origin)
    out = {}
    first_team = []
    mlb = []
    foreign_last = []
    for lag in range(3):
        foreign = sum(float(source['foreign_history_counts'][f'{l}_{lag}']['counts']['pa'])
                      for l in ['NPB', 'KBO']) if source else 0.
        # Existing work_lag already applies the MLB short-season normalization.
        # Overseas PA are observed opportunities, not imputed full-season totals.
        work = float(row[f'work_{lag}'])
        total = work + foreign
        out[f'professional_work_{lag}'] = total / 600
        if work > 0:
            mlb.append((lag, work, float(row[f'quality_{lag}'])))
        if total > 0:
            first_team.append((lag, total))
        if foreign > 0:
            foreign_last.append(lag)
    out['professional_stat_gap'] = min([float(row['last_stat_gap']), *foreign_last]) / 5
    out.update(last_MLB_work=mlb[0][1]/600 if mlb else 0.,
               last_MLB_quality=mlb[0][2] if mlb else 0., last_MLB_lag=mlb[0][0]/3 if mlb else 0.,
               last_MLB_known=float(bool(mlb)), last_first_team_work=first_team[0][1]/600 if first_team else 0.,
               last_first_team_lag=first_team[0][0]/3 if first_team else 0., last_first_team_known=float(bool(first_team)))
    out['returner_MLB_work'] = out['last_MLB_work'] if row['pa_0'] == 0 else 0.
    linked = bool(row['status_major_link'] or row['on_40man'] or row['status_agreement_unspecified'])
    out['signed_first_team_work'] = out['last_first_team_work'] if linked else 0.
    codes = set(source['roster_hitter_codes']) if source else set()
    out['position_outfield_unspecified'] = float('O' in codes and not codes & {'7', '8', '9'})
    if not np.isfinite(list(out.values())).all():
        raise ValueError('Nonfinite job evidence')
    return out


def check_cutoff(row, source):
    now = date.fromisoformat(row['ctx_information_date'])
    if now.year != row['origin_year'] + 1 or row['target_year'] != now.year:
        raise ValueError('Mismatched forecast date')
    if source is not None and (source['origin_year'] != row['origin_year'] or source['information_date'] != now.isoformat()):
        raise ValueError('Mismatched foreign information date')
