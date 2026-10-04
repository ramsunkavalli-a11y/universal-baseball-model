"""Matched count-risk scores, independent simulation audit and player evidence."""
import sys
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_event_count_risk import fit_count_laws, simulate, mixture_terms, tilt
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import EVENTS
from universal_baseball.storage import sha256_file
from universal_baseball.histogram_prediction_trace import trace
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
import evaluate_hitter_event_count_risk as e

ARMS = ['fixed', 'normal', 'independent', 'associated']
FIXED = [(592450, 2024), (665742, 2023), (701762, 2024), (694671, 2023),
         (624413, 2018), (668804, 2018), (702616, 2023), (474832, 2023),
         (677551, 2023), (660670, 2022), (592450, 2016), (666163, 2023), (605253, 2018)]


def equal_year(g, name):
    return float(g.group_by('target_year').agg(pl.col(name).mean())[name].mean())


def public():
    return (pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null()


def scopes(q):
    answer = [('all', q), ('public', q.filter(public())),
        ('current_MLB', q.filter(pl.col('pa_0') > 0)),
        ('upper_never', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Upper minors'))),
        ('lower_never', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Lower minors'))),
        ('absent_prior', q.filter((pl.col('prior_debut') == 1) & (pl.col('pa_0') == 0))),
        ('thin_new_draft', q.filter((pl.col('draft_known') == 1) & (pl.col('draft_year') == pl.col('origin_year')) &
            (pl.col('minor_pa_0')+pl.col('minor_pa_1')+pl.col('minor_pa_2')+pl.col('pa_0')+pl.col('pa_1')+pl.col('pa_2') < 150))),
        ('active_outcomes_diagnostic', q.filter(pl.col('next_pa') > 0)),
        ('no_calibration_profile', q.filter(pl.col('calibration_people') == 0))]
    answer.extend(('origin_'+str(y), q.filter(pl.col('origin_year') == y)) for y in sorted(q['origin_year'].unique()))
    return [(name, g) for name, g in answer if len(g)]


def paired(g, arm, reference):
    _, yi = np.unique(g['target_year'].to_numpy(), return_inverse=True)
    people, pi = np.unique(g['player_id'].to_numpy(), return_inverse=True)
    den = np.zeros((len(people), int(yi.max())+1)); num = den.copy()
    np.add.at(den, (pi, yi), 1)
    np.add.at(num, (pi, yi), (g[arm+'_pinball']-g[reference+'_pinball']).to_numpy())
    rng = np.random.default_rng(88004); draws = []
    for _ in range(1000):
        w = np.bincount(rng.integers(0, len(people), len(people)), minlength=len(people))
        d = w @ den
        if (d > 0).all(): draws.append(float(np.mean((w @ num)/d)))
    return dict(arm=arm, reference=reference, estimate=float(np.mean(num.sum(0)/den.sum(0))),
        lower=float(np.quantile(draws, .025)), upper=float(np.quantile(draws, .975)), draws=len(draws),
        qualification='Nominal player-clustered development interval; repeated historical selection not corrected')


def selected(q):
    chosen = {}
    def choose(g, reason):
        if len(g): chosen.setdefault(int(g['row_id'][0]), []).append(reason)
    for pid, year in FIXED:
        g = q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year))
        assert len(g) == 1, ('Fixed case missing', pid, year)
        choose(g, 'fixed before fitting')
    for ref in ['normal', 'independent']:
        z = q.with_columns((pl.col(ref+'_pinball')-pl.col('associated_pinball')).alias('gain'))
        choose(z.sort('gain', descending=True), 'largest gain versus '+ref)
        choose(z.sort('gain'), 'largest harm versus '+ref)
    z = q.with_columns((pl.col('preseason_value')-pl.col('next_value')).alias('error'))
    choose(z.sort('error', descending=True), 'major false high mean')
    choose(z.sort('error'), 'major false low mean')
    choose(z.filter(pl.col('next_pa').is_between(200, 600)).sort(pl.col('error').abs()), 'ordinary active mean')
    return chosen


def draw_row(r, cell, arm, draws=4096, replicate=0):
    par = cell['parameters'][arm]
    return simulate(np.array([r['reference_'+v] for v in EVENTS]), r['preseason_rate'],
        r['origin_index'], r['origin_replacement_rate'], r['preseason_p'],
        r['preseason_conditional_pa'], cell['workload_concentration'], par['phi'], par['beta'],
        row_id=r['row_id'], draws=draws, replicate=replicate)


def score():
    assert not (e.OUT/'scores.json').exists(), 'Preserve original scored result'
    pre = e.read(e.OUT/'preflight.json'); report = e.read(e.OUT/'fit-report.json')
    e.old.check_hashes(pre['input_hashes'])
    assert sha256_file(e.WORK/'predictions.parquet') == report['output_sha256']
    base = pl.read_parquet(e.old.WORK/'scored-predictions.parquet').sort('row_id')
    new = pl.read_parquet(e.WORK/'predictions.parquet').sort('row_id')
    shared = [c for c in new.columns if c in base.columns]
    assert new.select(shared).equals(base.select(shared))
    assert len(base) == 30506 and len(base.filter(public())) == 2627
    normal_cols = [c for c in base.columns if c.startswith('sample_')]
    q = base.with_columns([pl.col(c).alias('normal_'+c[7:]) for c in normal_cols])
    q = q.hstack(new.select([c for c in new.columns if c not in q.columns]))
    for arm in ['independent', 'associated']:
        assert np.allclose(q[arm+'_expected_value'], q['preseason_value'], atol=1e-10, rtol=0)
        assert q[arm+'_impossible_mass'].max() == 0
        for event, actual in [('negative', q['next_value'].to_numpy() < 0), ('two', q['next_value'].to_numpy() >= 2)]:
            y = actual.astype(float); p = q[arm+'_p_'+event].to_numpy(); z = np.clip(p, 1e-12, 1-1e-12)
            q = q.with_columns(pl.Series(arm+'_brier_'+event, (p-y)**2),
                pl.Series(arm+'_log_'+event, -y*np.log(z)-(1-y)*np.log1p(-z)))
    replay = []
    with threadpool_limits(limits=2):
        for cell, source in zip(report['cells'], pre['cells']):
            assert (cell['year'], cell['fold']) == (source['year'], source['fold'])
            e.old.check_hashes(cell['output_hashes']); e.old.check_hashes(source['artifact_hashes'])
            cal = pl.read_parquet(source['calibration_path'])
            fresh = fit_count_laws(cal['common_rate_label'], cal['next_pa'], cal['nested_rate'], cal['origin_index'],
                cal.select(['reference_'+v for v in EVENTS]).to_numpy(), cal['workload_log_center'], weights(cal))
            assert fresh == cell['parameters'], ('Calibration replay mismatch', cell['year'], cell['fold'])
            replay.append(dict(year=cell['year'], fold=cell['fold'], parameters_exact=True))
            print('Replayed count parameters', cell['year'], cell['fold'], flush=True)
    metrics = ['pinball', 'interval_score', 'coverage', 'width', 'impossible_mass', 'brier_negative', 'log_negative', 'brier_two', 'log_two']
    scores = []; intervals = []
    with threadpool_limits(limits=2):
        for name, g in scopes(q):
            scores.append(dict(scope=name, rows=len(g), people=g['player_id'].n_unique(),
                scores={a: {m: equal_year(g, a+'_'+m) for m in metrics} for a in ARMS},
                expected_pa=float(g['preseason_pa'].sum()), actual_pa=int(g['next_pa'].sum()),
                expected_value=float(g['preseason_value'].sum()), actual_value=float(g['next_value'].sum()),
                zero_calibration_people=int((g['calibration_people'] == 0).sum()),
                below20_calibration_people=int((g['calibration_people'] < 20).sum()),
                expected_negative={a: float(g[a+'_p_negative'].sum()) for a in ARMS},
                actual_negative=int((g['next_value'] < 0).sum()),
                expected_two={a: float(g[a+'_p_two'].sum()) for a in ARMS}, actual_two=int((g['next_value'] >= 2).sum())))
            if name in ['all', 'public', 'current_MLB', 'upper_never', 'lower_never', 'absent_prior']:
                intervals.extend(dict(scope=name, **paired(g, a, b)) for a, b in
                    [('associated', 'normal'), ('associated', 'independent'), ('independent', 'normal')])
    chosen = selected(q)
    q.write_parquet(e.WORK/'scored-predictions.parquet')
    e.write(e.OUT/'scores.json', scores); e.write(e.OUT/'intervals.json', intervals)
    e.write(e.OUT/'case-selection.json', [{'row_id': rid, 'reasons': reasons} for rid, reasons in chosen.items()])
    paths = [Path(__file__), e.OUT/'preflight.json', e.OUT/'fit-report.json', e.OUT/'scores.json',
        e.OUT/'intervals.json', e.OUT/'case-selection.json', e.WORK/'scored-predictions.parquet']
    e.write(e.OUT/'scoring-verification.json', dict(original_columns_exact=True, count_calibrations_replayed=70,
        replayed_cells=replay, zero_impossible_count_mass=True, cases=len(chosen),
        distribution_replay_status='selected and independent Monte Carlo audit pending; not all-row replay',
        player_walkthrough_status='pending', protected_outcomes_used=False,
        artifact_hashes={str(p): sha256_file(p) for p in paths}))
    for s in scores:
        print(s['scope'], {a: {m: round(s['scores'][a][m], 6) for m in ['pinball', 'coverage', 'width']} for a in ARMS}, flush=True)


def audit():
    assert not (e.OUT/'monte-carlo-audit.json').exists(), 'Preserve original numerical audit'
    note = e.read(e.OUT/'scoring-verification.json'); e.old.check_hashes(note['artifact_hashes'])
    q = pl.read_parquet(e.WORK/'scored-predictions.parquet').sort('row_id')
    report = e.read(e.OUT/'fit-report.json'); cells = {(c['year'], c['fold']): c for c in report['cells']}
    rng = np.random.default_rng(88004)
    extra = rng.permutation(q['row_id'].to_numpy())[:256].tolist()
    selected_ids = [c['row_id'] for c in e.read(e.OUT/'case-selection.json')]
    ids = set(q.filter(public())['row_id']) | set(extra) | set(selected_ids)
    auditrows = []
    with threadpool_limits(limits=2):
        for i, r in enumerate(q.filter(pl.col('row_id').is_in(ids)).iter_rows(named=True)):
            cell = cells[r['origin_year'], r['outer_fold']]; answer = {'row_id': r['row_id']}
            for arm in ['independent', 'associated']:
                draw = draw_row(r, cell, arm, 8192, 1)
                terms = mixture_terms(draw['values'], r['preseason_p'], r['next_value'])
                answer.update({arm+'_'+n: v for n, v in terms.items()})
                answer[arm+'_theoretical_mean'] = draw['expected_value']
                answer[arm+'_mean_standard_error'] = float(r['preseason_p']*np.std(draw['values'], ddof=1)/np.sqrt(8192))
            auditrows.append(answer)
            if (i+1) % 200 == 0: print('Independent Monte Carlo audit', i+1, '/', len(ids), flush=True)
    result = q.select('row_id', 'target_year', 'pa_0', 'steamer_index', 'zips_index', 'normal_pinball', 'preseason_value').join(
        pl.DataFrame(auditrows), on='row_id', how='inner', validate='1:1')
    assert len(result) == len(ids)
    result.write_parquet(e.WORK/'monte-carlo-audit.parquet')
    comparisons = []
    for arm in ['independent', 'associated']:
        main = q.filter(public()); check = result.filter(public())
        first = equal_year(main, arm+'_pinball')-equal_year(main, 'normal_pinball')
        second = equal_year(check, arm+'_pinball')-equal_year(check, 'normal_pinball')
        tolerance = .02*equal_year(main, 'normal_pinball')
        comparisons.append(dict(arm=arm, public_rows=len(check), original_difference=first,
            independent_difference=second, tolerance=tolerance,
            direction_stable=bool(np.sign(first) == np.sign(second)), absolute_change=abs(second-first),
            stable=bool(np.sign(first) == np.sign(second) and abs(second-first) <= tolerance)))
    e.write(e.OUT/'monte-carlo-audit.json', dict(audited_rows=len(ids), positive_draws=8192, replicate=1,
        deterministic_extra_row_ids=extra, selected_case_row_ids=selected_ids,
        public_comparisons=comparisons, numerical_ranking_stable=all(c['stable'] for c in comparisons),
        exact_integer_support=True, current_mean_unchanged=True,
        source_hashes=note['artifact_hashes'], artifact_sha256=sha256_file(e.WORK/'monte-carlo-audit.parquet'),
        player_walkthrough_status='pending', protected_outcomes_used=False))
    print(comparisons, flush=True)


def cases():
    assert not (e.OUT/'cases.json').exists(), 'Preserve original player evidence'
    note = e.read(e.OUT/'scoring-verification.json'); e.old.check_hashes(note['artifact_hashes'])
    q = pl.read_parquet(e.WORK/'scored-predictions.parquet'); f = e.old.context()
    cells = {(c['year'], c['fold']): c for c in e.read(e.OUT/'fit-report.json')['cells']}
    oldcells = {(c['year'], c['fold']): c for c in e.read(e.old.OUT/'fit-report.json')['cells']}
    names = e.read(e.old.OUT/'preflight.json')['rate_features']
    point_names = e.read(e.old.current.OUT/'preflight.json')['pa_features']
    counts = pl.scan_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet').filter(pl.col('season') <= 2025).collect()
    support = pl.read_parquet(e.OUT/'outer-support.parquet')
    answers = []
    with threadpool_limits(limits=2):
        for chosen in e.read(e.OUT/'case-selection.json'):
            rid = chosen['row_id']; r = q.filter(pl.col('row_id') == rid).row(0, named=True)
            ft = f.filter(pl.col('row_id') == rid); y, k = r['origin_year'], r['outer_fold']; cell = cells[y, k]
            h = oldcells[y, k]['outer_rate_model']; assert sha256_file(Path(h['path'])) == h['sha256']
            model = joblib.load(h['path']); x = safe_matrix(ft, names)[0]; contributions = x*model.coef_
            assert np.isclose(model.intercept_+contributions.sum(), r['preseason_rate'], atol=1e-10, rtol=0)
            point = e.read(e.old.current.OUT/f'fit-{y}-{k}.json'); paths = {}
            for h in point['heads']:
                assert sha256_file(Path(h['path'])) == h['sha256']
                m = joblib.load(h['path']); px = ft.select(point_names).to_numpy()[0]
                if h['head'] == 'participation':
                    assert np.isclose(m.predict_proba(px[None])[0, 1], r['preseason_raw_p'], atol=1e-10)
                    paths['participation'] = logit_trace(m, px, point_names)
                else:
                    assert np.isclose(m.predict(px[None])[0], r['preseason_raw_conditional_pa'], atol=1e-10)
                    paths['conditional_pa'] = trace(m, px, point_names)
            verified = {}; draws_hashes = {}
            for arm in ['independent', 'associated']:
                draw = draw_row(r, cell, arm)
                terms = mixture_terms(draw['values'], r['preseason_p'], r['next_value'])
                for name, value in terms.items():
                    assert np.isclose(value, r[arm+'_'+name], atol=1e-12, rtol=0), (rid, arm, name)
                dp = e.WORK/f'case-{rid}-{arm}-draws.parquet'
                pl.DataFrame({'pa': draw['pa'], 'value': draw['values'],
                    **{'count_'+v: draw['counts'][:, j] for j, v in enumerate(EVENTS)}}).write_parquet(dp)
                draws_hashes[str(dp)] = sha256_file(dp)
                verified[arm] = dict(terms=terms, theoretical_expected_value=draw['expected_value'],
                    workload_log_center=draw['center'], simulated_count_sum_exact=True,
                    min_positive_draw=float(draw['values'].min()), max_positive_draw=float(draw['values'].max()),
                    conditional_sample_mean=float(np.mean(draw['values'])),
                    event_profile_at_mean_pa=tilt(np.array([r['reference_'+v] for v in EVENTS]),
                        r['origin_index']+(r['preseason_rate']+cell['parameters'][arm]['beta']*
                            (np.log(r['preseason_conditional_pa'])-draw['center']))/UNIT)[0].tolist())
            peers = q.filter((pl.col('origin_year') == y) & (pl.col('player_id') != r['player_id']) &
                (pl.col('prior_debut') == r['prior_debut']) & (pl.col('stage') == r['stage'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+
                 ((pl.col('pa_0')-r['pa_0'])/250)**2+(pl.col('pooled_mlb_quality')-r['pooled_mlb_quality'])**2+
                 2*(pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2+
                 (pl.col('source_position') != r['source_position']).cast(pl.Float64)).alias('distance')).sort('distance', 'player_id').head(4)
            answers.append(dict(origin=r, selection=chosen['reasons'], information_date=point['information_date'],
                source_history=counts.filter((pl.col('player_id') == r['player_id']) & pl.col('season').is_between(y-2, y)).sort('season', 'bucket').to_dicts(),
                observed_target_counts=counts.filter((pl.col('player_id') == r['player_id']) & (pl.col('season') == y+1) & (pl.col('bucket') == 'MLB')).to_dicts(),
                actual_rate_inputs=ft.select(names).row(0, named=True), actual_opportunity_inputs=ft.select(point_names).row(0, named=True),
                point_paths=paths, rate_intercept=float(model.intercept_), rate_contributions=dict(zip(names, contributions.tolist())),
                count_parameters=cell['parameters'], workload_concentration=cell['workload_concentration'],
                verified_draws=verified, draw_artifact_hashes=draws_hashes,
                actual_training_support=support.filter(pl.col('row_id') == rid).to_dicts(),
                peers=peers.select('player_id', 'player_name', 'age', 'source_position', 'pa_0', 'minor_pa_0',
                    'pooled_mlb_quality', 'new_scout_rank_score_0', 'preseason_pa', 'preseason_rate', 'preseason_value',
                    'associated_q10', 'associated_q50', 'associated_q90', 'next_pa', 'next_value', 'distance').to_dicts(),
                peer_limit='Outcome-blind broad stage/age/position/exposure/MLB quality/rank; not a minor-performance or exact-level match',
                player_walkthrough_status='pending'))
            print('CASE', rid, r['player_name'], y, chosen['reasons'],
                'normal', [r['normal_q'+str(j)] for j in [10, 50, 90]],
                'independent', [r['independent_q'+str(j)] for j in [10, 50, 90]],
                'associated', [r['associated_q'+str(j)] for j in [10, 50, 90]],
                'actual', r['next_pa'], r['next_value'], 'beta', cell['parameters']['associated']['beta'], flush=True)
    e.write(e.OUT/'cases.json', answers)
    e.write(e.OUT/'case-replay-verification.json', dict(cases=len(answers), integer_draws_replayed=len(answers)*2*4096,
        quantiles_replayed=len(answers)*6, actual_saved_point_models_replayed=True,
        all_case_terms_exact=True, evidence_sha256=sha256_file(e.OUT/'cases.json'),
        player_walkthrough_status='pending', protected_outcomes_used=False))


if __name__ == '__main__':
    {'score': score, 'audit': audit, 'cases': cases}[sys.argv[1]]()
