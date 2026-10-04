"""Additive source-specific initial/surname reconciliation, never fuzzy matching."""
import re

from universal_baseball.npb_history import name_key


def reviewed_id(row, listing):
    if row['npb_id'] is not None:
        return row['npb_id'], row['npb_identity_status']
    candidates = set()
    for name, ids in listing.items():
        match = re.fullmatch(r'[A-ZＡ-Ｚ][.．](.+)', name_key(name))
        if match and match[1] == row['name_key']:
            candidates.update(ids)
    if len(candidates) == 1:
        return next(iter(candidates)), 'unique_same_team_published_initial_alias'
    if candidates:
        return None, 'ambiguous_published_initial_alias'
    return None, row['npb_identity_status']
