"""Small, exposure-shrunk range transfer within related position families."""
from collections import defaultdict

import numpy as np

from universal_baseball import defense_native_range as base

EXTRA = ("other_range_IF", "other_range_OF", "other_reliability_IF",
         "other_reliability_OF", "SS_to_2B3B", "2B3B_to_SS",
         "CF_to_corners", "corners_to_CF")
FEATURES = (*base.FEATURES, *EXTRA)


def family(position):
    if position in (4, 5, 6):
        return (4, 5, 6)
    if position in (7, 8, 9):
        return (7, 8, 9)
    return ()


def other_history(sources, origin, position):
    allowed = set(family(position)) - {position}
    recent = [s for s in sources if origin - 2 <= s["season"] <= origin
              and s["position"] in allowed]
    measured = [s for s in recent if s["range_valid"]]
    n = sum(s["native_outs"] * .5 ** (origin - s["season"]) for s in measured)
    runs = sum(s["range_runs"] * .5 ** (origin - s["season"]) for s in measured)
    pivot = 6 if position in (4, 5, 6) else 8
    pivot_outs = sum(s["native_outs"] * .5 ** (origin - s["season"])
                     for s in measured if s["position"] == pivot)
    return dict(other_outs=n, other_runs=runs,
                other_rate=1500 * runs / (n + 3000),
                other_reliability=n / (n + 3000),
                other_pivot_share=pivot_outs / n if n else 0.,
                other_positions=len({s["position"] for s in measured}),
                other_invalid_outs=sum(s["native_outs"] for s in recent if not s["range_valid"])), measured


def features(row):
    out = base.features(row)
    pos = row["position"]
    d = 1 - row["reliability"]
    n = row["other_reliability"] * d
    r = row["other_rate"] * d
    share = row["other_pivot_share"]
    out.update(other_range_IF=r if pos in (4, 5, 6) else 0.,
               other_range_OF=r if pos in (7, 8, 9) else 0.,
               other_reliability_IF=n if pos in (4, 5, 6) else 0.,
               other_reliability_OF=n if pos in (7, 8, 9) else 0.,
               SS_to_2B3B=n * share if pos in (4, 5) else 0.,
               **{"2B3B_to_SS":n * (1 - share) if pos == 6 else 0.},
               CF_to_corners=n * share if pos in (7, 9) else 0.,
               corners_to_CF=n * (1 - share) if pos == 8 else 0.)
    return out


def matrix(rows, disabled=()):
    x = np.array([[float(features(r)[c]) for c in FEATURES] for r in rows],
                 dtype=float).reshape(len(rows), len(FEATURES))
    for c in disabled:
        x[:, FEATURES.index(c)] = 0.
    return x


def transfer_profile(row):
    n = row["other_outs"]
    return (*base.profile(row), "<300" if n < 300 else "300-1499" if n < 1500 else "1500+")


def preflight(train, test, origin, fold):
    check, old_counts = base.preflight(train, test, origin, fold)
    assert np.isfinite(matrix(train)).all() and np.isfinite(matrix(test)).all()
    people = defaultdict(set)
    nonzero = {c:set() for c in EXTRA}
    for r in train:
        people[transfer_profile(r)].add(r["player_id"])
        f = features(r)
        for c in EXTRA:
            if abs(f[c]) > 1e-12:
                nonzero[c].add(r["player_id"])
    counts = [len(people[transfer_profile(r)]) for r in test]
    disabled = [c for c in EXTRA if len(nonzero[c]) < 20]
    check.update(transfer_profile_counts=counts,
                 added_feature_people={c:len(p) for c,p in nonzero.items()},
                 disabled_features=disabled, old_profile_counts=old_counts)
    return check, counts


def fit(train, disabled=()):
    x, w = matrix(train, disabled), base.player_weights(train)
    y = np.array([r["quality_rate"] for r in train])
    mean = np.average(x, axis=0, weights=w)
    scale = np.sqrt(np.average((x - mean) ** 2, axis=0, weights=w))
    scale[scale < 1e-10] = 1.
    z = (x - mean) / scale
    intercept = float(np.average(y, weights=w))
    coef = np.linalg.solve(z.T @ (w[:,None] * z) + 10 * np.eye(len(FEATURES)),
                           z.T @ (w * (y - intercept)))
    return dict(mean=mean.tolist(), scale=scale.tolist(), coef=coef.tolist(),
                intercept=intercept, alpha=10, features=list(FEATURES), disabled=list(disabled))


def predict(model, rows):
    z = (matrix(rows, model["disabled"]) - model["mean"]) / model["scale"]
    return model["intercept"] + z @ model["coef"]
