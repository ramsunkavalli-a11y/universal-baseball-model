"""Interpretable conditional opportunity means with explicit partial pooling."""

from collections import defaultdict
import math

import numpy as np

POSITIONS = tuple(range(2, 10))
ROLES = (*POSITIONS, 10)
MIN_PEOPLE = 20
MIN_EFFECTIVE = 10.0
CHANNELS = ("framing", "throwing", "blocking", "arm", "receiving")


def role_mix(row):
    values = [float(row[f"mlb_weighted_starts_{p}"]) + float(row[f"minor_weighted_starts_{p}"]) for p in ROLES]
    kind = "observed_starts"
    if sum(values) == 0:
        values = [float(row[f"mlb_weighted_outs_{p}"]) + float(row[f"minor_weighted_outs_{p}"]) for p in POSITIONS] + [0.]
        kind = "observed_outs_fallback"
    if sum(values) == 0:
        pos = str(row.get("source_position", "unknown"))
        values = [float(str(p) == pos) for p in ROLES]
        kind = "roster_fallback" if sum(values) else "unknown_role"
    total = sum(values)
    assert all(math.isfinite(v) and v >= 0 for v in values)
    return ([v / total for v in values] if total else values), kind


def group_keys(row, role):
    return [("role_stage_age", str(role), row["stage"], row["age_band"]),
            ("role_stage", str(role), row["stage"]), ("role", str(role))]


def sufficient(cell):
    return cell["people"] >= MIN_PEOPLE and cell["effective_people"] >= MIN_EFFECTIVE and cell["denominator_PA"] > 0


def estimate(rows, scope, target=None):
    """Prepare support without outcomes when target is None; fit one fixed mean otherwise."""
    masses = defaultdict(float)
    total_pa = 0.
    numerator = np.zeros(len(ROLES))
    n = 0
    for row in rows:
        shares = row.get("bridge_role_shares")
        if shares is None:
            shares, _ = role_mix(row)
        weight = 1. if scope[0] == "all" else shares[ROLES.index(int(scope[1]))]
        if scope[0] in {"role_stage", "role_stage_age"} and row["stage"] != scope[2]:
            continue
        if scope[0] == "role_stage_age" and row["age_band"] != scope[3]:
            continue
        if weight <= 0:
            continue
        pa = float(row["next_pa"])
        assert pa > 0 and math.isfinite(pa)
        masses[row["player_id"]] += weight * pa
        total_pa += weight * pa
        n += 1
        if target is not None:
            numerator += weight * np.asarray(target[row["row_id"]], dtype=float)
    effective = total_pa ** 2 / sum(v * v for v in masses.values()) if total_pa else 0.
    return dict(scope=list(scope), rows=n, people=len(masses), effective_people=effective,
                denominator_PA=total_pa, numerator=numerator.tolist() if target is not None else None,
                rates=(numerator / total_pa).tolist() if target is not None and total_pa else None)


def support_tables(train, test):
    needed = {("all",)}
    for row in test:
        shares, _ = role_mix(row)
        for role, share in zip(ROLES, shares):
            if share:
                needed.update(group_keys(row, role))
    return {key: estimate(train, key) for key in sorted(needed)}


def fit_tables(train, test, targets):
    return {key: estimate(train, key, targets) for key in support_tables(train, test)}


def choose(tables, row, role, contextual):
    keys = group_keys(row, role) if contextual else [("role", str(role))]
    for key in keys + [("all",)]:
        cell = tables[key]
        if sufficient(cell):
            return cell
    raise ValueError("No supported broad opportunity fallback")


def predict(tables, row, contextual):
    shares, kind = role_mix(row)
    rates = np.zeros(len(ROLES))
    trace = []
    if sum(shares) == 0:
        cell = tables[("all",)]
        if not sufficient(cell):
            raise ValueError("Unsupported unknown-role fallback")
        rates = np.asarray(cell["rates"])
        trace = [dict(role="unknown", share=1., **cell)]
    else:
        for role, share in zip(ROLES, shares):
            if share:
                cell = choose(tables, row, role, contextual)
                rates += share * np.asarray(cell["rates"])
                trace.append(dict(role=str(role), share=share, **cell))
    values = rates * float(row["preseason_pa"])
    assert np.isfinite(values).all() and (values >= 0).all()
    return dict(values=values.tolist(), rates=rates.tolist(), role_shares=shares, role_kind=kind,
                trace=trace, coarse_mass=sum(t["share"] for t in trace if t["scope"][0] in {"role", "all"}))


def native_conversion(records, origin, fold, fold_for_player):
    selected = [r for r in records if origin - 2 <= r["season"] <= origin and r["valid"] and fold_for_player(r["player_id"]) != fold]
    fallback = False
    if len({r["player_id"] for r in selected}) < MIN_PEOPLE or len({r["season"] for r in selected}) < 2:
        selected = [r for r in records if r["season"] <= origin and r["valid"] and fold_for_player(r["player_id"]) != fold]
        fallback = True
    if len({r["player_id"] for r in selected}) < MIN_PEOPLE or len({r["season"] for r in selected}) < 2:
        raise ValueError("Native conversion has insufficient historical coverage")
    opportunities = sum(r["opportunities"] * 0.5 ** (origin - r["season"]) for r in selected)
    outs = sum(r["official_exposure"] * 0.5 ** (origin - r["season"]) for r in selected)
    assert outs > 0 and opportunities >= 0
    return dict(rate=opportunities / outs, opportunities=opportunities, official_outs=outs,
                people=len({r["player_id"] for r in selected}), seasons=sorted({r["season"] for r in selected}),
                rows=len(selected), expanded_history_fallback=fallback)


def native_from_outs(values, conversions):
    by_pos = dict(zip(ROLES, values))
    return {c: (by_pos[2] if c in {"framing", "throwing", "blocking"} else
                sum(by_pos[p] for p in (7, 8, 9)) if c == "arm" else by_pos[3]) * conversions[c]["rate"] for c in CHANNELS}
