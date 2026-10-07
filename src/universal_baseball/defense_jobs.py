"""Joint field/DH role evidence and a capacity-limited information projection."""

from collections import defaultdict

import numpy as np
from scipy.optimize import linprog, minimize
from scipy.sparse import coo_matrix

from universal_baseball.defense_repertoire import POSITIONS, ROLES, family, normalized


def evidence(row, annual, dh_outs):
    y = row['origin_year']
    past = [r for r in annual if y-2 <= r['season'] <= y]
    mlb = [r for r in past if r['is_mlb']]
    vector = sum((np.array([r[f'outs_{p}'] for p in POSITIONS] +
                           [r['starts_10'] * dh_outs], float) * .5**(y-r['season'])
                  for r in mlb), np.zeros(9))
    kind = 'weighted_MLB'
    source_year = None
    if vector.sum() == 0:
        minor = [r for r in past if not r['is_mlb']]
        source_year = max((r['season'] for r in minor), default=None)
        vector = sum((np.array([r[f'outs_{p}'] for p in POSITIONS] +
                               [r['starts_10'] * dh_outs], float)
                      for r in minor if r['season'] == source_year), np.zeros(9))
        kind = 'latest_minor' if vector.sum() else 'roster_or_unknown'
    if vector.sum() == 0:
        vector = np.array([str(p) == str(row['source_position']) for p in ROLES], float)
    own = normalized(vector)
    role = ROLES[int(own.argmax())] if own.sum() else 0
    pa = sum(float(row[f'pa_{lag}']) * .5**lag for lag in range(3))
    if pa < 0 or not np.isfinite(pa):
        raise ValueError('Invalid MLB reliability exposure')
    catcher = any(r['outs_2'] > 0 or r['starts_2'] > 0 for r in past) or str(row['source_position']) == '2'
    return dict(job_own_shares=own.tolist(), job_primary_role=role, job_family=family(role),
                job_status='prior_MLB' if row['prior_debut'] else 'no_prior_MLB',
                job_evidence_kind=kind, job_minor_season=source_year,
                job_weight=pa/(pa+100.), job_evidence_PA=pa,
                job_catching_evidence=catcher, job_unknown=bool(own.sum() == 0))


def keys(row):
    role, fam, status = str(row['job_primary_role']), row['job_family'], row['job_status']
    return [('role_status', role, status), ('role', role),
            ('family_status', fam, status), ('family', fam), ('all',)]


def matches(row, key):
    if key[0].startswith('role') and str(row['job_primary_role']) != key[1]:
        return False
    if key[0].startswith('family') and row['job_family'] != key[1]:
        return False
    return not (key[0].endswith('_status') and row['job_status'] != key[2])


def group(rows, key, fit=False):
    selected = [r for r in rows if matches(r, key)]
    people = defaultdict(float)
    numerator = np.zeros(9)
    for r in selected:
        mass = np.array(r['actual_job_vector'], float)
        if r['next_pa'] <= 0 or mass.sum() <= 0 or r['target_year'] < 2022:
            raise ValueError('Invalid same-policy conditional role label')
        people[r['player_id']] += float(mass.sum())
        if fit:
            numerator += mass
    den = sum(people.values())
    out = dict(key=list(key), people=len(people), rows=len(selected), denominator_job_time=den,
               effective_people=den**2/sum(v*v for v in people.values()) if den else 0.)
    if fit:
        out.update(numerators=numerator.tolist(), shares=(numerator/den).tolist() if den else None)
    return out


def supported(cell):
    return cell['people'] >= 20 and cell['effective_people'] >= 10 and cell['denominator_job_time'] > 0


