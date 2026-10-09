"""Own-position joint workload, without learned donations of position shares."""
from collections import defaultdict
import numpy as np
from universal_baseball.defense_repertoire import ROLES, normalized, family


def evidence(row, annual, dh_outs):
    y, pid = row['origin_year'], row['player_id']
    if not np.isfinite(dh_outs) or dh_outs <= 0:
        raise ValueError('Invalid DH unit conversion')
    history = [r for r in annual if r['player_id'] == pid and y-2 <= r['season'] <= y]
    current = [r for r in history if r['is_mlb'] and r['season'] == y]
    minor = [r for r in history if not r['is_mlb']]
    fallback = minor or [r for r in history if r['is_mlb'] and r['season'] < y]
    latest = max((r['season'] for r in fallback), default=None)
    fallback = [r for r in fallback if r['season'] == latest]
    def vector(records):
        return sum((np.array([r[f'outs_{p}'] for p in ROLES[:-1]] +
                            [r['starts_10']*dh_outs], float) for r in records), np.zeros(9))
    c, f = vector(current), vector(fallback)
    kind = 'latest_minor' if minor else 'older_MLB' if fallback else 'roster_or_unknown'
    if f.sum() == 0:
        f = np.array([str(p) == str(row.get('source_position')) for p in ROLES], float)
    pa = float(row['pa_0'])
    if not np.isfinite(pa) or pa < 0:
        raise ValueError('Invalid MLB PA')
    a = pa/(pa+100.)
    shares = normalized(a*normalized(c)+(1-a)*normalized(f))
    role = ROLES[int(shares.argmax())] if shares.sum() else 0
    return dict(role_shares=shares.tolist(), role=role, family=family(role),
                current_vector=c.tolist(), fallback_vector=f.tolist(),
                fallback_kind=kind, fallback_season=latest, reliability=a,
                unknown=not bool(shares.sum()), current_rate=float(c.sum()/pa) if pa else 0.)


def keys(row):
    return [('role_stage',str(row['role']),row['stage']),
            ('family_stage',row['family'],row['stage']),('role',str(row['role'])),
            ('family',row['family']),('all',)]


def cell(rows, key, with_outcomes=False):
    selected = [r for r in rows if key in keys(r)]
    people = defaultdict(float)
    for r in selected:
        if r['next_pa'] <= 0 or r['target_year'] < 2022:
            raise ValueError('Invalid conditional same-policy training row')
        people[r['player_id']] += r['next_pa']
    den = sum(people.values())
    result = dict(key=list(key), people=len(people), denominator_PA=den,
                  effective_people=den**2/sum(v*v for v in people.values()) if den else 0.)
    if with_outcomes:
        result['job_outs_per_PA'] = sum(r['actual_job_total'] for r in selected)/den if den else None
    return result


def supported(c):
    return c['people'] >= 20 and c['effective_people'] >= 10 and c['denominator_PA'] > 0


def predict(row, tables, dh_outs):
    prior = next((tables[k] for k in keys(row) if k in tables and supported(tables[k])),None)
    if prior is None:
        raise ValueError('No supported scalar prior')
    a = row['reliability']
    rate = a*row['current_rate']+(1-a)*prior['job_outs_per_PA']
    budget = float(row['preseason_pa'])*rate
    if not np.isfinite(budget) or budget < 0:
        raise ValueError('Invalid workload')
    jobs = budget*np.array(row['role_shares'])
    values = [*jobs[:-1].tolist(),float(jobs[-1]/dh_outs)]
    return dict(values=values, job_budget=budget, job_outs_per_PA=rate,
                unallocated=budget-float(jobs.sum()), prior=prior)
