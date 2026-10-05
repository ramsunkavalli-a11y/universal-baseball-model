"""Repair assigned/signed substring confusion; preserve distinct context evidence."""
import re
from datetime import date
from .hitter_status_evidence import employment_kind as previous_kind, organization_state
from .hitter_preseason_population import available_date, transaction_key


def employment_kind(raw, teams):
    result = previous_kind(raw, teams)
    if (result == 'agreement_unspecified' and raw.get('typeCode') != 'SFA'
            and (raw.get('typeDesc') or '').lower() != 'signed as free agent'
            and re.search(r'\bsigned\b', (raw.get('description') or '').lower()) is None):
        return 'assignment_context'
    return result


def events(raw_events, teams, cutoff):
    unique = {}
    for raw in raw_events:
        known = available_date(raw)
        if known is None or date.fromisoformat(known) > cutoff:
            continue
        kind = employment_kind(raw, teams)
        if kind is None:
            continue
        key = transaction_key(raw)
        if key in unique and unique[key]['raw'] != raw:
            raise ValueError('Conflicting transaction version')
        target = (raw.get('toTeam') or {}).get('id')
        source = (raw.get('fromTeam') or {}).get('id')
        unique[key] = dict(known_date=known, kind=kind,
                          team_id=target if target in teams else source, raw=raw)
    return sorted(unique.values(), key=lambda x: (x['known_date'], str(transaction_key(x['raw']))))


def reconcile(previous, population, raw, teams):
    cutoff = date.fromisoformat(previous['information_date'])
    selected = events(raw, teams, cutoff)
    context = [e for e in selected if e['kind'] == 'assignment_context']
    employment = organization_state([e for e in selected if e['kind'] != 'assignment_context'])
    literal = population['returned_40man']
    conflict = (population['roster_cross_team_conflict'] or population['roster_status_conflict']
                or employment['same_date_conflict'])
    positive_conflict = literal and employment['state'] in {
        'reported_release', 'reported_retirement', 'reserve_departure_organization_unconfirmed'}
    negative_conflict = not literal and employment['explicit_major_link'] and not conflict
    return dict(**{k: v for k, v in previous.items() if k not in {
        'employment', 'status_major_link', 'status_minor_agreement', 'status_agreement_unspecified',
        'status_acquisition_only', 'status_released', 'status_employment_unknown',
        'status_employment_conflict', 'status_negative_listing_conflict', 'status_positive_listing_conflict'}},
        employment=employment, assignment_context=context,
        status_major_link=bool(literal and not conflict and not positive_conflict
                               or employment['explicit_major_link'] and not conflict),
        status_minor_agreement=employment['state'] == 'minor_agreement',
        status_agreement_unspecified=employment['state'] == 'agreement_unspecified',
        status_acquisition_only=employment['state'] == 'acquisition',
        status_released=employment['state'] == 'reported_release',
        status_employment_unknown=employment['state'] == 'unknown' and not literal,
        status_employment_conflict=bool(conflict or positive_conflict),
        status_negative_listing_conflict=bool(negative_conflict),
        status_positive_listing_conflict=bool(positive_conflict))
