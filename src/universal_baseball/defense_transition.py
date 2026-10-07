"""Supported conditional MLB position distributions, distinct from fielding skill."""

from collections import defaultdict

import numpy as np

from universal_baseball.defense_repertoire import POSITIONS, ROLES, normalized


def evidence(row, annual):
    y = row['origin_year']
    past = [r for r in annual if r['player_id'] == row['player_id'] and y-2 <= r['season'] <= y]
    pa = sum(float(row[f'pa_{lag}']) * .5**lag for lag in range(3))
    if pa < 0 or not np.isfinite(pa):
        raise ValueError('Invalid observed MLB PA')
    shares = np.array(row['repertoire_shares'], float)
    role = row['repertoire_primary_role']
    older = [r for r in past if r['is_mlb'] and r['season'] < y and r['defensive_outs'] > 0]
    returning = row['pa_0'] == 0 and bool(older)
    season = None
    if returning:
        season = max(r['season'] for r in older)
        old = [r for r in past if r['is_mlb'] and r['season'] == season]
        outs = np.array([sum(r[f'outs_{p}'] for r in old) for p in POSITIONS], float)
        starts = np.array([sum(r[f'starts_{p}'] for r in old) for p in ROLES], float)
        shares = normalized(outs)
        role = ROLES[int(np.argmax(starts))] if starts.sum() else POSITIONS[int(np.argmax(outs))]
    c = any(r['outs_2'] > 0 or r['starts_2'] > 0 for r in past) or str(row['source_position']) == '2'
    return dict(transition_shares=shares.tolist(), transition_primary_role=role,
                transition_status='prior_MLB' if row['prior_debut'] else 'no_prior_MLB',
                transition_evidence_PA=pa, transition_weight=pa/(pa+100.),
                transition_returning_history=returning, transition_return_season=season,
                transition_catching_evidence=c, transition_unknown=bool(shares.sum() == 0))


def keys(row):
    role = str(row['transition_primary_role'])
    return [('role_status', role, row['transition_status']), ('role', role)]


def matches(row, key):
    return str(row['transition_primary_role']) == key[1] and (
        key[0] == 'role' or row['transition_status'] == key[2])


def group(rows, key, fit=False):
    selected = [r for r in rows if matches(r, key)]
    masses = defaultdict(float)
    for r in selected:
        total = sum(r[f'actual_{p}'] for p in POSITIONS)
        if total <= 0 or r['next_pa'] <= 0:
            raise ValueError('Transition training requires positive measured fielding and PA')
        masses[r['player_id']] += total
    den = sum(masses.values())
    result = dict(key=list(key), rows=len(selected), people=len(masses), denominator_outs=den,
                  effective_people=den**2/sum(v*v for v in masses.values()) if den else 0.)
    if fit:
        num = [sum(r[f'actual_{p}'] for r in selected) for p in POSITIONS]
        result.update(position_outs=num, shares=(np.array(num)/den).tolist() if den else None)
    return result


def supported(cell):
    return cell['people'] >= 20 and cell['effective_people'] >= 10 and cell['denominator_outs'] > 0


def allocate(row, tables):
    own = np.array(row['transition_shares'], float)
    cell = next((tables[key] for key in keys(row) if supported(tables[key])), None)
    learned = np.array(cell['shares'], float) if cell else own.copy()
    if not row['transition_catching_evidence']:
        learned[0] = 0
    learned = normalized(learned)
    # A known role is needed even when the cohort has a supported position mean.
    if row['transition_unknown']:
        shares = np.zeros(8)
    elif learned.sum() == 0:
        shares = own
    else:
        a = row['transition_weight']
        shares = normalized(a*own + (1-a)*learned)
    if not row['transition_catching_evidence'] and shares[0] != 0:
        raise ValueError('Catcher allocation without own catching evidence')
    total = float(row['repair_potential_outs'])
    values = total*shares
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Invalid transition allocation')
    return dict(values=[*values.tolist(),row['repair_10']], shares=shares.tolist(),
                learned_allowed_shares=learned.tolist(), own_shares=own.tolist(),
                prior=cell, unsupported_transition=cell is None,
                potential_total_outs=total, unallocated_outs=total-float(values.sum()))
