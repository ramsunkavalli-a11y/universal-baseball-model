"""Native range quality, separated from defensive exposure and player value."""
from collections import Counter, defaultdict
import math

import numpy as np

FEATURES = ("history_rate", "reliability", "age_c", "age_sq", "age_missing",
            *(f"pos_{p}" for p in range(4, 10)), "history_x_reliability")
SHRINK_OUTS = 3000.0
RATE_OUTS = 1500.0


def history(rows, origin, position):
    past = [r for r in rows if origin - 2 <= r["season"] <= origin
            and r["position"] == position and r["range_valid"]]
    n = sum(r["native_outs"] * .5 ** (origin - r["season"]) for r in past)
    runs = sum(r["range_runs"] * .5 ** (origin - r["season"]) for r in past)
    return dict(history_outs=n, history_runs=runs, history_seasons=len(past),
                history_rate=RATE_OUTS * runs / (n + SHRINK_OUTS),
                reliability=n / (n + SHRINK_OUTS)), past


def features(row):
    age = row.get("age")
    c = ((age if age is not None else 27.) - 27.) / 10.
    return dict(history_rate=row["history_rate"], reliability=row["reliability"],
                age_c=c, age_sq=c * c, age_missing=age is None,
                **{f"pos_{p}": row["position"] == p for p in range(4, 10)},
                history_x_reliability=row["history_rate"] * row["reliability"])


def matrix(rows):
    return np.array([[float(features(r)[c]) for c in FEATURES] for r in rows],
                    dtype=float).reshape(len(rows), len(FEATURES))


def profile(row):
    a, n = row["age"], row["history_outs"]
    age = "unknown" if a is None else "<=24" if a <= 24 else "25-29" if a <= 29 else "30+"
    exposure = "<1500" if n < 1500 else "1500-4499" if n < 4500 else "4500+"
    return row["position"], age, exposure


def player_weights(rows):
    counts = Counter(r["player_id"] for r in rows)
    return np.array([1. / counts[r["player_id"]] for r in rows])


def preflight(train, test, origin, fold):
    assert all(r["window_end"] <= origin and r["origin_year"] < origin
               and r["quality_rate"] is not None and r["player_id"] % 5 != fold for r in train)
    assert all(r["origin_year"] == origin and r["player_id"] % 5 == fold for r in test)
    assert {r["player_id"] for r in train}.isdisjoint(r["player_id"] for r in test)
    for rows in (train, test):
        keys = [(r["origin_year"], r["player_id"], r["position"]) for r in rows]
        assert len(keys) == len(set(keys))
        assert np.isfinite(matrix(rows)).all()
    profiles = defaultdict(set)
    for r in train:
        profiles[profile(r)].add(r["player_id"])
    counts = [len(profiles[profile(r)]) for r in test]
    people = len({r["player_id"] for r in train})
    origins = sorted({r["origin_year"] for r in train})
    return dict(origin=origin, fold=fold, training_people=people, training_rows=len(train),
                training_origins=origins, test_rows=len(test),
                training_windows_with_2020=sum(r["window_has_2020"] for r in train),
                fit_allowed=people >= 100 and len(origins) >= 2,
                train_keys=[[r["origin_year"], r["player_id"], r["position"]] for r in train],
                test_keys=[[r["origin_year"], r["player_id"], r["position"]] for r in test],
                profile_counts=counts), counts


def fit(train):
    """Weighted standardization and ridge; serializable, independently replayable."""
    x, w = matrix(train), player_weights(train)
    y = np.array([r["quality_rate"] for r in train])
    mean = np.average(x, axis=0, weights=w)
    scale = np.sqrt(np.average((x - mean) ** 2, axis=0, weights=w))
    scale[scale < 1e-10] = 1.
    z = (x - mean) / scale
    intercept = float(np.average(y, weights=w))
    coef = np.linalg.solve(z.T @ (w[:, None] * z) + 10 * np.eye(z.shape[1]),
                           z.T @ (w * (y - intercept)))
    return dict(mean=mean.tolist(), scale=scale.tolist(), coef=coef.tolist(),
                intercept=intercept, alpha=10, features=list(FEATURES))


def predict(model, rows):
    z = (matrix(rows) - model["mean"]) / model["scale"]
    return model["intercept"] + z @ model["coef"]


def score(rows, arm):
    y = np.array([r["quality_rate"] for r in rows])
    p = np.array([r[arm] for r in rows])
    w = player_weights(rows)
    err = p - y
    return dict(rows=len(rows), people=len({r["player_id"] for r in rows}),
                rmse=float(np.sqrt(np.average(err ** 2, weights=w))),
                mae=float(np.average(np.abs(err), weights=w)),
                bias=float(np.average(err, weights=w)),
                oracle_exposure_actual_runs=sum(r["future_runs"] for r in rows),
                oracle_exposure_predicted_runs=sum(r[arm] * r["future_outs"] / RATE_OUTS for r in rows))


def paired_interval(rows, left, right, seed=313, draws=2000):
    """Resample people; each person's positions/origins jointly stay together."""
    groups = defaultdict(list)
    for r in rows:
        groups[r["player_id"]].append(r)
    losses = np.array([[np.mean([(r[a] - r["quality_rate"]) ** 2 for r in group])
                        for a in (left, right)] for group in groups.values()])
    if not len(losses):
        return None
    rng = np.random.default_rng(seed)
    differences = []
    for _ in range(draws):
        sample = losses[rng.integers(len(losses), size=len(losses))]
        differences.append(float(np.sqrt(sample[:, 0].mean()) - np.sqrt(sample[:, 1].mean())))
    return dict(left=left, right=right,
                difference=float(np.sqrt(losses[:, 0].mean()) - np.sqrt(losses[:, 1].mean())),
                interval_95=np.quantile(differences, [.025, .975]).tolist(),
                draws=draws, seed=seed)
