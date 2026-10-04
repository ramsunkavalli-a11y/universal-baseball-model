"""Proper offense scores and source-to-fit player evidence, no promotion."""
import json
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from scipy.optimize import brentq
from scipy.stats import norm
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_offense_risk import fit_rate_variances, offense_distribution
from universal_baseball.hitter_workload_risk import mixture_pmf
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from universal_baseball.histogram_prediction_trace import trace
from evaluate_hitter_readiness_v49 import logit_trace
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_offense_risk as e

FIXED = [(592450, 2024), (665742, 2023), (701762, 2024), (694671, 2023),
         (624413, 2018), (668804, 2018), (702616, 2023), (474832, 2023), (677551, 2023)]
ARMS = ['fixed', 'constant', 'sample']


def equal_year(g, col):
    return float(g.group_by('target_year').agg(pl.col(col).mean())[col].mean())


def paired(g, reference):
    years, yi = np.unique(g['target_year'].to_numpy(), return_inverse=True)
    players, pi = np.unique(g['player_id'].to_numpy(), return_inverse=True)
    den = np.zeros((len(players), len(years))); num = den.copy()
    np.add.at(den, (pi, yi), 1)
    np.add.at(num, (pi, yi), (g['sample_pinball']-g[reference+'_pinball']).to_numpy())
    rng = np.random.default_rng(804); draws = []
    for _ in range(1000):
        w = np.bincount(rng.integers(0, len(players), len(players)), minlength=len(players))
        d = w @ den
        if (d > 0).all():
            draws.append(float(np.mean((w @ num)/d)))
    return dict(reference=reference, estimate=float(np.mean(num.sum(0)/den.sum(0))),
                lower=float(np.quantile(draws, .025)), upper=float(np.quantile(draws, .975)),
                draws=len(draws), qualification='Nominal player-clustered historical development interval')


def scalar_quantiles(pmf, rate, rep, a, b):
    n = np.arange(1, 801); mu = n*(rate/600+rep)
    if a is None:
        order = sorted(zip([0., *mu], pmf), key=lambda t: t[0])
        answers = []
        for alpha in [.1, .5, .9]:
            total = 0
            for value, mass in order:
                total += mass
                if total >= alpha-1e-14:
                    answers.append(float(value)); break
        return answers
    sd = n/600*np.sqrt(np.maximum(a+b*600/n, 1e-8))
    def continuous(x):
        return float(np.dot(pmf[1:], norm.cdf(x, loc=mu, scale=sd)))
    low0 = continuous(0); high0 = low0+pmf[0]; answers = []
    for alpha in [.1, .5, .9]:
        if low0 <= alpha <= high0:
            answers.append(0.); continue
        def cdf(x):
            return continuous(x)+(pmf[0] if x >= 0 else 0)-alpha
        answers.append(float(brentq(cdf, min(0., float((mu-14*sd).min())),
                                   max(0., float((mu+14*sd).max())), xtol=1e-11)))
    return answers


