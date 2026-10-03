"""Bound reported roster absence using known transactions and actual MLB use.

No clinical recovery or exact return date is inferred from aggregate PA.
Inputs are the frozen normalized historical records, not fresh model outcomes.
"""
from datetime import date
import re


def as_of(records, cutoff):
    selected = {}
    for raw in records:
        row = dict(raw)
        for name in ('available_date', 'event_date'):
            if isinstance(row[name], str):
                row[name] = date.fromisoformat(row[name])
        if row['available_date'] > cutoff:
            continue
        if row['event_date'] > row['available_date']:
            raise ValueError('Occurrence is after availability')
        key = row['transaction_id'], row['player_id']
        old = selected.get(key)
        if old and old['available_date'] == row['available_date'] and (
                old['description'], old['event_date']) != (
                row['description'], row['event_date']):
            raise ValueError('Conflicting eligible transaction versions')
        if old is None or old['available_date'] < row['available_date']:
            selected[key] = row
    return sorted(selected.values(), key=lambda r: (
        r['event_date'], r['available_date'], r['transaction_id'] < 0,
        r['transaction_id']))


def safe_roster_return(row):
    if row.get('il_kind') == 'activation':
        return True
    if re.search(r'\b(paternity|bereavement|restricted|administrative|suspended|all[- ]?stars?)\b',
                 row['description'].lower()):
        return False
    return row['kind'] in {'mlb_return', 'mlb_activation'}


def reconcile(records, windows, cutoff):
    """Replay medical intervals; positive disjoint windows bound a roster return.

    The lower absence bound is deliberately not the start of an observed window:
    missing activations might mean the player returned much earlier.
    """
    events = [(r['event_date'], 0, r) for r in as_of(records, cutoff)]
    for raw in windows:
        row = dict(raw)
        for name in ('start', 'end'):
            if isinstance(row[name], str):
                row[name] = date.fromisoformat(row[name])
        if row['start'] > row['end']:
            raise ValueError('Reversed observation window')
        if row['end'] <= cutoff and row['pa'] > 0:
            events.append((row['end'], 1, row))
    events.sort(key=lambda x: (x[0], x[1]))
    spells = []
    current = None
    interrupts = {'scope_exit', 'retired', 'deceased', 'restricted',
                  'administrative_leave', 'ineligible_unspecified',
                  'suspended_unspecified', 'permanent_ineligible',
                  'finite_ineligible', 'foreign_departure'}
    for day, kind, row in events:
        if kind == 1:
            if current is not None and current['latest_entry'] < row['start']:
                current.update(open_observation=False, end_upper=day,
                    closure_kind='observed_MLB_PA_window',
                    closure_known_by=day, return_window_start=row['start'],
                    return_window_end=day, exact_return_date_known=False)
                current = None
            continue
        il = row.get('il_kind')
        if il in {'placement', 'transfer'}:
            if current is None:
                current = dict(start=day, latest_entry=day, end_upper=cutoff,
                    open_observation=True, transaction_ids=[], categories=[],
                    surgery=False, closure_kind=None, closure_known_by=None,
                    return_window_start=None, return_window_end=None,
                    exact_return_date_known=False, medical_recovery_certified=False,
                    duration_is_upper_bound=True)
                spells.append(current)
            current['latest_entry'] = day
            current['transaction_ids'].append(row['transaction_id'])
            if row.get('category') not in current['categories']:
                current['categories'].append(row.get('category', 'unspecified'))
            current['surgery'] |= bool(row.get('surgery'))
        elif current is not None and safe_roster_return(row):
            current.update(open_observation=False, end_upper=day,
                closure_known_by=row['available_date'],
                closure_kind='named_IL_activation' if il == 'activation'
                    else 'reported_MLB_roster_return',
                exact_return_date_known=False)
            # This is a reported roster event, not a known first game back or
            # certified continuous absence until that event.
            current = None
        elif current is not None and row['kind'] in interrupts:
            current.update(open_observation=False, end_upper=day,
                closure_known_by=row['available_date'],
                closure_kind='observation_scope_exit')
            current = None
    return spells
