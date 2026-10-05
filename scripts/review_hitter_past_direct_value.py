"""Replay, fixed cohort scoring and actual player mechanics before disposition."""
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_count_baseline import past_profile, assemble
from universal_baseball.hitter_compatible_value import UNIT, labels
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import annual_labels
from review_hitter_evidence_representation import rate_interval
from review_hitter_overseas_integration import origin_weights
from supplement_hitter_overseas_scores import rate_score
from run_hitter_count_baseline import ROOT, GEN, OUT as COUNT, SHARED, FEATURES, REF, read, verify, source_data, matrix
from run_hitter_past_direct_value import OUT, save, past_rate


def summary(g, arm):
    w = origin_weights(g); error = (g[arm + '_value'] - g['actual_relative_value']).to_numpy()
    active = g.filter(pl.col('next_pa') > 0)
    return dict(value_rmse=float(np.sqrt(w @ (error**2))), value_mae=float(w @ abs(error)), value_bias=float(w @ error),
                expected_value=float(g[arm + '_value'].sum()), expected_PA=float(g[arm + '_pa'].sum()),
                rate_rmse=rate_score(active, arm + '_rate', 'actual_relative_rate', True) if active.height else None)


def value_interval(g, anchor):
    w = origin_weights(g); a = g['actual_relative_value'].to_numpy()
    delta = (g['scalar_value'].to_numpy() - a)**2 - (g[anchor + '_value'].to_numpy() - a)**2
    people, ix = np.unique(g['player_id'].to_numpy(), return_inverse=True)
    sums = np.zeros(len(people)); den = sums.copy()
    np.add.at(sums, ix, w * delta); np.add.at(den, ix, w)
    rng = np.random.default_rng(84); draw = []
    for _ in range(2000):
        c = np.bincount(rng.integers(len(people), size=len(people)), minlength=len(people)); draw.append(float(c @ sums / (c @ den)))
    return dict(change=float(w @ delta), lower=float(np.quantile(draw, .025)), upper=float(np.quantile(draw, .975)), nominal_exposed_development_interval=True)


