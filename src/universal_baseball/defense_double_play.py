"""Small-channel MLB DP evidence, not mechanical talent or raw minor counts."""
import math
from collections import Counter, defaultdict

import numpy as np

PRIOR_OUTS = 3000.
RATE_OUTS = 1500.


def history(rows, origin, position):
    if position not in (3, 4, 5, 6):
        raise ValueError('DP history only covers infield positions 3 through 6')
    recent = [r for r in rows if origin-2 <= r['season'] <= origin and r['position'] == position]
    if len({r['season'] for r in recent}) != len(recent):
        raise ValueError('Duplicate player position season')
    outs = 0.; runs = 0.; missing_outs = 0; trace = []
    for r in sorted(recent, key=lambda r: r['season']):
        n = r['native_outs']; value = r['dp_runs']; weight = .5 ** (origin-r['season'])
        if n < 0 or not math.isfinite(n) or (value is not None and not math.isfinite(value)):
            raise ValueError('Invalid source exposure or DP runs')
        valid = bool(r['exposure_valid']) and value is not None and n > 0
        if valid:
            outs += weight*n; runs += weight*value
        else:
            missing_outs += r['official_outs']
        trace.append(dict(source=r, recency_weight=weight, used=valid,
            weighted_outs=weight*n if valid else 0., weighted_runs=weight*value if valid else None))
    return dict(dp_history_outs=outs, dp_history_runs=runs,
        dp_history_seasons=sum(t['used'] for t in trace), dp_missing_history_official_outs=missing_outs,
        dp_history_left_truncated=origin-2 < 2016,
        dp_raw_rate=RATE_OUTS*runs/outs if outs else None,
        dp_reliability=outs/(outs+PRIOR_OUTS), neutral=0.,
        candidate=RATE_OUTS*runs/(outs+PRIOR_OUTS), dp_prior_outs=PRIOR_OUTS,
        fallback=outs == 0, trace=trace)


def profile(r):
    age = r['age']; outs = r['dp_history_outs']
    return (r['position'], 'unknown' if age is None else '<=24' if age <= 24 else '25-29' if age <= 29 else '30+',
        '<1500' if outs < 1500 else '1500-4499' if outs < 4500 else '4500+')


def score(rows, arm):
    counts = Counter(r['player_id'] for r in rows)
    w = np.array([1./counts[r['player_id']] for r in rows])
    e = np.array([r[arm]-r['quality_rate'] for r in rows])
    return dict(rows=len(rows), people=len(counts), rmse=float(np.sqrt(np.average(e*e, weights=w))),
        mae=float(np.average(np.abs(e), weights=w)), bias=float(np.average(e, weights=w)),
        oracle_exposure_predicted_runs=sum(r[arm]*r['future_outs']/RATE_OUTS for r in rows),
        oracle_exposure_actual_runs=sum(r['future_runs'] for r in rows))


def interval(rows, seed):
    groups = defaultdict(list)
    for r in rows:
        groups[r['player_id']].append(r)
    losses = np.array([[np.mean([(r[a]-r['quality_rate'])**2 for r in rs]) for a in ('candidate', 'neutral')]
        for rs in groups.values()])
    rng = np.random.default_rng(seed); differences = []
    for _ in range(2000):
        sample = losses[rng.integers(len(losses), size=len(losses))]
        differences.append(float(np.sqrt(sample[:, 0].mean())-np.sqrt(sample[:, 1].mean())))
    return dict(seed=seed, draws=2000, difference=float(np.sqrt(losses[:, 0].mean())-np.sqrt(losses[:, 1].mean())),
        interval_95=np.quantile(differences, [.025, .975]).tolist())
