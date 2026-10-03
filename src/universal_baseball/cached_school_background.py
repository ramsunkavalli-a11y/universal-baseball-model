"""Recover broad background, never a player's class, from dated cached picks."""
from collections import defaultdict
import re


def name_key(value):
    return re.sub(r'\s+',' ',str(value or '').strip().upper())


def explicit_group(name,school_class):
    n,c=name_key(name),name_key(school_class)
    if c.startswith('HS') or re.search(r'\bHS\b|HIGH SCHOOL',n):return 'hs'
    if c.startswith('JC') or re.search(r'\b(JC|CC)\b|JUNIOR COLLEGE|COMMUNITY COLLEGE',n):return 'jc'
    if c.startswith('4YR') or c in ['FR','SO','JR','SR']:return 'college'
    return None


class DatedSchoolBackground:
    def __init__(self,records):
        self.evidence=defaultdict(list)
        for r in records:
            group=explicit_group(r['school_name'],r['school_class'])
            key=name_key(r['school_name'])
            if group and key:
                self.evidence[key].append(dict(year=int(r['draft_year']),player_id=int(r['player_id']),group=group,
                    school_name=r['school_name'],school_class=r['school_class']))

    def resolve(self,record,origin):
        if record is None:return dict(background='unknown',basis='no usable drafted pick',evidence=[])
        assert record['draft_year']<=origin
        group=explicit_group(record['school_name'],record['school_class'])
        if group:
            return dict(background=group,basis='own dated school class or explicit HS/JC name',
                evidence=[dict(year=record['draft_year'],player_id=record['player_id'],group=group,
                    school_name=record['school_name'],school_class=record['school_class'])])
        known=[r for r in self.evidence.get(name_key(record['school_name']),[]) if r['year']<=origin]
        groups={r['group'] for r in known}
        if len(groups)!=1:
            return dict(background='unknown',basis='conflicting dated institution groups' if groups else 'no exact dated institution match',evidence=known)
        # One representative per group proves the identity/date without a large ledger.
        first=min(known,key=lambda r:(r['year'],r['player_id']))
        return dict(background=first['group'],basis='exact institution name in a cutoff-known classified pick',evidence=[first])
