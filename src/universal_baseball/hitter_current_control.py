"""Scoped service replay for the dated hitter release, not PA-derived service."""
import re
from datetime import timedelta
import polars as pl
from universal_baseball.control_events import classify_control_transactions, OPENING_CONTROL_STATE_SCHEMA


def service_events(transactions, mlb_team_ids):
    """Other-team activations must not replace an MLB service state."""
    events = classify_control_transactions(transactions, mlb_team_ids=mlb_team_ids).to_dicts()
    source = {(r['player_id'], r['transaction_id']):r for r in transactions.to_dicts()}
    for event in events:
        row = source[event['player_id'], event['transaction_id']]
        text = ' '.join(row['description'].lower().split())
        direct = row['from_team_id'] in mlb_team_ids or row['to_team_id'] in mlb_team_ids
        if re.search(r'\belected free agency\b',text):
            event.update(action='close_state',target_state=None,rule_id='description.elected_free_agency.v1',
                         reason='Explicit election ends service state; contract liability is separate.')
        elif not direct:
            event.update(action='preserve_state',target_state=None,rule_id='scope.non_MLB_service_preserve.v1',
                         reason='Non-MLB event cannot replace MLB service/option status.')
    return pl.DataFrame(events,schema=classify_control_transactions(transactions.head(0),mlb_team_ids=mlb_team_ids).schema)


def resolve_selection_option_pairs(events, transactions):
    """Selection to the 40-man list is not activation when immediately optioned."""
    rows=events.to_dicts()
    codes={}
    for r in transactions.to_dicts():
        codes.setdefault((r['player_id'],r['effective_date']),set()).add(r['type_code'])
    for r in rows:
        day_codes=codes.get((r['player_id'],r['event_date']),set())
        if r['rule_id']=='type.SE.v1' and {'SE','OPT'}<=day_codes and not {'CU','RE'}&day_codes:
            r.update(action='preserve_state',target_state=None,rule_id='selection_with_same_day_option.v1',
                reason='Same-day selection plus option establishes 40-man membership, not MLB active service.')
    return pl.DataFrame(rows,schema=events.schema)


def service_bounds(intervals, events, start, end, opening_known):
    """Bound uncertain state segments; the 172-day cap may resolve a balance."""
    active=set()
    for r in intervals:
        if r['roster_state'] in ('mlb_active','mlb_injured','mlb_service_list'):
            day=max(start,r['start_date'])
            while day<=min(end,r['end_date']):active.add(day);day+=timedelta(days=1)
    by_day={}
    for r in events:
        if start<=r['event_date']<=end:by_day.setdefault(r['event_date'],[]).append(r)
    uncertain=set();unknown=not opening_known;day=start
    while day<=end:
        rr=by_day.get(day,[])
        changes=[r for r in rr if r['action'] in ('set_state','close_state')]
        states={r['target_state'] in ('mlb_active','mlb_injured','mlb_service_list') for r in changes}
        if len(states)>1 or any(r['action']=='review' for r in rr):unknown=True
        elif changes:unknown=False
        if unknown:uncertain.add(day)
        day+=timedelta(days=1)
    return min(172,len(active-uncertain)),min(172,len(active|uncertain)),len(uncertain)


def service_openings(roster_openings, events, roster_entries, season, start):
    """Use dated conclusive events when terminal roster statuses lose history."""
    existing={r['player_id']:r for r in roster_openings.to_dicts()}
    entries={}
    for r in roster_entries.to_dicts():
        if r['start_date']<=start and (r['end_date'] is None or r['end_date']>=start):
            entries[r['player_id']]=max(entries.get(r['player_id'],r['start_date']),r['start_date'])
    last={}
    for r in sorted(events.to_dicts(),key=lambda r:(r['event_date'],r['transaction_id'])):
        if r['event_date']<=start and r['action'] in ('set_state','close_state'):
            last[r['player_id']]=r
    provenance=[]
    for pid,event in last.items():
        if pid not in existing or event['event_date']>=entries.get(pid,event['event_date']):
            state=event['target_state'] if event['action']=='set_state' else 'pro_inactive'
            existing[pid]=dict(player_id=pid,season=season,roster_state=state,
                               source_snapshot_id=event['source_snapshot_id'])
            provenance.append(dict(player_id=pid,opening_state=state,transaction_id=event['transaction_id'],
                                   event_date=event['event_date'],rule_id=event['rule_id']))
    return pl.DataFrame(list(existing.values()),schema=OPENING_CONTROL_STATE_SCHEMA),provenance
