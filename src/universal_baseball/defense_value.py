"""Separate quality, defensive opportunities and custom expanded player value."""

import math
import numpy as np

POSITION_RUNS = {2: 12.5, 3: -12.5, 4: 2.5, 5: 2.5, 6: 7.5,
                 7: -7.5, 8: 2.5, 9: -7.5}
OPPORTUNITY_ARMS = ('ratio', 'repair', 'transition')
QUALITY_ARMS = ('neutral', 'history', 'calibrated')


def position_value(row, prefix):
    """Research DH-start approximation, not published WAR reconstruction."""
    return sum(row[f'{prefix}_{p}']*v/4374. for p, v in POSITION_RUNS.items()) - 17.5*row[f'{prefix}_10']/162.


def quality(channel_row, arm):
    if arm == 'neutral': return 0.
    assert arm in ('history', 'calibrated')
    if (arm == 'calibrated' and channel_row['channel'].startswith('range_') and
        channel_row['quality_evidence_observed'] and channel_row['range_calibration_fit_allowed'] and
        channel_row['saved_range_calibration'] is not None):
        return channel_row['saved_range_calibration']
    return channel_row['history_rate']


def opportunity(row, channel, arm):
    return row[f'{arm}_{channel[-1]}'] if channel.startswith('range_') else row[f'{arm}_native_{channel}']


def predicted_runs(row, channel_row, opportunity_arm, quality_arm):
    n = opportunity(row, channel_row['channel'], opportunity_arm)
    assert math.isfinite(n) and n >= 0 and channel_row['rate_unit'] > 0
    return n*quality(channel_row, quality_arm)/channel_row['rate_unit']


def score_rows(rows, fields, target):
    """One row per player/origin; output per-origin and equally weighted origins."""
    origins = sorted({r['origin_year'] for r in rows})
    per_origin = []
    for y in origins:
        selected = [r for r in rows if r['origin_year'] == y and r[target] is not None]
        assert len({r['row_id'] for r in selected}) == len(selected)
        if not selected: continue
        actual = np.array([r[target] for r in selected], float)
        for field in fields:
            p = np.array([r[field] for r in selected], float)
            assert np.isfinite(p).all() and np.isfinite(actual).all()
            e = p-actual
            per_origin.append(dict(origin=y, arm=field, rows=len(selected),
                rmse=float(np.sqrt(np.mean(e*e))), mae=float(np.mean(abs(e))),
                bias=float(e.mean()), actual_total=float(actual.sum()), predicted_total=float(p.sum())))
    equal = []
    for field in fields:
        parts = [r for r in per_origin if r['arm'] == field]
        if parts: equal.append(dict(arm=field, origins=len(parts),
            mean_origin_rmse=float(np.mean([p['rmse'] for p in parts])),
            mean_origin_mae=float(np.mean([p['mae'] for p in parts])),
            mean_origin_bias=float(np.mean([p['bias'] for p in parts]))))
    return dict(per_origin=per_origin, equal_origin=equal)


def paired_interval(rows, left, right, target, draws=2000, seed=712001):
    selected = [r for r in rows if r[target] is not None]
    if not selected: return None
    people = sorted({r['player_id'] for r in selected}); origins = sorted({r['origin_year'] for r in selected})
    pi, yi = {p:i for i,p in enumerate(people)}, {y:i for i,y in enumerate(origins)}
    loss = np.zeros((len(people),len(origins),2)); counts = np.zeros((len(people),len(origins)))
    for r in selected:
        i,j = pi[r['player_id']],yi[r['origin_year']]
        assert counts[i,j] == 0
        counts[i,j] = 1
        loss[i,j] = [(r[f]-r[target])**2 for f in (left,right)]
    base = np.sqrt(loss.sum(axis=0)/counts.sum(axis=0)[:,None]).mean(axis=0)
    rng = np.random.default_rng(seed); diffs = []
    for _ in range(draws):
        indices = rng.integers(len(people),size=len(people))
        denominator = counts[indices].sum(axis=0)
        assert (denominator > 0).all()
        roots = np.sqrt(loss[indices].sum(axis=0)/denominator[:,None]).mean(axis=0)
        diffs.append(float(roots[0]-roots[1]))
    return dict(left=left,right=right,target=target,people=len(people),draws=draws,seed=seed,
                mean_origin_RMSE_difference=float(base[0]-base[1]),
                interval_95=np.quantile(diffs,[.025,.975]).tolist(),person_clustered=True,
                qualification='Nominal development uncertainty, not corrected for model selection or season shocks.')
