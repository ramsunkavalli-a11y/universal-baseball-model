"""Role hints from dated records, without replacing unknown performance."""
import re

HITTER_CODES = {'2','3','4','5','6','7','8','9','10','O','I'}
HITTER_ABBREVIATIONS = {'C','1B','2B','3B','SS','LF','CF','RF','OF','IF','DH'}


def role_from_position(position):
    if position.get('code')=='Y' or position.get('abbreviation')=='TWP':
        return 'two_way_hint'
    if position.get('code') in HITTER_CODES or position.get('abbreviation') in HITTER_ABBREVIATIONS:
        return 'hitter_hint'
    if position.get('code')=='1' or position.get('abbreviation') in {'P','RHP','LHP'}:
        return 'pitcher_hint'
    return 'unknown'


def role_from_transaction(row):
    """A shared trade description must not assign another player's position."""
    name = row.get('person',{}).get('fullName')
    if not name:
        return 'unknown'
    found = re.search(r'\b(TWP|RHP/DH|LHP/DH|RHP|LHP|1B|2B|3B|SS|LF|CF|RF|OF|IF|DH|C)\s+'+re.escape(name)+r'(?!\w)',
                      row.get('description',''),flags=re.IGNORECASE)
    if not found:
        return 'unknown'
    abbreviation = found.group(1).upper()
    if abbreviation in {'TWP','RHP/DH','LHP/DH'}:
        return 'two_way_hint'
    return role_from_position({'abbreviation':abbreviation})


def reconcile_hints(hints):
    hints = set(hints)-{'unknown'}
    if 'two_way_hint' in hints or {'pitcher_hint','hitter_hint'} <= hints:
        return 'two_way_or_conflicting_hints'
    return next(iter(hints)) if hints else 'unknown'
