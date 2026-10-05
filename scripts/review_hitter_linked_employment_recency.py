"""Replays, matched scores and source-to-path player walks for one interaction."""
from datetime import date

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_compatible_value import labels
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.linked_employment_recency import OLD, NEW, profiles, support
from universal_baseball.storage import sha256_file
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_hitter_overseas_integration import ANCHOR, annual_labels
from review_hitter_overseas_integration import score, origin_weights
from review_hitter_evidence_representation import interval
from run_hitter_linked_employment_recency import ROOT, BASE, OUT, read, save, verify


def main():
    assert not (OUT / 'review-receipt.json').exists()
    pre, fit = read(OUT / 'preflight.json'), read(OUT / 'fit-report.json')
    verify(pre['hashes'])
    assert sha256_file(OUT / 'predictions.parquet') == fit['predictions_sha256']
    q = pl.read_parquet(OUT / 'predictions.parquet').sort('row_id')
    baseq = pl.read_parquet(BASE / 'predictions.parquet').sort('row_id')
    assert q.select(baseq.columns).equals(baseq) and q['recency_rate'].equals(q['observation_rate'])
    assert q.filter(~pl.col('source_addition'))['recency_rate'].equals(q.filter(~pl.col('source_addition'))['current_rate'])
    frames = {k: pl.read_parquet(OUT / f'features-{k}.parquet') for k in range(5)}
    models, replayed = {}, 0
    oldfit = read(BASE / 'fit-report.json')
    with threadpool_limits(limits=2):
        for arm, cells, names in [('recency', fit['cells'], pre['features']),
                                  ('observation', oldfit['cells'], pre['baseline_features'])]:
            for c in cells:
                y, k = c['origin'], c['fold']
                if arm == 'recency':
                    verify(c['hashes'])
                g = q.filter((pl.col('origin_year') == y) & (pl.col('outer_fold') == k)).sort('row_id')
                te = frames[k].filter(pl.col('row_id').is_in(g['row_id'].to_list())).sort('row_id')
                assert te['row_id'].equals(g['row_id'])
                for h in c['heads']:
                    path = __import__('pathlib').Path(h['path'])
                    if not path.is_absolute():
                        path = ROOT / path
                    model = joblib.load(path)
                    if arm == 'observation':
                        assert sha256_file(path) == h['sha256']
                    assert h['features'] == names
                    x = te.select(names).to_numpy()
                    values = model.predict_proba(x)[:, 1] if h['head'] == 'participation' else model.predict(x)
                    suffix = '_raw_p' if h['head'] == 'participation' else '_raw_conditional_pa'
                    assert np.allclose(values, g[arm + suffix], atol=1e-10, rtol=0)
                    models[arm, y, k, h['head']] = model
                    replayed += 1
    assert replayed == 140
    stints_path = ROOT / 'reports/generated/practical-hitter-v31/dated-stints.parquet'
    stints = pl.read_parquet(stints_path)
    actual, env = annual_labels(stints)
    counts = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in q.iter_rows(named=True)])
    actual_labels = labels(counts, np.array([env[y] for y in q['origin_year']]),
        np.array([env[y] for y in q['target_year']]), q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(actual_labels['pa'], q['next_pa'])
    assert np.allclose(actual_labels['relative_value'], q['actual_relative_value'], atol=1e-10)
    assert np.allclose(actual_labels['relative_rate'], q['actual_relative_rate'], atol=1e-10)
    assert np.allclose(q['recency_pa'], q['recency_p'] * q['recency_conditional_pa'], atol=1e-10)
    assert np.allclose(q['recency_value'], q['recency_pa'] * (q['recency_rate'] / 600 + q['origin_replacement_rate']), atol=1e-10)
    context = profiles(frames[0]).select('row_id', 'prior_regular_evidence', 'status_major_link', 'current_MLB_present',
        OLD, NEW, 'work_0', 'work_1', 'work_2', 'quality_0', 'quality_1', 'quality_2', 'minor_pa_0')
    q = q.join(context, on='row_id', validate='1:1')
    original = q.filter(~pl.col('source_addition'))
    public = original.join(pl.read_parquet(ANCHOR, columns=['row_id', 'steamer_pa', 'steamer_index', 'zips_index']),
        on='row_id', how='left', validate='1:1').filter((pl.col('pa_0') > 0) &
        pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    assert original.height == 30506 and public.height == 2627
    absent = original.filter(~pl.col('current_MLB_present') & pl.col('prior_regular_evidence'))
    assert absent.height == 54
    scopes = dict(original_all=original, public=public, additions=q.filter(pl.col('source_addition')),
        current_regular=original.filter(pl.col('pa_0') >= 400), absent_former_regular=absent,
        absent_linked=absent.filter(pl.col('status_major_link') > 0), absent_unlinked=absent.filter(pl.col('status_major_link') == 0),
        input_changed=original.filter(pl.col(OLD) != pl.col(NEW)), nonparticipants=original.filter(pl.col('next_pa') == 0))
    scopes.update({f'origin_{y}': original.filter(pl.col('origin_year') == y) for y in sorted(original['origin_year'].unique())})
    scopes.update({f'stage_{s}': original.filter(pl.col('stage') == s) for s in sorted(original['stage'].unique())})
    scopes.update({f'never_{s}': original.filter((pl.col('stage') == s) & (pl.col('prior_debut') == 0))
                   for s in ['Upper minors', 'Lower minors']})
    scores = []
    for name, g in scopes.items():
        arms = ['recency', 'observation'] + ([] if name == 'additions' else ['current'])
        scores.append(dict(scope=name, rows=g.height, people=g['player_id'].n_unique(),
            actual_PA=int(g['next_pa'].sum()), actual_participants=int((g['next_pa'] > 0).sum()),
            actual_value=float(g['actual_relative_value'].sum()), scores={a: score(g, a) for a in arms},
            allocations={a: dict(PA_to_participants=float(g.filter(pl.col('next_pa') > 0)[a + '_pa'].sum()),
                PA_to_nonparticipants=float(g.filter(pl.col('next_pa') == 0)[a + '_pa'].sum())) for a in arms}))
    intervals = {}
    with threadpool_limits(limits=2):
        for scope, anchor in [('original_all', 'observation'), ('original_all', 'current'), ('public', 'observation'),
                              ('absent_former_regular', 'observation')]:
            intervals[scope + ':' + anchor] = interval(scopes[scope], 'recency', anchor)
    w = origin_weights(public)
    public_error = public['steamer_pa'].to_numpy() - public['next_pa'].to_numpy()
    save('scores.json', dict(scopes=scores, intervals=intervals,
        public_steamer=dict(PA_RMSE=float(np.sqrt(w @ public_error ** 2)), PA_MAE=float(w @ abs(public_error))),
        conditional_hitting_unchanged=True, player_walkthrough_status='pending'))
    chosen = {rid: ['fixed before fitting'] for rid in pre['fixed_cases']}
    ranked = original.with_columns(((pl.col('recency_value') - pl.col('actual_relative_value')) ** 2 -
        (pl.col('observation_value') - pl.col('actual_relative_value')) ** 2).alias('delta'),
        (pl.col('recency_value') - pl.col('actual_relative_value')).alias('error'))
    for g, why in [(ranked.sort('delta', 'row_id'), 'largest contribution gain'),
        (ranked.sort('delta', 'row_id', descending=[True, False]), 'largest contribution harm'),
        (ranked.sort('error', 'row_id'), 'largest false low'),
        (ranked.sort('error', 'row_id', descending=[True, False]), 'largest false high'),
        (ranked.filter(pl.col('next_pa').is_between(200, 399)).sort(pl.col('error').abs(), 'row_id'), 'ordinary positive PA')]:
        chosen.setdefault(int(g['row_id'][0]), []).append(why)
    timing_path = ROOT / 'reports/generated/hitter-employment-comparison-v2/employment-timing.parquet'
    dates = {(r['origin_year'], r['player_id']): r for r in pl.read_parquet(timing_path).iter_rows(named=True)}
    ledger_path = ROOT / 'reports/generated/hitter-status-evidence-v2/status-ledger.json'
    ledger = {r['candidate_key']: r for r in read(ledger_path)['rows']}
    delta_path = ROOT / 'reports/generated/hitter-employment-v3/employment-deltas.json'
    corrected = {r['candidate_key']: r for r in read(delta_path)['rows']}
    previous = {r['origin']['row_id']: r for r in read(BASE / 'player-walks.json')['cases']}
    walks = []
    for rid, why in chosen.items():
        o = q.filter(pl.col('row_id') == rid).row(0, named=True)
        y, k, pid = o['origin_year'], o['outer_fold'], o['player_id']
        f = frames[k].filter(pl.col('row_id') == rid)
        row = f.row(0, named=True)
        d = dates[y, pid]
        assert np.isclose(d['new_' + OLD], row[OLD], atol=1e-12)
        if d['new_latest_date'] is not None:
            assert date.fromisoformat(d['new_latest_date']) <= date.fromisoformat(o['ctx_information_date'])
        key = f'{y}:{pid}'
        employment = corrected[key]['employment'] if key in corrected else ledger[key]['employment']
        assert employment['latest_date'] == d['new_latest_date']
        mechanics, supports = {}, {}
        cell = next(c for c in pre['cells'] if c['year'] == y and c['fold'] == k)
        tr = frames[k].filter(pl.col('row_id').is_in(cell['training_row_ids']))
        for head in ['participation', 'conditional_pa']:
            sub = tr if head == 'participation' else tr.filter(pl.col('next_pa') > 0)
            supports[head] = support(sub, f).row(0, named=True)
            for arm, names in [('observation', pre['baseline_features']), ('recency', pre['features'])]:
                x = f.select(names).to_numpy()[0]
                m = models[arm, y, k, head]
                mechanics[arm + '_' + head] = logit_trace(m, x, names) if head == 'participation' else trace(m, x, names)
        # Peers require established-career evidence, not just the same zero current PA.
        peers = original.filter((pl.col('origin_year') == y) & (pl.col('player_id') != pid) &
            (pl.col('prior_regular_evidence') == o['prior_regular_evidence']) &
            (pl.col('current_MLB_present') == o['current_MLB_present']) &
            (pl.col('status_major_link') == o['status_major_link']))
        distance = ((pl.col('age') - o['age']) / 5) ** 2
        for lag in range(3):
            distance += ((pl.col(f'work_{lag}') - o[f'work_{lag}']) / 600) ** 2
            distance += ((pl.col(f'quality_{lag}') - o[f'quality_{lag}']) / 3) ** 2
        peers = peers.with_columns(distance.alias('origin_distance')).sort('origin_distance', 'player_id').head(3)
        peer_walks = []
        for p in peers.iter_rows(named=True):
            stats = stints.filter((pl.col('player_id') == p['player_id']) & pl.col('season').is_between(y - 2, y))
            peer_walks.append(dict(forecast=p, raw_three_year_stints=stats.select('season', 'bucket', 'plate_appearances',
                'home_runs', 'strike_outs', 'unintentional_walks').to_dicts()))
        raw = stints.filter((pl.col('player_id') == pid) & pl.col('season').is_between(y - 2, y))
        walks.append(dict(row_id=rid, selection=why, forecast=o, actual_rate=o['actual_relative_rate'] if o['next_pa'] else None,
            raw_three_year_stints=raw.select('season', 'bucket', 'plate_appearances', 'home_runs', 'strike_outs', 'unintentional_walks').to_dicts(),
            raw_employment=employment, timing=d, raw_age=row[OLD], transformed_age=row[NEW], reported_major_link=row['status_major_link'],
            model_inputs={n: row[n] for n in set(pre['baseline_features'] + pre['features'])}, head_paths=mechanics,
            training_support=supports, previous_walk=previous.get(rid), actual_counts=actual.get((y + 1, pid), np.zeros(8)).tolist(),
            peers=peer_walks, peer_exact_count_before_limit=original.filter((pl.col('origin_year') == y) & (pl.col('player_id') != pid) &
                (pl.col('prior_regular_evidence') == o['prior_regular_evidence']) & (pl.col('current_MLB_present') == o['current_MLB_present']) &
                (pl.col('status_major_link') == o['status_major_link'])).height))
    save('player-walks.json', dict(cases=walks, player_walkthrough_status='pending',
        peer_rule='same origin/current MLB presence/reported link/prior regular, then age and three-year MLB work/quality; no outcomes'))
    paths = [__import__('pathlib').Path(__file__), OUT / 'preflight.json', OUT / 'fit-report.json', OUT / 'predictions.parquet',
             OUT / 'scores.json', OUT / 'player-walks.json', timing_path, ledger_path, delta_path, stints_path, ANCHOR,
             ROOT / 'src/universal_baseball/histogram_prediction_trace.py']
    save('review-receipt.json', dict(heads_replayed=replayed, cases=len(walks), original_columns_preserved=True,
        original_population=30506, additions=13, hitting_exactly_fixed=True, actual_labels_reconstructed=True,
        player_walkthrough_status='pending', deployment_approved=False,
        hashes={str(p): sha256_file(p) for p in paths}))
    print('Scores and source/path walks ready for judgment; no automatic promotion.', flush=True)


if __name__ == '__main__':
    main()
