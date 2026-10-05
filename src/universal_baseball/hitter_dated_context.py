"""Narrow dated-source corrections; no employment inference or foreign translation."""
from datetime import date

import polars as pl


def materialize(frame, population, foreign):
    context = {(r['player_id'], r['origin_year']): r for r in population}
    if len(context) != len(population):
        raise ValueError('Duplicate dated context')
    overseas = {(r['player_id'], r['origin_year']): r for r in foreign}
    if len(overseas) != len(foreign):
        raise ValueError('Duplicate foreign input')
    changes = []
    updates = []
    positions = [str(i) for i in range(1, 11)] + ['Y', 'UNKNOWN']
    for original in frame.iter_rows(named=True):
        key = original['player_id'], original['origin_year']
        if key not in context:
            raise ValueError('Missing exact dated context')
        p = context[key]
        if p['target_year'] != original['target_year'] or int(p['information_date'][:4]) != original['target_year']:
            raise ValueError('Future or mismatched source context')
        new = dict(original)
        new['on_40man'] = int(p['returned_40man'])
        codes = set(p['roster_position_codes'])
        explicit = codes & ({str(i) for i in range(2, 11)} | {'Y'})
        conflict = p['roster_cross_team_conflict'] or p['roster_status_conflict']
        if original['source_position'] in {'UNKNOWN', 'X', 'I', 'O'} and len(explicit) == 1 and '1' not in codes and not conflict:
            position = next(iter(explicit))
            new['source_position'] = position
            for pos in positions:
                new['position_' + pos] = int(pos == position)
        f = overseas.get(key)
        if original['age_unknown'] == 1 and f and f['birth_date'] and f['dated_role_hint'] in {'hitter_hint', 'two_way_hint', 'two_way_or_conflicting_hints'}:
            age = (date(original['origin_year'], 12, 31) - date.fromisoformat(f['birth_date'])).days / 365.2425
            if not 10 <= age <= 60:
                raise ValueError('Invalid professional age')
            new.update(age=age, age_unknown=0, age_centered=(age - 27) / 5, age_squared=((age - 27) / 5) ** 2)
        different = {c: dict(old=original[c], new=new[c]) for c in frame.columns if original[c] != new[c]}
        if different:
            changes.append(dict(row_id=original['row_id'], player_id=key[0], origin_year=key[1],
                                information_date=p['information_date'], changes=different))
        new.update(ctx_changed=bool(different), ctx_foreign_history_known=f is not None,
                   ctx_information_date=p['information_date'])
        updates.append(new)
    result = pl.DataFrame(updates, schema_overrides=frame.schema)
    return result, changes