def main():
    assert not (e.OUT/'scores.json').exists(), 'Preserve original results'
    pre = e.read(e.OUT/'preflight.json'); report = e.read(e.OUT/'fit-report.json')
    e.check_hashes(pre['input_hashes'])
    assert sha256_file(e.WORK/'predictions.parquet') == report['output_sha256']
    base = pl.read_parquet(e.current.OUT/'scored-predictions.parquet').sort('row_id')
    new = pl.read_parquet(e.WORK/'predictions.parquet').sort('row_id')
    originals = [c for c in new.columns if c in base.columns]
    assert new.select(originals).equals(base.select(originals))
    q = base.hstack(new.select([c for c in new.columns if c not in base.columns]))
    f = e.context(); replayed = set(); variance_replays = 0; distribution_rows = 0
    with threadpool_limits(limits=2):
        for cell in report['cells']:
            e.check_hashes(cell['output_hashes'])
            for h in cell['nested_heads']:
                e.check_hashes(h['output_hashes'])
                if h['model_path'] in replayed:
                    continue
                val = f.filter(pl.col('row_id').is_in(h['validation_row_ids'])).sort('row_id')
                saved = pl.read_parquet(h['prediction_path']).sort('row_id')
                assert saved['row_id'].equals(val['row_id'])
                model = joblib.load(h['model_path'])
                assert np.allclose(model.predict(safe_matrix(val, pre['rate_features'])), saved['nested_rate'], atol=1e-10, rtol=0)
                replayed.add(h['model_path'])
            cal = pl.read_parquet(cell['calibration_path'])
            pars = fit_rate_variances((cal['common_rate_label']-cal['nested_rate']).to_numpy(), cal['next_pa'].to_numpy(), weights(cal))
            assert pars == cell['variance_parameters']; variance_replays += 1
            g = q.filter((pl.col('origin_year') == cell['year']) & (pl.col('outer_fold') == cell['fold']))
            for start in range(0, len(g), 96):
                z = g.slice(start, 96)
                pmf = mixture_pmf(z['preseason_p'], z['preseason_conditional_pa'], cell['workload_concentration'])
                for arm, a, b in [('fixed', None, 0), ('constant', pars['constant_variance'], 0),
                                  ('sample', pars['sample_dependent']['a'], pars['sample_dependent']['b'])]:
                    fresh = offense_distribution(pmf, z['preseason_rate'], z['origin_replacement_rate'], z['next_value'],
                        a=a, b=b, origin_index=z['origin_index'], unit=UNIT, event_min=float(VALUES.min()), event_max=float(VALUES.max()))
                    for name, values in fresh.items():
                        assert np.allclose(values, z[arm+'_'+name], atol=1e-10, rtol=0), name
                distribution_rows += len(z)
            print(f'Replayed risks {cell["year"]}/{cell["fold"]}', flush=True)
    for arm in ARMS:
        for event, actual in [('negative', q['next_value'].to_numpy() < 0), ('two', q['next_value'].to_numpy() >= 2)]:
            actual = actual.astype(float)
            p = q[arm+'_p_'+event].to_numpy(); clipped = np.clip(p, 1e-12, 1-1e-12)
            q = q.with_columns(pl.Series(arm+'_brier_'+event, (p-actual)**2),
                pl.Series(arm+'_log_'+event, -actual*np.log(clipped)-(1-actual)*np.log1p(-clipped)))
    profiles = pl.read_parquet(e.OUT/'calibration-profile-support.parquet').select('row_id', 'calibration_people')
    q = q.join(profiles, on='row_id', validate='1:1')
    public = (pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null()
    assert q.filter(public).height == 2627
    scopes = [('all', q), ('public', q.filter(public)), ('current_MLB', q.filter(pl.col('pa_0') > 0)),
              ('upper_never', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Upper minors'))),
              ('lower_never', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Lower minors'))),
              ('absent_prior', q.filter((pl.col('prior_debut') == 1) & (pl.col('pa_0') == 0))),
              ('thin_new_draft', q.filter((pl.col('draft_known') == 1) & (pl.col('draft_year') == pl.col('origin_year')) &
                (pl.col('minor_pa_0')+pl.col('minor_pa_1')+pl.col('minor_pa_2')+pl.col('pa_0')+pl.col('pa_1')+pl.col('pa_2') < 150))),
              ('active_outcomes_diagnostic', q.filter(pl.col('next_pa') > 0)),
              ('no_calibration_profile', q.filter(pl.col('calibration_people') == 0))]
    scopes.extend(('origin_'+str(y), q.filter(pl.col('origin_year') == y)) for y in sorted(q['origin_year'].unique()))
    metrics = ['pinball', 'interval_score', 'coverage', 'width', 'impossible_mass', 'brier_negative', 'log_negative', 'brier_two', 'log_two']
    scores, intervals = [], []
    with threadpool_limits(limits=2):
        for name, g in scopes:
            if g.is_empty():
                continue
            scores.append(dict(scope=name, rows=len(g), people=g['player_id'].n_unique(),
                scores={arm: {metric: equal_year(g, arm+'_'+metric) for metric in metrics} for arm in ARMS},
                expected_pa=float(g['preseason_pa'].sum()), actual_pa=int(g['next_pa'].sum()),
                expected_value=float(g['preseason_value'].sum()), actual_value=float(g['next_value'].sum()),
                zero_calibration_people=int((g['calibration_people'] == 0).sum()),
                below20_calibration_people=int((g['calibration_people'] < 20).sum()),
                expected_negative={arm: float(g[arm+'_p_negative'].sum()) for arm in ARMS}, actual_negative=int((g['next_value'] < 0).sum()),
                expected_two={arm: float(g[arm+'_p_two'].sum()) for arm in ARMS}, actual_two=int((g['next_value'] >= 2).sum())))
            if name in ['all', 'public', 'current_MLB', 'upper_never', 'lower_never', 'absent_prior']:
                intervals.extend(dict(scope=name, **paired(g, ref)) for ref in ['fixed', 'constant'])
    e.write(e.OUT/'scores.json', scores); e.write(e.OUT/'intervals.json', intervals)
    q.write_parquet(e.WORK/'scored-predictions.parquet')
    chosen = {}
    def choose(g, reason):
        if len(g): chosen.setdefault(g['row_id'][0], []).append(reason)
    for pid, year in FIXED:
        choose(q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year)), 'fixed before fits')
    for arm in ['fixed', 'constant']:
        changes = q.with_columns((pl.col(arm+'_pinball')-pl.col('sample_pinball')).alias('gain'))
        choose(changes.sort('gain', descending=True), 'largest gain versus '+arm)
        choose(changes.sort('gain'), 'largest harm versus '+arm)
    errors = q.with_columns((pl.col('preseason_value')-pl.col('next_value')).alias('error'))
    choose(errors.sort('error', descending=True), 'major false high mean')
    choose(errors.sort('error'), 'major false low mean')
    choose(errors.filter(pl.col('next_pa').is_between(200, 600)).sort(pl.col('error').abs()), 'ordinary active mean')
    counts = pl.scan_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('season') <= 2025).collect()
    cells = {(c['year'], c['fold']): c for c in report['cells']}; cases = []
    with threadpool_limits(limits=2):
        for rid, selection in chosen.items():
            row = q.filter(pl.col('row_id') == rid).row(0, named=True)
            ft = f.filter(pl.col('row_id') == rid); y, k = row['origin_year'], row['outer_fold']; cell = cells[y, k]
            model = joblib.load(cell['outer_rate_model']['path']); x = safe_matrix(ft, pre['rate_features'])[0]
            contributions = x*model.coef_
            assert np.isclose(model.intercept_+contributions.sum(), row['preseason_rate'], atol=1e-10)
            paths = {}
            point_receipt = e.read(e.current.OUT/f'fit-{y}-{k}.json')
            point_names = e.read(e.current.OUT/'preflight.json')['pa_features']
            for head in point_receipt['heads']:
                assert sha256_file(Path(head['path'])) == head['sha256']
                m = joblib.load(head['path']); px = ft.select(point_names).to_numpy()[0]
                if head['head'] == 'participation':
                    assert np.isclose(m.predict_proba(px[None])[0, 1], row['preseason_raw_p'], atol=1e-10)
                    paths['participation'] = logit_trace(m, px, point_names)
                else:
                    assert np.isclose(m.predict(px[None])[0], row['preseason_raw_conditional_pa'], atol=1e-10)
                    paths['conditional_pa'] = trace(m, px, point_names)
            pars = cell['variance_parameters']; pmf = mixture_pmf([row['preseason_p']], [row['preseason_conditional_pa']], cell['workload_concentration'])[0]
            independently = {}
            for arm, a, b in [('fixed', None, 0), ('constant', pars['constant_variance'], 0),
                              ('sample', pars['sample_dependent']['a'], pars['sample_dependent']['b'])]:
                ans = scalar_quantiles(pmf, row['preseason_rate'], row['origin_replacement_rate'], a, b)
                assert np.allclose(ans, [row[arm+'_q'+str(j)] for j in [10, 50, 90]], atol=1e-8, rtol=0)
                independently[arm] = ans
            peers = q.filter((pl.col('origin_year') == y) & (pl.col('player_id') != row['player_id']) &
                (pl.col('prior_debut') == row['prior_debut']) & (pl.col('stage') == row['stage'])).with_columns(
                (((pl.col('age')-row['age'])/3)**2 + ((pl.col('minor_pa_0')-row['minor_pa_0'])/250)**2 +
                 ((pl.col('pa_0')-row['pa_0'])/250)**2 + (pl.col('pooled_mlb_quality')-row['pooled_mlb_quality'])**2 +
                 2*(pl.col('new_scout_rank_score_0')-row['new_scout_rank_score_0'])**2 +
                 (pl.col('source_position') != row['source_position']).cast(pl.Float64)).alias('distance')).sort('distance', 'player_id').head(4)
            cases.append(dict(origin=row, selection=selection, information_date=point_receipt['information_date'],
                source_history=counts.filter((pl.col('player_id') == row['player_id']) & pl.col('season').is_between(y-2, y)).sort('season', 'bucket').to_dicts(),
                observed_target_counts=counts.filter((pl.col('player_id') == row['player_id']) & (pl.col('season') == y+1) & (pl.col('bucket') == 'MLB')).to_dicts(),
                actual_rate_inputs=ft.select(pre['rate_features']).row(0, named=True),
                actual_opportunity_inputs=ft.select(point_names).row(0, named=True), point_paths=paths,
                rate_intercept=float(model.intercept_), rate_contributions=dict(zip(pre['rate_features'], contributions.tolist())),
                variance_parameters=pars, calibration_path=cell['calibration_path'],
                calibration_people=cell['calibration_people'], calibration_rows=cell['calibration_rows'],
                pa_probability_mass=pmf.tolist(), independent_quantiles=independently,
                peers=peers.select('player_id', 'player_name', 'age', 'source_position', 'pa_0', 'minor_pa_0', 'pooled_mlb_quality',
                    'new_scout_rank_score_0', 'preseason_p', 'preseason_pa', 'preseason_rate', 'preseason_value',
                    'sample_q10', 'sample_q50', 'sample_q90', 'next_pa', 'next_value', 'distance').to_dicts(),
                peer_limit='Origin-known broad stage, age, position, exposure, MLB quality and rank; minor hitting and exact highest level are not fully matched',
                player_walkthrough_status='pending'))
    e.write(e.OUT/'cases.json', cases)
    paths = [Path(__file__), e.OUT/'preflight.json', e.OUT/'fit-report.json', e.OUT/'scores.json', e.OUT/'intervals.json', e.OUT/'cases.json', e.WORK/'scored-predictions.parquet']
    e.write(e.OUT/'verification.json', dict(nested_heads_replayed=len(replayed), variance_fits_replayed=variance_replays,
        distribution_rows_replayed=distribution_rows, original_columns_exact=True, independent_case_quantiles=len(cases)*9,
        cases=len(cases), player_walkthrough_status='pending', protected_outcomes_used=False,
        output_hashes={str(p): sha256_file(p) for p in paths}))
    for s in scores[:9]:
        print(s['scope'], {a: {m: round(s['scores'][a][m], 6) for m in ['pinball', 'coverage', 'impossible_mass']} for a in ARMS}, flush=True)
    for c in cases:
        r = c['origin']; print('CASE', r['row_id'], r['player_name'], r['origin_year'], c['selection'],
            'means', r['preseason_pa'], r['preseason_rate'], r['preseason_value'],
            'ranges', c['independent_quantiles'], 'actual', r['next_pa'], r['next_value'], flush=True)


if __name__ == '__main__':
    main()
