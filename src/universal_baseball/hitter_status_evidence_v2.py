"""Independent list scopes; preserve the sealed first status implementation."""
from collections import defaultdict
from datetime import date

from .availability_context_v29 import as_of
from .hitter_status_evidence import reconcile as original_reconcile

RESTRICTIONS = {'suspended_unspecified': 'suspended', 'restricted': 'restricted',
    'administrative_leave': 'administrative', 'ineligible_unspecified': 'ineligible',
    'finite_ineligible': 'ineligible', 'permanent_ineligible': 'ineligible', 'deceased': 'deceased'}


def clear_scope(record):
    text = record['description'].lower()
    if record['kind'] not in {'nonmedical_activation', 'reinstated'}:
        return None
    scopes = [name for word, name in [('restricted', 'restricted'), ('administrative', 'administrative'),
        ('suspended', 'suspended'), ('suspension', 'suspended'), ('ineligible', 'ineligible')]
        if word in text]
    scopes = set(scopes)
    return next(iter(scopes)) if len(scopes) == 1 else None


def displayed_state(active, reinstated):
    if 'deceased' in active: return 'deceased'
    if any(r['kind'] == 'permanent_ineligible' for r in active.values()): return 'permanent_ineligible'
    if any(r.get('ambiguous') for r in active.values()): return 'ambiguous_same_date_restriction'
    if any(r.get('duration_games') for r in active.values()): return 'finite_game_suspension'
    if any(r.get('calendar_end') for r in active.values()): return 'finite_calendar_ineligibility'
    if set(active) == {'suspended'}: return 'suspension_unspecified'
    if active: return 'unresolved_nonmedical'
    return 'reported_nonmedical_reinstatement' if reinstated else 'no_captured_restriction'


def absence_state(records, cutoff, return_reports=()):
    groups = defaultdict(list)
    for r in as_of(records, cutoff): groups[r['event_date']].append(r)
    active = {}; retired = False; reinstated = False; trace = []; unscoped = []
    for day, group in sorted(groups.items()):
        restricted = defaultdict(list); cleared = defaultdict(list)
        for r in group:
            if r['kind'] in RESTRICTIONS: restricted[RESTRICTIONS[r['kind']]].append(r)
            if r['kind'] in {'reinstated', 'nonmedical_activation'}:
                scope = clear_scope(r)
                if scope: cleared[scope].append(r)
                else: unscoped.append(dict(date=day.isoformat(), transaction_id=r['transaction_id'], description=r['description']))
            plain = r['kind'] == 'mlb_activation' and r.get('il_kind') != 'activation' and not any(
                word in r['description'].lower() for word in ['injured', 'disabled', 'paternity', 'bereavement', 'restricted', 'administrative'])
            if plain: cleared['suspended'].append(r)
        before = {k: dict(v) for k, v in active.items()}
        for scope in sorted(set(restricted) | set(cleared)):
            additions = restricted.get(scope, []); removals = cleared.get(scope, [])
            if scope == 'deceased':
                if additions: active[scope] = dict(kind='deceased', event_date=day.isoformat(), ambiguous=False)
                continue
            if additions:
                # Explicit finite/permanent facts refine same-day generic status.
                chosen = max(additions, key=lambda r: (r['kind'] == 'permanent_ineligible',
                    r['kind'] == 'finite_ineligible', bool(r.get('duration_games'))))
                if active.get(scope, {}).get('kind') == 'permanent_ineligible':
                    chosen = dict(chosen, kind='permanent_ineligible')
                info = dict(kind=chosen['kind'], event_date=day.isoformat(), ambiguous=bool(removals))
                if chosen.get('duration_games'): info['duration_games'] = chosen['duration_games']
                if chosen['kind'] == 'finite_ineligible':
                    durations = {int(r['duration_years']) for r in additions if r['kind'] == 'finite_ineligible'}
                    if len(durations) != 1: raise ValueError('Conflicting calendar durations')
                    try: end = day.replace(year=day.year + next(iter(durations)))
                    except ValueError: end = day.replace(year=day.year + next(iter(durations)), day=28)
                    info['calendar_end'] = end.isoformat()
                active[scope] = info
            elif removals and scope in active:
                permanent = active[scope]['kind'] == 'permanent_ineligible'
                legal = any(r['kind'] == 'reinstated' and clear_scope(r) == 'ineligible' for r in removals)
                if not permanent or legal:
                    del active[scope]; reinstated = True
        kinds = {r['kind'] for r in group}
        if 'retired' in kinds: retired = True
        elif kinds & {'org_acquisition', 'minor_contract', 'foreign_return_signing'}: retired = False
        if active != before or restricted or any(k in {'reinstated', 'nonmedical_activation', 'retired'} for k in kinds):
            trace.append(dict(date=day.isoformat(), kinds=sorted(kinds), state=displayed_state(active, reinstated),
                active_channels=sorted(active), clearing_scopes=sorted(cleared)))
    elapsed = []
    for scope, r in list(active.items()):
        if r.get('calendar_end') and cutoff >= date.fromisoformat(r['calendar_end']):
            elapsed.append(r); del active[scope]
    state = displayed_state(active, reinstated)
    if elapsed and not active: state = 'finite_end_elapsed_return_unconfirmed'
    games = [r for r in active.values() if r.get('duration_games')]
    ends = [r['calendar_end'] for r in active.values() if r.get('calendar_end')]
    matching_reports = [r for r in return_reports if date.fromisoformat(r['known_date']) <= cutoff
        and date.fromisoformat(r['event_date']) <= cutoff and 'suspended' in active
        and active['suspended'].get('duration_games') and r['event_date'] == active['suspended']['event_date']]
    report = max(matching_reports, key=lambda r: r['known_date']) if matching_reports else None
    return dict(state=state, original_duration_games=games[0]['duration_games'] if len(games) == 1 else None,
        known_calendar_end=max(ends) if ends else None, reported_return_date=report['reported_return_date'] if report else None,
        return_report=report, retired_evidence=retired,
        hard_unavailable='deceased' in active or any(r['kind'] == 'permanent_ineligible' for r in active.values()),
        active_restrictions=active, elapsed_finite_restrictions=elapsed, unscoped_return_evidence=unscoped, trace=trace)


def reconcile(population_row, raw_events, records, teams, return_reports=()):
    row = original_reconcile(population_row, raw_events, records, teams, return_reports)
    absence = absence_state(records, date.fromisoformat(population_row['information_date']), return_reports)
    row['absence'] = absence
    row['status_hard_unavailable'] = absence['hard_unavailable']
    row['status_finite_nonmedical'] = any(r.get('duration_games') or r.get('calendar_end')
        for r in absence['active_restrictions'].values())
    row['status_unresolved_nonmedical'] = any(r.get('ambiguous') or r['kind'] in {
        'restricted', 'administrative_leave', 'ineligible_unspecified'} or
        r['kind'] == 'suspended_unspecified' and not r.get('duration_games')
        for r in absence['active_restrictions'].values())
    return row