def main():
    assert not (OUT / 'review-receipt.json').exists()
    pre = read(OUT / 'preflight.json'); verify(pre['source_hashes'])
    fit = read(OUT / 'fit-report.json'); assert fit['predictions_sha256'] == sha256_file(OUT / 'predictions.parquet')
    q = pl.read_parquet(OUT / 'predictions.parquet').sort('row_id')
    old = pl.read_parquet(COUNT / 'predictions.parquet').sort('row_id')
    assert q.select(old.columns).equals(old) and q['scalar_pa'].equals(q['count_pa'])
    actual, env = annual_labels(pl.read_parquet(GEN / 'practical-hitter-v31/dated-stints.parquet'))
    counts = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in q.iter_rows(named=True)])
    lab = labels(counts, np.array([env[y] for y in q['origin_year']]), np.array([env[y] for y in q['target_year']]), q['origin_replacement_rate'].to_numpy())
    assert np.allclose(lab['relative_rate'], q['actual_relative_rate'], atol=1e-10) and np.allclose(lab['relative_value'], q['actual_relative_value'], atol=1e-10)
    q = q.with_columns(pl.Series('actual_common_rate', lab['common_rate']))
    frames = {k: pl.read_parquet(COUNT / f'features-{k}.parquet') for k in range(5)}
    models = {}; replayed = 0; envelope_flags = []
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y, k = c['origin'], c['fold']; verify(c['hashes'])
            g = q.filter((pl.col('origin_year') == y) & (pl.col('outer_fold') == k)).sort('row_id')
            f = frames[k].filter(pl.col('row_id').is_in(g['row_id'])).sort('row_id'); forecasts = {}
            assert f['row_id'].equals(g['row_id'])
            b = past_rate(f)
            for h in c['heads']:
                m = joblib.load(h['path']); models[y, k, h['arm']] = (m, h['features'])
                forecasts[h['arm']] = b + m.predict(matrix(f, h['features'])); replayed += 1
            r = np.where(f['prior_debut'].to_numpy() == 0, forecasts['prospect'], np.where(f['sc_tracked'].to_numpy(), forecasts['tracking'], forecasts['base']))
            assert np.allclose(r, g['scalar_rate'], atol=1e-10) and np.allclose(b, g['scalar_baseline_rate'], atol=1e-10)
            assert np.allclose(g['scalar_value'], g['scalar_pa'] * (g['scalar_rate'] / 600 + g['origin_replacement_rate']), atol=1e-10)
            ref_index = f.select(REF).to_numpy() @ VALUES
            bad = (r < (VALUES.min() - ref_index) * UNIT) | (r > (VALUES.max() - ref_index) * UNIT)
            envelope_flags.extend(g.filter(pl.Series(bad))['row_id'].to_list())
    assert replayed == 105
    diagnostic = pl.read_parquet(GEN / 'hitter-count-error-diagnosis/diagnostic-rows.parquet').select('row_id', 'recent_observed_MLB_mass', 'overseas_source')
    public = pl.read_parquet(GEN / 'hitter-minor-statcast-precision/scored-predictions.parquet').select('row_id', 'steamer_rate', 'steamer_index', 'common_zips_rate', 'zips_index')
    q = q.join(diagnostic, on='row_id', validate='1:1').join(public, on='row_id', how='left', validate='1:1')
    original = q.filter(~pl.col('source_addition')); additions = q.filter(pl.col('source_addition'))
    pub = original.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    assert original.height == 30506 and additions.height == 13 and pub.height == 2627
    scopes = [('all', original), ('public', pub), ('current_MLB', original.filter(pl.col('pa_0') > 0)),
              ('upper_never_debut', original.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Upper minors'))),
              ('lower_never_debut', original.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Lower minors'))),
              ('no_arrival', original.filter(pl.col('next_pa') == 0)), ('recent_MLB_600plus', original.filter(pl.col('recent_observed_MLB_mass') >= 600)),
              ('foreign', original.filter(pl.col('overseas_source') != 'none')), ('additions', additions)]
    scopes += [(f'origin_{y}', original.filter(pl.col('origin_year') == y)) for y in sorted(original['origin_year'].unique())]
    scores = []
    for name, g in scopes:
        arms = ['count', 'scalar'] if name == 'additions' else ['current', 'count', 'scalar']
        scores.append(dict(scope=name, rows=g.height, players=g['player_id'].n_unique(), active_rows=int((g['next_pa'] > 0).sum()),
                           actual_PA=int(g['next_pa'].sum()), actual_value=float(g['actual_relative_value'].sum()), scores={a: summary(g, a) for a in arms}))
    pub_active = pub.filter(pl.col('next_pa') > 0)
    save('scores.json', dict(scopes=scores, intervals={a: dict(rate=rate_interval(original, 'scalar', a), value=value_interval(original, a)) for a in ['current', 'count']},
         public_common_rate=dict(rows=pub.height, active_rows=pub_active.height, scores={a: rate_score(pub_active, col, 'actual_common_rate', True) for a, col in [('current', 'current_rate'), ('count', 'count_rate'), ('scalar', 'scalar_rate'), ('steamer', 'steamer_rate'), ('zips', 'common_zips_rate')]},
         qualification='Origin-centered public comparison; release/environment/park differences remain. Not a certified ZiPS playing-time comparison; no scalar event probabilities invented.'),
         physical_envelope_violations=envelope_flags, player_walkthrough_status='pending'))
    # Independent equations verify the headline, without importing summary helpers.
    allscore = scores[0]['scores']
    for arm in ['current', 'count', 'scalar']:
        value_mse = []; rate_mse = []
        for y in sorted(original['origin_year'].unique()):
            g = original.filter(pl.col('origin_year') == y); e = (g[arm + '_value'] - g['actual_relative_value']).to_numpy(); value_mse.append(np.mean(e * e))
            g = g.filter(pl.col('next_pa') > 0); e = (g[arm + '_rate'] - g['actual_relative_rate']).to_numpy(); n = g['next_pa'].to_numpy(); rate_mse.append(np.sum(n * e * e) / n.sum())
        assert np.isclose(np.sqrt(np.mean(value_mse)), allscore[arm]['value_rmse'], atol=1e-12)
        assert np.isclose(np.sqrt(np.mean(rate_mse)), allscore[arm]['rate_rmse'], atol=1e-12)
    chosen = {rid: ['fixed before fitting, retained previous walk'] for rid in pre['fixed_case_row_ids']}
    ranked = original.with_columns(((pl.col('scalar_value') - pl.col('actual_relative_value'))**2 - (pl.col('current_value') - pl.col('actual_relative_value'))**2).alias('change'), (pl.col('scalar_value') - pl.col('actual_relative_value')).alias('error'))
    for rows, why in [(ranked.sort('change'), 'largest gain'), (ranked.sort('change', descending=True), 'largest harm'), (ranked.sort('error'), 'false low'), (ranked.sort('error', descending=True), 'false high'), (ranked.filter(pl.col('next_pa').is_between(200, 399)).sort(pl.col('error').abs()), 'ordinary')]:
        chosen.setdefault(int(rows['row_id'][0]), []).append(why)
    _, history, sources, foreign = source_data(); cases = []
    support = pl.read_parquet(COUNT / 'profile-support.parquet'); ranges = read(COUNT / 'feature-ranges.json')
    with threadpool_limits(limits=2):
        for rid, why in chosen.items():
            o = q.filter(pl.col('row_id') == rid).row(0, named=True); y, k, pid = o['origin_year'], o['outer_fold'], o['player_id']; f = frames[k]
            one = f.filter(pl.col('row_id') == rid); a = one.row(0, named=True)
            graph = read(SHARED / f'graphs-{k}.json')[f'{y}:{k}']; key = f'{y}:{pid}'
            v, note = past_profile(history[pid], graph, sources.get(key), foreign.get((key, k)), origin=y, outer_fold=k, own_fold=k)
            assert all(np.isclose(v[n], a[n], atol=1e-12) for n in v)
            m, names = models[y, k, o['count_branch']]; x = matrix(one, names)[0]; effects = x * m.coef_
            residual = float(m.intercept_ + effects.sum()); b = float(past_rate(one)[0])
            assert np.isclose(b + residual, o['scalar_rate'], atol=1e-10)
            probes = {}
            for family in ['minor', 'foreign']:
                vv, pp = assemble(note['contributions'], note['reference'], note['observed_precision_PA'], remove=family)
                changed = one.with_columns(*[pl.lit(value).alias(n) for n, value in vv.items()]); br = float(past_rate(changed)[0]); rr = float(br + m.predict(matrix(changed, names))[0])
                probes[family] = dict(baseline_rate=br, rate=rr, change=rr - o['scalar_rate'], artificial_not_causal=True)
            cell = next(c for c in pre['cells'] if c['year'] == y and c['fold'] == k)
            peers = f.filter(pl.col('row_id').is_in(cell['training_row_ids']) & (pl.col('prior_debut') == a['prior_debut']) & (pl.col('stage') == a['stage']))
            if a['count_NPB_share'] + a['count_KBO_share'] > 0:
                peers = peers.filter(((pl.col('count_NPB_share') > 0) == (a['count_NPB_share'] > 0)) & ((pl.col('count_KBO_share') > 0) == (a['count_KBO_share'] > 0)))
            distance = pl.sum_horizontal([(pl.col(n) - a[n])**2 for n in FEATURES[:8]]).sqrt() + (pl.col('age') - a['age']).abs() / 5 + (pl.col('pa_0') - a['pa_0']).abs() / 600 + (pl.col('draft_rank') - a['draft_rank']).abs() + (pl.col('scout_rank_score_0') - a['scout_rank_score_0']).abs()
            peers = peers.with_columns(distance.alias('origin_production_distance')).sort('origin_production_distance', 'player_id', 'origin_year').unique('player_id', maintain_order=True).head(3)
            cases.append(dict(row_id=rid, why=why, forecast=o, information_date=a['ctx_information_date'], age=a['age'], source=note,
                raw_history=[r for r in history[pid] if y-2 <= r['season'] <= y], past_baseline_rate=b, fitted_scalar_intercept=float(m.intercept_), fitted_scalar_residual=residual,
                feature_terms=[dict(feature=n, input=float(xx), coefficient=float(cc), effect=float(ee)) for n, xx, cc, ee in zip(names, x, m.coef_, effects, strict=True)],
                actual_counts=actual.get((o['target_year'], pid), np.zeros(8)).tolist(), probes=probes,
                support=support.filter((pl.col('row_id') == rid) & (pl.col('arm') == o['count_branch'])).to_dicts(),
                feature_extrapolations=[r for r in ranges if r['origin'] == y and r['fold'] == k and r['arm'] == o['count_branch'] and rid in r['row_ids']],
                origin_production_selected_comparisons=peers.select('row_id', 'player_id', 'player_name', 'origin_year', 'age', 'pa_0', 'minor_pa_0', 'next_pa', 'actual_relative_rate', 'origin_production_distance', *FEATURES).to_dicts(),
                interpretation='Exact baseline plus linear accounting, not causal attribution; probes artificial; peers selected without future outcomes.'))
    save('player-walks.json', dict(cases=cases, walkthrough_status='pending_readable_review', fixed_cases=13))
    paths = [Path(__file__), OUT / 'preflight.json', OUT / 'fit-report.json', OUT / 'scores.json', OUT / 'player-walks.json', OUT / 'predictions.parquet', GEN / 'hitter-minor-statcast-precision/scored-predictions.parquet']
    save('review-receipt.json', dict(heads_replayed=replayed, independent_headline_equations=6, original_columns_exactly_preserved=True, PA_exactly_fixed=True,
        labels_independently_reconstructed=True, cases=len(cases), player_walkthrough_status='pending_readable_review', protected_outcomes_used=False, deployment_approved=False, hashes={str(p): sha256_file(p) for p in paths}))
    print(str(allscore)); print(f'Replayed 105 heads and saved {len(cases)} source/model walks. Readable review remains required.', flush=True)


if __name__ == '__main__':
    main()
