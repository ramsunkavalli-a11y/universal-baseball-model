"""Score locked history/calibration candidates without selecting a replacement."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_history_calibration_v1 import OUT, SOURCE, MAIN
from fit_hitter_arrival_coherence_v1 import save
from score_hitter_detail_arrival_v1 import metrics, paired, GROUPS
from universal_baseball.storage import sha256_file

PATH = 'path0__level_path__'
SLICES = {
    'all_prospects': pl.lit(True),
    'young_advancing': (pl.col('age') <= 23) & (pl.col(PATH+'primary_level_change') > 0),
    'short_current': pl.col('pa_lag0') < 400,
    'first_at_level': pl.col(PATH+'prior_seasons_at_primary') == 0,
    'substantial_repeat': pl.col(PATH+'substantial_same_level_repeat') == 1,
    'partial_promotion_return': pl.col(PATH+'returned_after_partial_promotion') == 1,
    'upper': pl.col('stage') == 'Upper minors',
    'lower': pl.col('stage') == 'Lower minors',
}


def ranks(frame):
    result = {}
    for fraction in (.05, .10):
        captures = []
        for (year,), f in frame.partition_by('origin_year', as_dict=True).items():
            n = int(np.ceil(f.height*fraction))
            top = f.sort(['probability', 'player_id'], descending=[True, False]).head(n)
            captures.append({'origin': year, 'selected': n, 'successes': int(top['actual'].sum()),
                             'total_successes': int(f['actual'].sum())})
        result[str(fraction)] = {'by_origin': captures,
                                'successes': sum(c['successes'] for c in captures),
                                'selected': sum(c['selected'] for c in captures)}
    return result


def summarize(f):
    return {arm: metrics(g) for (arm,), g in f.partition_by('arm', as_dict=True).items()}


def matched(candidate, reference):
    j = candidate.join(reference.select('origin_year', 'player_id', 'target',
                       pl.col('probability').alias('reference_probability')),
                       on=['origin_year', 'player_id', 'target'], how='inner', validate='1:1')
    b = j.with_columns(pl.col('reference_probability').alias('probability'))
    return {'candidate': metrics(j), 'reference': metrics(b), 'paired': paired(j, b)}


def main():
    manifest = json.loads((OUT/'fit-manifest.json').read_text())
    for n, h in manifest['files'].items(): assert sha256_file(OUT/n) == h
    f = pl.read_parquet(OUT/'predictions.parquet')
    source = pl.read_parquet(SOURCE/'input-panel.parquet').select('origin_year', 'player_id', 'pa_lag0',
        PATH+'primary_level_change', PATH+'prior_seasons_at_primary', PATH+'substantial_same_level_repeat',
        PATH+'returned_after_partial_promotion')
    f = f.join(source, on=['origin_year', 'player_id'], how='left', validate='m:1')
    old = pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold') & ~pl.col('pandemic'))
    refs = pl.read_parquet(SOURCE/'reference-predictions.parquet')
    report = {'targets': {}, 'stress': {}, 'protected_outcomes_used': False, 'production_forecasts_changed': False}
    for target in MAIN:
        print('Scoring '+target, flush=True)
        t = f.filter((pl.col('target') == target) & ~pl.col('pandemic'))
        prospects = t.filter(pl.col('prospect'))
        m = summarize(prospects)
        comparisons = {}
        for a, b in [('HC', 'R'), ('H', 'R'), ('RC', 'R'), ('HC', 'H')]:
            comparisons[a+'_minus_'+b] = paired(prospects.filter(pl.col('arm') == a), prospects.filter(pl.col('arm') == b))
        candidate = prospects.filter(pl.col('arm') == 'HC')
        controls = {}
        for engine in ('lightgbm', 'logistic'):
            reference = old.filter((pl.col('target') == target) & (pl.col('arm') == 'B2') & (pl.col('engine') == engine))
            controls[engine+'_B2'] = matched(candidate, reference)
        for (name,), r in refs.filter(pl.col('target') == target).partition_by('model', as_dict=True).items():
            controls[name] = matched(candidate, r)
        slices = {name: summarize(prospects.filter(expr)) for name, expr in SLICES.items()}
        hc = m['HC']; comp = comparisons['HC_minus_R']
        gates = {
            'support': hc['origins'] >= 3 and hc['observed'] >= 30,
            'both_paired_intervals': all(comp[s]['interval95'][1] < 0 for s in ('brier', 'log_loss')),
            'majority_origins': all(comp[s]['improving_origins'] > hc['origins']/2 for s in ('brier', 'log_loss')),
            'calibration': hc['ratio'] is not None and .75 <= hc['ratio'] <= 1.25,
            'stage_guards': all(slices[g]['HC'][s] <= 1.1*slices[g]['R'][s]
                                for g in ('upper', 'lower') if slices[g]['HC']['rows'] >= 200 and slices[g]['HC']['observed'] >= 30
                                for s in ('brier', 'log_loss')),
            'B2_point_scores': all(controls['lightgbm_B2']['candidate'][s] < controls['lightgbm_B2']['reference'][s]
                                   for s in ('brier', 'log_loss')),
            'ensemble_point_scores': (all(controls['earlier_ensemble']['candidate'][s] < controls['earlier_ensemble']['reference'][s]
                                         for s in ('brier', 'log_loss')) if 'earlier_ensemble' in controls else None),
        }
        status = ('development_probability_candidate' if all(gates.values()) else 'not_confirmed_no_upgrade')
        report['targets'][target] = {
            'status': status, 'gates': gates, 'prospects': m, 'comparisons': comparisons,
            'controls': controls, 'slices': slices,
            '2021': summarize(prospects.filter(pl.col('origin_year') == 2021)),
            'other_years': summarize(prospects.filter(pl.col('origin_year') != 2021)),
            'ranking': {a: ranks(prospects.filter(pl.col('arm') == a)) for a in ('R', 'RC', 'H', 'HC')},
            'other_cohorts': {g: summarize(t.filter(expr)) for g, expr in GROUPS.items() if g != 'prospects'},
        }
        report['stress'][target] = summarize(f.filter((pl.col('target') == target) & pl.col('pandemic') & pl.col('prospect')))
    report['hashes'] = {n: sha256_file(OUT/n) for n in ('prefit-manifest.json', 'fit-manifest.json', 'predictions.parquet')}
    report['score_code_sha256'] = sha256_file(Path(__file__))
    save(OUT/'score-report.json', report)
    print(json.dumps({t: {'status': r['status'], 'gates': r['gates'],
          'metrics': {a: {k: v[k] for k in ('observed', 'expected', 'brier', 'log_loss')} for a, v in r['prospects'].items()}}
          for t, r in report['targets'].items()}, indent=2))


if __name__ == '__main__': main()
