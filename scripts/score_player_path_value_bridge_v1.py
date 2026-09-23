"""Predeclared distribution and upper-tail gates; no post-score tuning."""
from __future__ import annotations

import json
import numpy as np
import polars as pl

from fit_hitter_arrival_coherence_v1 import save
from fit_player_path_value_bridge_v1 import OUT
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.player_path_distribution import EVENTS
from universal_baseball.storage import sha256_file


LOSSES = ['crps', 'mse', 'energy', 'coverage80', 'width80', 'delivered_mse']
LOSSES += ['brier_'+e for e in EVENTS] + ['log_'+e for e in EVENTS]


def average(f, col):
    return float(f.group_by('origin_year').agg(pl.col(col).mean())[col].mean())


def metrics(f):
    if not f.height:
        return None
    result = {'rows': f.height, 'origins': sorted(f['origin_year'].unique().to_list())}
    result.update({c: average(f, c) for c in LOSSES})
    result['rmse'] = float(np.sqrt(result['mse']))
    result['delivered_rmse'] = float(np.sqrt(result['delivered_mse']))
    result['events'] = {e: {'observed': int(f['actual_'+e].sum()), 'predicted': float(f['p_'+e].sum()),
        'predicted_observed_ratio': float(f['p_'+e].sum()/f['actual_'+e].sum()) if f['actual_'+e].sum() else None} for e in EVENTS}
    return result


def paired(f, baseline, loss='crps'):
    keys = ['origin_year', 'player_id']
    left = f.filter(pl.col('method') == 'F1').select(*keys, pl.col(loss).alias('candidate'))
    right = f.filter(pl.col('method') == baseline).select(*keys, pl.col(loss).alias('baseline'))
    joined = left.join(right, on=keys, how='inner', validate='1:1')
    assert joined.height == left.height == right.height
    return compare_losses(joined, 'candidate', 'baseline')


def main():
    f = pl.read_parquet(OUT/'predictions.parquet')
    hist = f.filter(pl.col('origin_year') < 2025)
    normal = hist.filter((pl.col('horizon') == 3) & ~pl.col('pandemic') & ~pl.col('cold'))
    methods = {m: metrics(normal.filter(pl.col('method') == m)) for m in ('B0', 'F0', 'F1')}
    comparisons = {m: paired(normal, m) for m in ('B0', 'F0')}
    annual = {str(y): {m: metrics(normal.filter((pl.col('origin_year') == y) & (pl.col('method') == m)))
                      for m in methods} for y in (2016, 2021, 2022)}
    groups = {'Never-debuted minors': pl.col('prospect'), 'Recent debut': pl.col('recent_debut'),
              'Current MLB': pl.col('stage') == 'Current MLB',
              'Upper minors': pl.col('stage') == 'Upper minors',
              'Lower minors': pl.col('stage') == 'Lower minors',
              'Age under 23': pl.col('age') < 23, 'Age 23+': pl.col('age') >= 23}
    subgroup = {}
    for name, mask in groups.items():
        g = normal.filter(mask)
        subgroup[name] = {m: metrics(g.filter(pl.col('method') == m)) for m in methods}
    tail = {}
    for e in EVENTS:
        ratios = methods['F1']['events'][e]
        tail[e] = {'supported': ratios['observed'] >= 30, **ratios,
                   'brier_not_worse_than_F0': methods['F1']['brier_'+e] <= methods['F0']['brier_'+e],
                   'log_not_worse_than_F0': methods['F1']['log_'+e] <= methods['F0']['log_'+e]}
    top_rows = []
    for (year, method), g in normal.partition_by('origin_year', 'method', as_dict=True).items():
        for e in EVENTS:
            top = g.sort('p_'+e, descending=True).head(max(1, int(np.ceil(.1*g.height))))
            top_rows.append({'origin': year, 'method': method, 'event': e, 'n': top.height,
                             'predicted': float(top['p_'+e].sum()), 'observed': int(top['actual_'+e].sum())})
    gates = {
        'three_normal_origins': len(methods['F1']['origins']) >= 3,
        'crps_intervals': all(x['interval95'][1] < 0 for x in comparisons.values()),
        'majority_origins': all(sum(a['F1']['crps'] < a[m]['crps'] for a in annual.values()) >= 2 for m in ('B0', 'F0')),
        'mean_error': all(methods['F1']['mse'] <= 1.05*methods[m]['mse'] for m in ('B0', 'F0'))
                      and methods['F1']['mse'] <= 1.05*methods['F1']['delivered_mse'],
        'event_scores': all(methods['F1'][metric+'_'+e] <= 1.05*methods[m][metric+'_'+e]
                            for e in EVENTS for metric in ('brier', 'log') for m in ('B0', 'F0')),
        'upper_tail': all(tail[e]['supported'] and tail[e]['brier_not_worse_than_F0'] and tail[e]['log_not_worse_than_F0']
                          and .75 <= tail[e]['predicted_observed_ratio'] <= 1.25 for e in EVENTS[1:]),
        'starting_group_crps': all(g['F1']['crps'] <= 1.1*g[m]['crps'] for g in subgroup.values()
            if g['F1'] and g['F1']['rows'] >= 200 and len(g['F1']['origins']) >= 3 for m in ('B0', 'F0')),
    }
    report = {'status': 'development_supported_not_promoted' if all(gates.values()) else 'reject_current_path_challenger',
              'gates': gates, 'normal_h3': methods, 'paired_crps': comparisons, 'by_origin': annual,
              'subgroups': subgroup, 'tail': tail, 'top_decile': top_rows,
              'nonoverlapping_origin_check': {str(y): annual[str(y)] for y in (2016, 2021)},
              'stress': {}, 'cold': {}, 'target': 'batting_plus_replacement_not_whole_war',
              'production_forecasts_changed': False, 'dollar_values_available': False,
              'protected_outcomes_used': False, 'source_sha256': sha256_file(OUT/'predictions.parquet')}
    for h in (3, 6):
        stress = hist.filter((pl.col('horizon') == h) & pl.col('pandemic') & ~pl.col('cold'))
        report['stress'][str(h)] = {m: metrics(stress.filter(pl.col('method') == m)) for m in methods}
    cold = hist.filter(pl.col('cold'))
    report['cold'] = {m: metrics(cold.filter(pl.col('method') == m)) for m in methods}
    save(OUT/'score-report.json', report)
    print(json.dumps({'status': report['status'], 'gates': gates, 'normal_h3': methods, 'paired_crps': comparisons}, indent=2))


if __name__ == '__main__':
    main()
