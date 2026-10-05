"""Dated status and nested overseas inputs; no outcome-based source decisions."""
from datetime import date

import numpy as np

from universal_baseball.mlb_event_logit import EVENTS

STATUS_FLAGS = ['status_major_link', 'status_minor_agreement', 'status_agreement_unspecified',
    'status_acquisition_only', 'status_released', 'status_employment_unknown',
    'status_employment_conflict', 'status_negative_listing_conflict',
    'status_positive_listing_conflict', 'status_finite_nonmedical',
    'status_unresolved_nonmedical', 'status_hard_unavailable',
    'status_medical_evidence_open', 'status_medical_scope_interrupted']
STATUS_EXTRA = ['employment_evidence_unknown', 'employment_evidence_age_years',
    'restriction_games_known', 'restriction_games', 'restriction_end_known',
    'restriction_end_days', 'return_report_known', 'return_report_days',
    'status_retired', 'availability_annual_coverage', 'medical_recent_spells',
    'medical_recent_days', 'medical_recent_surgery', 'mixed_role_uncertain']
STATUS_FEATURES = STATUS_FLAGS + STATUS_EXTRA
FOREIGN_FEATURES = [f'foreign_{league}_{lag}_{field}' for league in ['NPB', 'KBO']
    for lag in range(3) for field in ['pa', 'observed', 'unknown']]
FOREIGN_FEATURES += [f'foreign_{league}_{field}' for league in ['NPB', 'KBO']
    for field in ['weighted_pa', 'profile_present', 'mover_people', *['clr_'+e for e in EVENTS]]]
FOREIGN_FEATURES += ['foreign_recent_pa', 'foreign_profile_present', 'foreign_translation_missing',
    'foreign_supported_fraction', *['foreign_translated_'+e for e in EVENTS]]


def status_features(row, mixed=False):
    now = date.fromisoformat(row['information_date'])
    if now.year != row['origin_year']+1:
        raise ValueError('Mismatched status cutoff')
    employment, absence = row['employment'], row['absence']
    latest = employment['latest_date']
    age = (now-date.fromisoformat(latest)).days if latest else None
    if age is not None and age < 0:
        raise ValueError('Future employment evidence')
    out = {n: float(row[n]) for n in STATUS_FLAGS}
    out.update(employment_evidence_unknown=float(age is None),
        employment_evidence_age_years=min(age, 3650)/365 if age is not None else 0.,
        status_retired=float(absence['retired_evidence']),
        availability_annual_coverage=float(row['full_annual_availability_coverage']),
        mixed_role_uncertain=float(mixed))
    games = absence['original_duration_games']
    out.update(restriction_games_known=float(games is not None),
        restriction_games=min(games, 1000)/100 if games is not None else 0.)
    for source, prefix in [('known_calendar_end', 'restriction_end'), ('reported_return_date', 'return_report')]:
        end = absence[source]
        out[prefix+'_known'] = float(end is not None)
        out[prefix+'_days'] = np.clip((date.fromisoformat(end)-now).days, -365, 365)/365 if end else 0.
    report = absence.get('return_report')
    if report and date.fromisoformat(report['known_date']) > now:
        raise ValueError('Future return report')
    spells = [s for s in row['clinical_spells'] if date.fromisoformat(s['start']) <= now
        and (s['end'] is None or date.fromisoformat(s['end']) >= date(row['origin_year']-1, 1, 1))]
    days = 0
    for s in spells:
        start = max(date.fromisoformat(s['start']), date(row['origin_year']-1, 1, 1))
        end = date.fromisoformat(s['end']) if s['end'] else now
        if end > now:
            raise ValueError('Future medical closure')
        days += max(0, (end-start).days)
    out.update(medical_recent_spells=len(spells)/10, medical_recent_days=days/365,
        medical_recent_surgery=float(any(s['surgery'] for s in spells)))
    return out


def foreign_features(source, profile, *, origin, outer_fold, own_fold):
    out = {n: 0. for n in FOREIGN_FEATURES}
    if source is None:
        if profile is not None:
            raise ValueError('Profile without source')
        return out
    if source['origin_year'] != origin:
        raise ValueError('Wrong overseas origin')
    out['foreign_recent_pa'] = source['recent_foreign_pa']/600
    for league in ['NPB', 'KBO']:
        for lag in range(3):
            r = source['foreign_history_counts'][f'{league}_{lag}']
            if r['season'] != origin-lag:
                raise ValueError('Future or mismatched foreign counts')
            prefix = f'foreign_{league}_{lag}_'
            out[prefix+'pa'] = r['counts']['pa']/600
            out[prefix+'observed'] = float(r['player_identity_and_stat_observed'])
            out[prefix+'unknown'] = float(r['absent_group_is_not_certified_zero'])
    if profile is None or profile['origin_year'] != origin or profile['outer_fold'] != outer_fold:
        raise ValueError('Missing or wrong nested profile')
    if not {outer_fold, own_fold} <= set(profile['excluded_folds']):
        raise ValueError('Nested held-player contamination')
    if profile['candidate_key'] != source['candidate_key']:
        raise ValueError('Nested identity mismatch')
    out['foreign_profile_present'] = 1.
    out['foreign_translation_missing'] = float(profile['missing_translation'])
    out['foreign_supported_fraction'] = profile.get('supported_fraction', 0.)
    for r in profile['leagues']:
        prefix = 'foreign_'+r['league']+'_'
        out[prefix+'weighted_pa'] = r['recency_weighted_exposure']/600
        out[prefix+'profile_present'] = 1.
        out[prefix+'mover_people'] = r['mover_people']/20
        for e, v in zip(EVENTS, r['source_relative_clr'], strict=True):
            out[prefix+'clr_'+e] = float(v)
    if profile['translated_probability'] is not None:
        p = np.asarray(profile['translated_probability'])
        ref = np.asarray(profile['MLB_reference'])
        if not np.isfinite(p).all() or (p <= 0).any() or not np.isclose(p.sum(), 1):
            raise ValueError('Invalid translated component probabilities')
        for e, v in zip(EVENTS, p-ref, strict=True):
            out['foreign_translated_'+e] = float(v)
    if not np.isfinite(list(out.values())).all():
        raise ValueError('Nonfinite overseas inputs')
    return out
