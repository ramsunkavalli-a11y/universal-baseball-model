"""Scalar opportunity shrinkage with a player's own defensive repertoire."""

from collections import defaultdict

import numpy as np

POSITIONS = tuple(range(2, 10))
ROLES = (*POSITIONS, 10)
PSEUDO_PA = 100.


def normalized(values):
    a = np.array(values, float)
    if not np.isfinite(a).all() or (a < 0).any():
        raise ValueError("Invalid role evidence")
    return a / a.sum() if a.sum() else a


def family(role):
    return "C" if role == 2 else "1B" if role == 3 else "IF" if role in (4,5,6) else "OF" if role in (7,8,9) else "DH" if role == 10 else "unknown"


def keys(row):
    role = str(row["repertoire_primary_role"])
    fam = row["repertoire_family"]
    return [("role_stage",role,row["stage"]),("family_stage",fam,row["stage"]),
            ("role",role),("family",fam),("all",)]


def make_repertoire(row, annual):
    y, pid = row["origin_year"], row["player_id"]
    records = [r for r in annual if r["player_id"] == pid and y-2 <= r["season"] <= y]
    current = [r for r in records if r["is_mlb"] and r["season"] == y]
    minor = [r for r in records if not r["is_mlb"]]
    if minor:
        latest = max(r["season"] for r in minor)
        fallback = [r for r in minor if r["season"] == latest]
        kind = "latest_minor_season"
    else:
        older = [r for r in records if r["is_mlb"] and r["season"] < y and r["defensive_outs"] > 0]
        latest = max((r["season"] for r in older), default=None)
        fallback = [r for r in older if r["season"] == latest]
        kind = "older_MLB_season" if fallback else "roster_or_unknown"
    c_out = np.array([sum(r[f"outs_{p}"] for r in current) for p in POSITIONS], float)
    f_out = np.array([sum(r[f"outs_{p}"] for r in fallback) for p in POSITIONS], float)
    c_start = np.array([sum(r[f"starts_{p}"] for r in current) for p in ROLES], float)
    f_start = np.array([sum(r[f"starts_{p}"] for r in fallback) for p in ROLES], float)
    pos = str(row.get("source_position","unknown"))
    if not fallback:
        f_out = np.array([str(p)==pos for p in POSITIONS],float)
        f_start = np.array([str(p)==pos for p in ROLES],float)
    pa = float(row["pa_0"])
    if pa < 0:
        raise ValueError("Invalid MLB sample")
    weight = pa / (pa + PSEUDO_PA)
    if c_out.sum() and not f_out.sum():
        mix = normalized(c_out)
    elif f_out.sum() and not c_out.sum():
        mix = normalized(f_out)
    else:
        mix = normalized(weight * normalized(c_out) + (1-weight) * normalized(f_out))
    c_role = normalized(c_start) if c_start.sum() else np.r_[normalized(c_out),0.]
    f_role = normalized(f_start) if f_start.sum() else np.r_[normalized(f_out),0.]
    role_mix = normalized(weight*c_role + (1-weight)*f_role)
    if role_mix.sum() == 0 and mix.sum():
        role_mix = np.r_[mix,0.]
    role = ROLES[int(np.argmax(role_mix))] if role_mix.sum() else 0
    return dict(repertoire_shares=mix.tolist(),repertoire_role_shares=role_mix.tolist(),
        repertoire_primary_role=role,repertoire_family=family(role),repertoire_weight=weight,
        repertoire_fallback_kind=kind,repertoire_current_outs=c_out.tolist(),repertoire_fallback_outs=f_out.tolist(),
        repertoire_current_starts=c_start.tolist(),repertoire_fallback_starts=f_start.tolist(),
        repertoire_fallback_season=latest,repertoire_unknown=bool(mix.sum()==0))


def group_matches(row, key):
    if key[0] in ("role_stage","role") and str(row["repertoire_primary_role"]) != key[1]:
        return False
    if key[0] in ("family_stage","family") and row["repertoire_family"] != key[1]:
        return False
    return not (key[0].endswith("_stage") and row["stage"] != key[2])


def mean_group(train,key,fit=False):
    rows = [r for r in train if group_matches(r,key)]
    people = defaultdict(float)
    for r in rows:
        if r["next_pa"] <= 0:
            raise ValueError("Conditional group includes nonpositive PA")
        people[r["player_id"]] += r["next_pa"]
    den = sum(people.values())
    result = dict(key=list(key),rows=len(rows),people=len(people),denominator_PA=den,
                  effective_people=den*den/sum(v*v for v in people.values()) if den else 0.)
    if fit:
        outs = sum(sum(r[f"actual_{p}"] for p in POSITIONS) for r in rows)
        dh = sum(r["actual_10"] for r in rows)
        result.update(numerator_outs=outs,numerator_DH_starts=dh,
                      outs_per_PA=outs/den if den else None,DH_starts_per_PA=dh/den if den else None)
    return result


def supported(cell):
    return cell["people"] >= 20 and cell["effective_people"] >= 10 and cell["denominator_PA"] > 0


def predict(row,tables):
    cell = next((tables[k] for k in keys(row) if supported(tables[k])),None)
    if cell is None:
        raise ValueError("No supported broad exposure prior")
    pa = float(row["pa_0"])
    a = row["repertoire_weight"]
    old_rate = sum(row[f"carry_{p}"] for p in POSITIONS)/pa if pa else 0.
    old_dh = row["carry_10"]/pa if pa else 0.
    total = row["preseason_pa"]*(a*old_rate+(1-a)*cell["outs_per_PA"])
    values = total*np.array(row["repertoire_shares"])
    dh = row["preseason_pa"]*(a*old_dh+(1-a)*cell["DH_starts_per_PA"])
    if not np.isfinite(values).all() or (values<0).any():
        raise ValueError("Invalid opportunity forecast")
    return dict(values=[*values.tolist(),float(dh)],potential_total_outs=total,
                unallocated_outs=total-float(values.sum()),prior=cell,raw_current_outs_per_PA=old_rate,
                shrunk_outs_per_PA=a*old_rate+(1-a)*cell["outs_per_PA"])