def allocate(row, tables, total):
    cell = next((tables[k] for k in keys(row) if k in tables and supported(tables[k])), None)
    own = np.array(row['job_own_shares'], float)
    learned = np.array(cell['shares'], float) if cell else own.copy()
    if not row['job_catching_evidence']:
        learned[0] = 0.
    learned = normalized(learned)
    a = row['job_weight']
    shares = (np.zeros(9) if row['job_unknown'] else
              normalized(a*own + (1-a)*learned) if learned.sum() else own)
    if not row['job_catching_evidence'] and shares[0] != 0:
        raise ValueError('Catching without origin evidence')
    if total < 0 or not np.isfinite(total):
        raise ValueError('Invalid job exposure')
    return dict(values=(total*shares).tolist(), shares=shares.tolist(),
                learned_shares=learned.tolist(), prior=cell,
                unsupported=cell is None, unknown_mass=total if row['job_unknown'] else 0.)


def reconcile(seed, caps):
    """Min KL from seed, fixed row mass, column upper bounds, no new edges."""
    seed, caps = np.asarray(seed, float), np.asarray(caps, float)
    if seed.ndim != 2 or caps.shape != (seed.shape[1],):
        raise ValueError('Shape mismatch')
    if not np.isfinite(seed).all() or not np.isfinite(caps).all() or (seed < 0).any() or (caps <= 0).any():
        raise ValueError('Invalid job masses/capacities')
    total = float(seed.sum())
    factor = min(1., float(caps.sum())/total) if total else 1.
    seed = seed*factor
    active = seed.sum(axis=1) > 0
    if not active.any():
        return seed, dict(global_mass_factor=factor, multipliers=[0.]*len(caps), iterations=0,
                          feasibility=True, max_row_residual=0., max_cap_excess=0., kkt_residual=0.)
    s = seed[active]
    r = s.sum(axis=1)
    # Sparse feasibility on the exact support graph, in league-scale units.
    ii, jj = np.where(s > 0)
    n, m = s.shape
    eq = coo_matrix((np.ones(len(ii)), (ii, np.arange(len(ii)))), shape=(n,len(ii))).tocsr()
    ub = coo_matrix((np.ones(len(ii)), (jj, np.arange(len(ii)))), shape=(m,len(ii))).tocsr()
    scale = float(caps.sum())
    feasible = linprog(np.zeros(len(ii)), A_ub=ub, b_ub=caps/scale,
                       A_eq=eq, b_eq=r/scale, bounds=(0,None), method='highs')
    if not feasible.success:
        raise ValueError('Role support graph cannot meet capacity: '+feasible.message)
    p = s/r[:,None]
    rn, cn = r/scale, caps/scale
    def objective(lam):
        weights = p*np.exp(-lam)[None,:]
        z = weights.sum(axis=1)
        x = rn[:,None]*weights/z[:,None]
        return float(rn@np.log(z)+cn@lam), cn-x.sum(axis=0)
    solution = minimize(objective, np.zeros(m), jac=True, method='L-BFGS-B',
                        bounds=[(0,None)]*m,
                        options=dict(maxiter=10000, ftol=1e-15, gtol=1e-12, maxls=100))
    lam = solution.x
    weights = p*np.exp(-lam)[None,:]
    out = np.zeros_like(seed)
    out[active] = r[:,None]*weights/weights.sum(axis=1)[:,None]
    col = out.sum(axis=0)
    row_error = float(np.max(abs(out.sum(axis=1)-seed.sum(axis=1))))
    excess = float(max(0., np.max(col-caps)))
    grad = cn-col/scale
    kkt = float(max(np.max(abs(grad[lam>1e-8])) if (lam>1e-8).any() else 0.,
                    max(0.,-np.min(grad[lam<=1e-8])) if (lam<=1e-8).any() else 0.))
    if not solution.success or row_error > 1e-7 or excess > .02 or kkt > 2e-8 or (out[seed==0] != 0).any():
        raise ValueError(f'Projection not certified: {solution.message}, row={row_error}, cap={excess}, kkt={kkt}')
    return out, dict(global_mass_factor=factor, multipliers=lam.tolist(), iterations=int(solution.nit),
                     feasibility=True, max_row_residual=row_error, max_cap_excess=excess,
                     kkt_residual=kkt, seed_column_totals=seed.sum(axis=0).tolist(),
                     allocated_column_totals=col.tolist(), unused_capacity=(caps-col).tolist())
