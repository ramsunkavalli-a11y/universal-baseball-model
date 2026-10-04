"""Future-blind preseason source mechanics, not a talent or rights model."""
from collections import Counter
from datetime import date
import json


def canonical(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def transaction_key(row):
    """One trade can have multiple people and a cash leg with person ID zero."""
    return (row['id'], row.get('person', {}).get('id'),
            row.get('fromTeam', {}).get('id'), row.get('toTeam', {}).get('id'),
            row.get('typeCode'), row.get('date'), row.get('effectiveDate'), row.get('resolutionDate'))


def reconcile_transactions(whole, partitions, start, end):
    """Check content and multiplicity, not just a set of transaction IDs."""
    assert date.fromisoformat(start) <= date.fromisoformat(end)
    joined = []
    for begin, finish, rows in partitions:
        assert start <= begin <= finish <= end
        for row in rows:
            assert begin <= str(row['date'])[:10] <= finish, 'Transaction outside requested monthly window'
        joined.extend(rows)
    for row in whole:
        assert start <= str(row['date'])[:10] <= end, 'Transaction outside broad requested window'
    assert Counter(map(canonical, whole)) == Counter(map(canonical, joined)), 'Whole/monthly content mismatch'
    return dict(records=len(whole), transaction_ids=len({r['id'] for r in whole}),
                composite_events=len({transaction_key(r) for r in whole}),
                identical_duplicate_rows=len(whole)-len(set(map(canonical, whole))))


def available_date(row):
    """Conservative provider-date boundary; publication vintage is unverified."""
    values = [str(row[key])[:10] for key in ('date', 'effectiveDate', 'resolutionDate') if row.get(key)]
    if not values or not row.get('date'):
        return None
    for value in values:
        date.fromisoformat(value)
    return max(values)


def roster_people(rows):
    """Collapse identity-consistent duplicates; preserve status/parent diagnostics."""
    groups = {}
    for row in rows:
        pid = row['person']['id']
        assert isinstance(pid, int) and pid > 0
        groups.setdefault(pid, []).append(row)
    for group in groups.values():
        assert len({(r['person'].get('fullName'), r['person'].get('link')) for r in group}) == 1
    return groups


def classify_event(row, mlb_teams):
    """Event evidence only; neither a complete rights history nor guaranteed PA."""
    text = row.get('description', '').lower()
    target = row.get('toTeam', {}).get('id')
    source = row.get('fromTeam', {}).get('id')
    kind = row.get('typeDesc', '').lower()
    if source not in mlb_teams and target not in mlb_teams:
        return 'outside_mlb_team_event'
    if any(x in kind for x in ('free agency', 'released')) or any(x in text for x in (' elected free agency', ' released ')):
        return 'scope_exit'
    if target in mlb_teams and ('signed ' in text or kind == 'signed as free agent'):
        return 'minor_agreement' if 'minor league contract' in text or 'minor-league contract' in text else 'agreement_unspecified'
    if target in mlb_teams and kind in ('trade', 'claimed off waivers', 'selected off waivers', 'rule 5 draft', 'purchased'):
        return 'acquisition'
    if target in mlb_teams and ('selected the contract' in text or 'selected contract' in text):
        return 'contract_selection'
    if target in mlb_teams and (' activated ' in text or 'reinstated' in text):
        return 'activation'
    return 'other_mlb_team_event'
