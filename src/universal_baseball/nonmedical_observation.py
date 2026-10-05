"""Separate captured legal evidence from demonstrably interrupted MLB absence.

Positive windows are observations, not reinstatements or clinical clearance.
The caller must supply a verified, cutoff-replayed legal ledger.
"""
from copy import deepcopy
from datetime import date


def _day(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


def continuing_absence(player_id, absence, windows, cutoff, covered_years):
    cutoff = _day(cutoff)
    active = absence.get('active_restrictions', {})
    eligible = []
    for raw in windows:
        if raw['player_id'] != player_id:
            raise ValueError('Appearance window belongs to another player')
        start, end = _day(raw['start']), _day(raw['end'])
        if start > end:
            raise ValueError('Reversed appearance window')
        pa = raw['pa']
        if pa < 0 or int(pa) != pa:
            raise ValueError('Invalid PA count')
        # The period end, not its beginning, bounds availability of its total.
        known = _day(raw.get('available_date', raw['end']))
        if known < end:
            raise ValueError('Window total available before period ends')
        if known <= cutoff and end <= cutoff and pa > 0:
            eligible.append(raw)
    for record in active.values():
        if _day(record['event_date']) > cutoff:
            raise ValueError('Legal state was not replayed to this cutoff')
    observed = {}
    hard_conflicts = {}
    unresolved = deepcopy(active)
    for scope, record in sorted(active.items()):
        after = [w for w in eligible if _day(w['start']) > _day(record['event_date'])]
        if not after:
            continue
        first = min(after, key=lambda w: (_day(w['end']),
            (_day(w['end']) - _day(w['start'])).days, w['label']))
        evidence = dict(restriction=deepcopy(record), window=deepcopy(first),
            observed_return_upper=first['end'], exact_return_date_known=False,
            legal_reinstatement_certified=False, medical_recovery_certified=False)
        if record['kind'] in {'deceased', 'permanent_ineligible'}:
            hard_conflicts[scope] = evidence
        else:
            observed[scope] = evidence
            del unresolved[scope]
    finite = [r for r in unresolved.values() if r.get('duration_games') or r.get('calendar_end')]
    games = [r for r in unresolved.values() if r.get('duration_games')]
    ends = [r['calendar_end'] for r in unresolved.values() if r.get('calendar_end')]
    report = absence.get('return_report') if 'suspended' in unresolved else None
    # These explicit source flags are not a fitted model's replacement inputs.
    uncertainty = any(r.get('ambiguous') or r['kind'] in {
        'restricted', 'administrative_leave', 'ineligible_unspecified'} or
        r['kind'] == 'suspended_unspecified' and not r.get('duration_games')
        for r in unresolved.values())
    return dict(captured_legal_state=absence['state'],
        captured_active_restrictions=deepcopy(active),
        observation_unresolved_channels=unresolved,
        channels_with_subsequent_observed_MLB_use=observed,
        hard_status_activity_conflicts=hard_conflicts,
        legal_reinstatement_certified=False, medical_recovery_certified=False,
        absence_continuity_certified=False,
        appearance_capture_years=[y for y in sorted(set(covered_years))
                                  if y <= cutoff.year],
        absence_of_positive_window_means_unavailable=False,
        observation_finite_nonmedical=bool(finite),
        observation_unresolved_nonmedical=uncertainty,
        hard_unavailable=absence['hard_unavailable'],
        unresolved_original_duration_games=games[0]['duration_games'] if len(games) == 1 else None,
        unresolved_known_calendar_end=max(ends) if ends else None,
        unresolved_return_report=deepcopy(report),
        current_return_date=absence.get('reported_return_date') if report else None)
