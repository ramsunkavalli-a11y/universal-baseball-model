"""Replay absolute fits and trace actual production through learned forecasts."""
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_count_baseline import past_profile, assemble
from universal_baseball.hitter_mlb_events import reconstruct
from universal_baseball.hitter_mlb_detail import reconstruct as quality_source
from universal_baseball.hitter_compatible_value import labels, UNIT
from universal_baseball.hitter_error_geometry import decompose, change
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import annual_labels
from review_hitter_evidence_representation import rate_interval
from review_hitter_past_direct_value import summary, value_interval
from run_hitter_count_baseline import ROOT, GEN, OUT as COUNT, SHARED, FEATURES, REF, read, verify, matrix, source_data
from run_hitter_past_direct_value import past_rate
from run_hitter_absolute_rate import OUT, PREVIOUS, save
from supplement_hitter_overseas_scores import rate_score


def main():
    assert not (OUT / 'review-receipt.json').exists()
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    verify(read(OUT / 'source-review.json')['hashes'])
    fit = read(OUT / 'fit-report.json'); assert fit['predictions_sha256'] == sha256_file(OUT / 'predictions.parquet')
    q = pl.read_parquet(OUT / 'predictions.parquet').sort('row_id')
    previous = pl.read_parquet(PREVIOUS / 'predictions.parquet').sort('row_id')
    assert q.select(previous.columns).equals(previous) and q['absolute_pa'].equals(q['components_pa'])
    actual, env = annual_labels(pl.read_parquet(GEN / 'practical-hitter-v31/dated-stints.parquet'))
    raw = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in q.iter_rows(named=True)])
    lab = labels(raw, np.array([env[y] for y in q['origin_year']]), np.array([env[y] for y in q['target_year']]), q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(raw.sum(1), q['next_pa'].to_numpy())
    assert np.allclose(lab['relative_rate'], q['actual_relative_rate'], atol=1e-10)
    assert np.allclose(lab['relative_value'], q['actual_relative_value'], atol=1e-10)
    q = q.with_columns(pl.Series('actual_common_rate', lab['common_rate']))
    frames = {k: pl.read_parquet(COUNT / f'features-{k}.parquet') for k in range(5)}
    models, physical, replays = {}, [], 0
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y, k = c['origin'], c['fold']; verify(c['hashes'])
            g = q.filter((pl.col('origin_year') == y) & (pl.col('outer_fold') == k)).sort('row_id')
            f = frames[k].filter(pl.col('row_id').is_in(g['row_id'].to_list())).sort('row_id')
            assert f['row_id'].equals(g['row_id']); ps = {}
            for h in c['heads']:
                m = joblib.load(h['path']); assert m.alpha == 100 and h['training_offset'] == h['inference_offset'] == 0
                models[y, k, h['arm']] = (m, h['features']); ps[h['arm']] = m.predict(matrix(f, h['features'])); replays += 1
            rr = np.where(f['prior_debut'].to_numpy() == 0, ps['prospect'], np.where(f['sc_tracked'].to_numpy(), ps['tracking'], ps['base']))
            assert np.allclose(rr, g['absolute_rate'], atol=1e-10)
            assert np.allclose(g['absolute_value'], g['absolute_pa'] * (g['absolute_rate'] / 600 + g['origin_replacement_rate']), atol=1e-10)
            index = f.select(REF).to_numpy() @ VALUES
            physical += g.filter(pl.Series((rr < (VALUES.min() - index) * UNIT) | (rr > (VALUES.max() - index) * UNIT)))['row_id'].to_list()
    assert replays == 105
    profiles = pl.read_parquet(GEN / 'hitter-count-error-diagnosis/diagnostic-rows.parquet').select('row_id', 'recent_observed_MLB_mass', 'overseas_source')
    profiles = profiles.with_columns((pl.when(pl.col('recent_observed_MLB_mass') == 0).then(pl.lit('none'))
               .when(pl.col('recent_observed_MLB_mass') < 600).then(pl.lit('positive_under600')).otherwise(pl.lit('600plus'))
               + pl.when(pl.col('overseas_source') == 'none').then(pl.lit('__domestic')).otherwise(pl.lit('__foreign'))).alias('joint_profile'))
    public = pl.read_parquet(GEN / 'hitter-minor-statcast-precision/scored-predictions.parquet').select('row_id', 'steamer_rate', 'steamer_index', 'common_zips_rate', 'zips_index')
    q = q.join(profiles, on='row_id', validate='1:1').join(public, on='row_id', how='left', validate='1:1')
    original, added = q.filter(~pl.col('source_addition')), q.filter(pl.col('source_addition'))
    pub = original.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    assert original.height == 30506 and added.height == 13 and pub.height == 2627
    scopes = [('all', original), ('public', pub), ('current_MLB', original.filter(pl.col('pa_0') > 0)),
              ('upper_never_debut', original.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Upper minors'))),
              ('lower_never_debut', original.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Lower minors'))),
              ('no_arrival', original.filter(pl.col('next_pa') == 0)), ('recent_MLB_600plus', original.filter(pl.col('recent_observed_MLB_mass') >= 600)),
              ('foreign', original.filter(pl.col('overseas_source') != 'none')), ('additions', added)]
    scopes += [(f'origin_{y}', original.filter(pl.col('origin_year') == y)) for y in sorted(original['origin_year'].unique())]
    scopes += [(f'joint_{p}', original.filter(pl.col('joint_profile') == p)) for p in sorted(original['joint_profile'].unique())]
    scores, triggers = [], []
    for name, g in scopes:
        arms = ['scalar', 'count', 'restored', 'components', 'absolute'] if name == 'additions' else ['current', 'scalar', 'count', 'restored', 'components', 'absolute']
        score = dict(scope=name, rows=g.height, people=g['player_id'].n_unique(), active_rows=int((g['next_pa'] > 0).sum()), actual_PA=int(g['next_pa'].sum()),
                     actual_value=float(g['actual_relative_value'].sum()), scores={arm: summary(g, arm) for arm in arms})
        scores.append(score)
        for anchor in ['components'] + ([] if name == 'additions' else ['current']):
            for metric in ['rate_rmse', 'value_rmse']:
                a, b = score['scores']['absolute'][metric], score['scores'][anchor][metric]
                if a is not None and b is not None and a > 1.05 * b:
                    triggers.append(dict(scope=name, anchor=anchor, metric=metric, relative_worsening=a / b - 1))
    intervals = {}
    for anchor in ['current', 'scalar', 'count', 'restored', 'components']:
        temp = original.with_columns(pl.col(anchor + '_value').alias('contrast_anchor_value'), pl.col('absolute_value').alias('scalar_value'))
        intervals[anchor] = dict(rate=rate_interval(original, 'absolute', anchor), value=value_interval(temp, 'contrast_anchor'))
    save('scores.json', dict(scopes=scores, intervals=intervals, physical_envelope_violations=physical, review_triggers=triggers,
                            public_common_rate=dict(rows=pub.height, active_rows=int((pub['next_pa'] > 0).sum()),
                            scores={a: rate_score(pub.filter(pl.col('next_pa') > 0), col, 'actual_common_rate', True) for a, col in
                                    [('current', 'current_rate'), ('components', 'components_rate'), ('absolute', 'absolute_rate'), ('steamer', 'steamer_rate'), ('zips', 'common_zips_rate')]}),
                            public_qualification='Unchanged origin-centered public reference; vintage/park/environment differences remain and ZiPS workload is not certified.', player_walkthrough_status='pending'))
    checks = 0
    for arm in ['current', 'scalar', 'count', 'restored', 'components', 'absolute']:
        mse, rates = [], []
        for y in sorted(original['origin_year'].unique()):
            g = original.filter(pl.col('origin_year') == y); e = (g[arm + '_value'] - g['actual_relative_value']).to_numpy(); mse.append(np.mean(e * e))
            g = g.filter(pl.col('next_pa') > 0); e = (g[arm + '_rate'] - g['actual_relative_rate']).to_numpy(); n = g['next_pa'].to_numpy(); rates.append(np.sum(n * e * e) / n.sum())
        assert np.isclose(np.sqrt(np.mean(mse)), scores[0]['scores'][arm]['value_rmse'], atol=1e-12)
        assert np.isclose(np.sqrt(np.mean(rates)), scores[0]['scores'][arm]['rate_rmse'], atol=1e-12); checks += 2
    chosen = {rid: ['fixed before fitting'] for rid in pre['fixed_case_row_ids']}
    ranked = original.with_columns(((pl.col('absolute_value') - pl.col('actual_relative_value'))**2 - (pl.col('current_value') - pl.col('actual_relative_value'))**2).alias('change'),
                                   (pl.col('absolute_value') - pl.col('actual_relative_value')).alias('error'))
    for rows, why in [(ranked.sort('change'), 'largest gain'), (ranked.sort('change', descending=True), 'largest harm'), (ranked.sort('error'), 'false low'),
                      (ranked.sort('error', descending=True), 'false high'), (ranked.filter(pl.col('next_pa').is_between(200, 399)).sort(pl.col('error').abs()), 'ordinary')]:
        chosen.setdefault(int(rows['row_id'][0]), []).append(why)
    _, history, sources, foreign = source_data()
    support = pl.read_parquet(PREVIOUS / 'profile-support.parquet'); ranges = read(PREVIOUS / 'feature-ranges.json')
    ann = pl.read_parquet(GEN / 'practical-hitter-v31/counts.parquet').filter(pl.col('bucket') == 'MLB')
    mlbcounts = {(r['season'], r['player_id']): r for r in ann.iter_rows(named=True)}
    covered = set(read(GEN / 'hitter-mlb-events-source-audit/audit.json')['covered_source_seasons'])
    oldwalks = {r['row_id']: r for r in read(PREVIOUS / 'player-walks.json')['cases']}; cases = []
    with threadpool_limits(limits=2):
        for rid, why in chosen.items():
            o = q.filter(pl.col('row_id') == rid).row(0, named=True); y, k, pid = o['origin_year'], o['outer_fold'], o['player_id']
            f = frames[k]; one = f.filter(pl.col('row_id') == rid); a = one.row(0, named=True); key = f'{y}:{pid}'
            graph = read(SHARED / f'graphs-{k}.json')[f'{y}:{k}']
            v, source = past_profile(history[pid], graph, sources.get(key), foreign.get((key, k)), origin=y, outer_fold=k, own_fold=k)
            ev, evsource = reconstruct(pid, y, mlbcounts, covered); quality, mlbsource = quality_source(pid, y, actual, env)
            assert all(np.isclose(a[n], value, atol=1e-10) for n, value in {**v, **ev, **quality}.items())
            arm = o['count_branch']; m, names = models[y, k, arm]; x = matrix(one, names)[0]; effects = x * m.coef_
            prediction = float(m.intercept_ + effects.sum()); assert np.isclose(prediction, o['absolute_rate'], atol=1e-10)
            b = float(past_rate(one)[0]); old = joblib.load(PREVIOUS / f'{arm}-rate-{y}-{k}.joblib')
            learned_change = float(m.intercept_ - old.intercept_ + x @ (m.coef_ - old.coef_))
            assert np.isclose(learned_change - b, o['absolute_rate'] - o['components_rate'], atol=1e-10)
            probes = {}
            for family in ['minor', 'foreign']:
                vv, _ = assemble(source['contributions'], source['reference'], source['observed_precision_PA'], remove=family)
                changed = one.with_columns(*[pl.lit(value).alias(n) for n, value in vv.items()]); rr = float(m.predict(matrix(changed, names))[0])
                probes[family] = dict(rate=rr, change=rr - o['absolute_rate'], artificial_not_causal=True, no_prediction_offset=True)
            if rid in oldwalks:
                peers = oldwalks[rid]['origin_production_selected_comparisons']
            else:
                cell = next(c for c in pre['cells'] if c['year'] == y and c['fold'] == k)
                pool = f.filter(pl.col('row_id').is_in(cell['training_row_ids']) & (pl.col('prior_debut') == a['prior_debut']) & (pl.col('stage') == a['stage']))
                if a['count_NPB_share'] + a['count_KBO_share'] > 0:
                    pool = pool.filter(((pl.col('count_NPB_share') > 0) == (a['count_NPB_share'] > 0)) & ((pl.col('count_KBO_share') > 0) == (a['count_KBO_share'] > 0)))
                distance = pl.sum_horizontal([(pl.col(n) - a[n])**2 for n in FEATURES[:8]]).sqrt() + (pl.col('age') - a['age']).abs() / 5 + (pl.col('pa_0') - a['pa_0']).abs() / 600 + (pl.col('draft_rank') - a['draft_rank']).abs() + (pl.col('scout_rank_score_0') - a['scout_rank_score_0']).abs()
                pool = pool.with_columns(distance.alias('origin_production_distance')).sort('origin_production_distance', 'player_id', 'origin_year').unique('player_id', maintain_order=True).head(3)
                peers = pool.select('row_id', 'player_id', 'player_name', 'origin_year', 'age', 'pa_0', 'minor_pa_0', 'next_pa', 'actual_relative_rate', 'origin_production_distance', *FEATURES).to_dicts()
            geometry, contrasts = {}, {}
            for aa in ['current', 'components', 'absolute']:
                if o[aa + '_rate'] is None:
                    continue
                d = decompose([o[aa + '_pa']], [o['next_pa']], [o[aa + '_rate']], [o['actual_relative_rate'] if o['next_pa'] else np.nan], [o['origin_replacement_rate']])
                geometry[aa] = dict(error=float(d['error'][0]), hitting=float(d['hitting'][0]) if o['next_pa'] else None, opportunity=float(d['opportunity'][0]) if o['next_pa'] else None)
            for aa in ['current', 'components']:
                if o[aa + '_rate'] is not None:
                    d = change([o['absolute_pa']], [o['next_pa']], [o[aa + '_rate']], [o['absolute_rate']], [o['actual_relative_rate'] if o['next_pa'] else np.nan], [o['origin_replacement_rate']])
                    contrasts[aa] = {n: float(d[n][0]) for n in ['delta', 'active_hitting_squared', 'active_interaction', 'nonarrival']}
            cases.append(dict(row_id=rid, why=why, forecast=o, information_date=a['ctx_information_date'], age=a['age'], source=source,
                              raw_history=[r for r in history[pid] if y - 2 <= r['season'] <= y], MLB_source=mlbsource, MLB_event_source=evsource,
                              previous_baseline=b, new_offset=0, fitted_intercept=float(m.intercept_), fitted_prediction=prediction,
                              removed_baseline_effect=-b, relearned_coefficient_change=learned_change,
                              feature_terms=[dict(feature=n, input=float(xx), coefficient=float(cc), effect=float(ee)) for n, xx, cc, ee in zip(names, x, m.coef_, effects, strict=True)],
                              actual_counts=actual.get((o['target_year'], pid), np.zeros(8)).tolist(), probes=probes,
                              joint_support=support.filter(pl.col('row_id') == rid).to_dicts(), inherited_added_feature_extrapolations=[r for r in ranges if r['origin'] == y and r['fold'] == k and r['arm'] == arm and rid in r['row_ids']],
                              origin_production_selected_comparisons=[dict(p, actual_relative_rate=p['actual_relative_rate'] if p['next_pa'] else None) for p in peers], geometry=geometry, contrasts=contrasts))
    save('player-walks.json', dict(cases=cases, fixed_cases_retained=17, walkthrough_status='pending_readable_review'))
    paths = [Path(__file__), OUT / 'preflight.json', OUT / 'source-review.json', OUT / 'fit-report.json', OUT / 'predictions.parquet', OUT / 'scores.json', OUT / 'player-walks.json',
             PREVIOUS / 'player-walks.json', GEN / 'hitter-minor-statcast-precision/scored-predictions.parquet']
    save('review-receipt.json', dict(heads_replayed=replays, independent_headline_equations=checks, original_columns_preserved=True, PA_exactly_fixed=True,
                                    labels_independently_reconstructed=True, cases=len(cases), player_walkthrough_status='pending_readable_review', protected_outcomes_used=False,
                                    deployment_approved=False, hashes={str(p): sha256_file(p) for p in paths}))
    print(scores[0]['scores']); print(f'{len(cases)} actual source/model walks saved; readable review pending.', flush=True)


if __name__ == '__main__':
    main()
