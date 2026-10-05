"""Fixed scores and actual model/source walks; no automatic validation claim."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from run_hitter_nonmedical_opportunity import ROOT, GEN, BASE, SOURCE, OUT, read, save, verify
from universal_baseball.nonmedical_opportunity import FIELDS, OBS
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.storage import sha256_file
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_hitter_overseas_integration import ANCHOR, annual_labels
from review_hitter_overseas_integration import score, origin_weights
from review_hitter_evidence_representation import interval

FIXED = [(665487, 2022), (665487, 2023), (665487, 2024), (518735, 2016),
    (408314, 2017), (677551, 2023), (680776, 2024), (672779, 2024), (434563, 2017),
    (592450, 2016), (670541, 2018), (701762, 2024), (680757, 2021),
    (673548, 2021), (807799, 2022), (808982, 2024)]


def groups(q, context):
    original = q.filter(~pl.col('source_addition'))
    public = original.join(pl.read_parquet(ANCHOR, columns=['row_id', 'steamer_pa', 'steamer_rate',
        'steamer_index', 'zips_index']), on='row_id', how='left', validate='1:1').filter(
        (pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())
    foreign = context.filter(pl.col('evidence_foreign_source_present') > 0)['row_id'].to_list()
    returned = context.filter(pl.col('observation_has_return'))['row_id'].to_list()
    unresolved = context.filter((pl.col(OBS[FIELDS[0]]) > 0) | (pl.col(OBS[FIELDS[1]]) > 0))['row_id'].to_list()
    g = dict(original_all=original, additions=q.filter(pl.col('source_addition')), public=public,
        foreign=q.filter(pl.col('row_id').is_in(foreign)),
        affected_original=original.filter(pl.col('observation_input_changed')),
        unaffected_original=original.filter(~pl.col('observation_input_changed')),
        observed_returns=original.filter(pl.col('row_id').is_in(returned)),
        unresolved_restrictions=original.filter(pl.col('row_id').is_in(unresolved)),
        current_regular=original.filter(pl.col('pa_0') >= 400),
        current_partial=original.filter(pl.col('pa_0').is_between(1, 399)),
        absent_prior_debut=original.filter((pl.col('pa_0') == 0) & (pl.col('prior_debut') > 0)))
    g.update({'origin_' + str(y): original.filter(pl.col('origin_year') == y) for y in sorted(original['origin_year'].unique())})
    g.update({'stage_' + s: original.filter(pl.col('stage') == s) for s in sorted(original['stage'].unique())})
    g.update({'never_' + s: original.filter((pl.col('stage') == s) & (pl.col('prior_debut') == 0))
              for s in ['Upper minors', 'Lower minors']})
    assert len(original) == 30506 and len(public) == 2627
    return g


def main():
    if (OUT / 'review-receipt.json').exists() or (OUT / 'review-source-seal.json').exists():
        raise ValueError('Preserve review execution; no automatic restart')
    pre, fit = read(OUT / 'preflight.json'), read(OUT / 'fit-report.json')
    verify(pre['hashes'])
    assert sha256_file(OUT / 'predictions.parquet') == fit['predictions_sha256']
    paths = [ROOT / 'scripts/review_hitter_nonmedical_opportunity.py',
        ROOT / 'scripts/review_hitter_overseas_integration.py', ROOT / 'scripts/review_hitter_evidence_representation.py',
        ROOT / 'scripts/prepare_hitter_overseas_integration.py', ROOT / 'scripts/evaluate_hitter_readiness_v49.py',
        ROOT / 'src/universal_baseball/histogram_prediction_trace.py',
        ROOT / 'src/universal_baseball/hitter_compatible_value.py',
        GEN / 'practical-hitter-v31/dated-stints.parquet', GEN / 'foreign-origin-inputs/origin-inputs.json',
        SOURCE / 'active-origin-evidence.json', SOURCE / 'player-walks.json',
        BASE / 'fit-report.json', ANCHOR, OUT / 'preflight.json', OUT / 'fit-report.json', OUT / 'predictions.parquet']
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in paths}
    save('review-source-seal.json', dict(before_review=True, hashes=before))
    q = pl.read_parquet(OUT / 'predictions.parquet').sort('row_id')
    frames = {k: pl.read_parquet(OUT / f'features-{k}.parquet') for k in range(5)}
    context = frames[0]
    stints = pl.read_parquet(GEN / 'practical-hitter-v31/dated-stints.parquet')
    assert stints['season'].max() <= 2025
    actual, env = annual_labels(stints)
    raw = np.array([actual.get((r['target_year'], r['player_id']), np.zeros(8)) for r in q.to_dicts()])
    lab = labels(raw, np.array([env[y] for y in q['origin_year']]), np.array([env[y] for y in q['target_year']]),
                 q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'], q['next_pa'])
    for name in ['relative_rate', 'relative_value']:
        assert np.allclose(lab[name], q['actual_' + name], atol=1e-10, rtol=0)
    assert q['observation_rate'].equals(q['corrected_job_rate'])
    assert np.allclose(q['observation_pa'], q['observation_p'] * q['observation_conditional_pa'], atol=1e-10)
    assert np.allclose(q['observation_value'], q['observation_pa'] *
        (q['observation_rate'] / 600 + q['origin_replacement_rate']), atol=1e-10)
    models, replayed = {}, 0
    with threadpool_limits(limits=2):
        for arm, report, names in [('observation', fit, pre['job_features']),
                                  ('corrected_job', read(BASE / 'fit-report.json'), pre['baseline_features'])]:
            for cell in report['cells']:
                y, k = cell['origin'], cell['fold']
                te = frames[k].filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
                g = q.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
                for h in cell['heads']:
                    path = ROOT / h['path']
                    assert sha256_file(path) == h['sha256'] and h['features'] == names
                    m = joblib.load(path)
                    x = te.select(names).to_numpy()
                    v = m.predict_proba(x)[:, 1] if h['head'] == 'participation' else m.predict(x)
                    col = arm + ('_raw_p' if h['head'] == 'participation' else '_raw_conditional_pa')
                    assert np.allclose(v, g[col], atol=1e-10, rtol=0)
                    models[arm, y, k, h['head']] = m
                    replayed += 1
    assert replayed == 140
    scopes = groups(q, context)
    scores = []
    for name, g in scopes.items():
        if not len(g):
            continue
        arms = ['corrected_job', 'observation', 'old_job'] + ([] if g['source_addition'].any() else ['current'])
        scores.append(dict(scope=name, rows=g.height, people=g['player_id'].n_unique(),
            actual_PA=int(g['next_pa'].sum()), actual_participants=int((g['next_pa'] > 0).sum()),
            actual_value=float(g['actual_relative_value'].sum()), scores={a: score(g, a) for a in arms},
            allocation={a: dict(PA_to_participants=float(g.filter(pl.col('next_pa') > 0)[a + '_pa'].sum()),
                PA_to_nonparticipants=float(g.filter(pl.col('next_pa') == 0)[a + '_pa'].sum())) for a in arms}))
    public = scopes['public']
    w = origin_weights(public)
    pe = public['steamer_pa'].to_numpy() - public['next_pa'].to_numpy()
    ve = public['steamer_pa'].to_numpy() * (public['steamer_rate'].to_numpy() / 600 +
        public['origin_replacement_rate'].to_numpy()) - public['actual_relative_value'].to_numpy()
    save('scores.json', dict(scopes=scores, public_steamer=dict(rows=2627,
        PA_RMSE=float(np.sqrt(w @ pe ** 2)), PA_MAE=float(w @ abs(pe)),
        batting_contribution_RMSE=float(np.sqrt(w @ ve ** 2)),
        qualification='Existing source-date/park/rate-qualified prior-MLB matched cohort; ordinary ZiPS PA not unconditional'),
        talent_held_fixed=True))
    with threadpool_limits(limits=2):
        comparisons = [dict(scope=name, candidate='observation', baseline=baseline,
            intervals=interval(scopes[name], 'observation', baseline)) for name, baseline in
            [('original_all', 'corrected_job'), ('original_all', 'current'),
             ('affected_original', 'corrected_job'), ('public', 'corrected_job')]]
    save('intervals.json', dict(repetitions=2000, seed=84, comparisons=comparisons))
    selected, diagnostics = {}, []
    for pid, year in FIXED:
        g = q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == year))
        assert g.height == 1, (pid, year)
        selected[int(g['row_id'][0])] = ['fixed source or hitter stress case']
    def choose(g, reason):
        if g.height:
            rid = int(g['row_id'][0])
            selected.setdefault(rid, []).append(reason)
            diagnostics.append(rid)
    original = scopes['original_all']
    for baseline in ['corrected_job', 'current']:
        z = original.with_columns(((pl.col('observation_value') - pl.col('actual_relative_value')) ** 2 -
            (pl.col(baseline + '_value') - pl.col('actual_relative_value')) ** 2).alias('delta'),
            (pl.col('observation_value') - pl.col('actual_relative_value')).alias('error'))
        choose(z.sort('delta', 'row_id'), baseline + ' largest contribution gain')
        choose(z.sort('delta', 'row_id', descending=[True, False]), baseline + ' largest contribution harm')
        choose(z.sort('error', 'row_id'), baseline + ' largest false low')
        choose(z.sort('error', 'row_id', descending=[True, False]), baseline + ' largest false high')
        choose(z.filter(pl.col('next_pa').is_between(200, 399)).with_columns(
            pl.col('error').abs().alias('abs_error')).sort('abs_error', 'row_id'), baseline + ' ordinary positive PA')
    changed = scopes['affected_original'].with_columns(((pl.col('observation_pa') - pl.col('next_pa')) ** 2 -
        (pl.col('corrected_job_pa') - pl.col('next_pa')) ** 2).alias('delta'))
    choose(changed.sort('delta', 'row_id'), 'source-changed largest PA gain')
    choose(changed.sort('delta', 'row_id', descending=[True, False]), 'source-changed largest PA harm')
    origin = context.filter(pl.col('row_id').is_in(q['row_id'].to_list()))
    peers = {}
    for rid in sorted(set(diagnostics)):
        r = origin.filter(pl.col('row_id') == rid).row(0, named=True)
        pool = origin.filter((pl.col('origin_year') == r['origin_year']) & (pl.col('row_id') != rid) &
            (pl.col('prior_debut') == r['prior_debut']) & (pl.col('stage') == r['stage']) &
            (pl.col('captured_legal_class') == r['captured_legal_class']))
        p = pool.with_columns((((pl.col('age') - r['age']) / 5) ** 2 +
            ((pl.col('pa_0') - r['pa_0']) / 250) ** 2 +
            (pl.col('professional_work_0') - r['professional_work_0']) ** 2).alias('distance')).sort(
                'distance', 'player_id', 'row_id').head(3)
        peers[rid] = p.select('row_id', 'player_id', 'age', 'stage', 'captured_legal_class',
                             'pa_0', 'professional_work_0', 'distance').to_dicts()
        for v in peers[rid]:
            selected.setdefault(v['row_id'], []).append('origin-only peer of ' + str(rid))
    save('case-selection.json', dict(selected={str(k): v for k, v in selected.items()},
        peers={str(k): v for k, v in peers.items()},
        peer_rule='Same origin, debut/stage/captured legal class; nearest age, MLB PA and professional work; no future outcome used'))
    old_source = {f'{c["origin_year"]}:{c["player_id"]}': c for c in read(SOURCE / 'player-walks.json')['cases']}
    source_details = read(SOURCE / 'active-origin-evidence.json')['origins']
    foreign = {r['candidate_key']: r for r in read(GEN / 'foreign-origin-inputs/origin-inputs.json')['rows']}
    support = pl.read_parquet(OUT / 'profile-support.parquet')
    cases = []
    with threadpool_limits(limits=2):
        for rid, reason in sorted(selected.items()):
            r = q.filter(pl.col('row_id') == rid).row(0, named=True)
            y, k, pid = r['origin_year'], r['outer_fold'], r['player_id']
            key = f'{y}:{pid}'
            row = frames[k].filter(pl.col('row_id') == rid).row(0, named=True)
            x = np.array([row[n] for n in pre['baseline_features']])
            z = np.array([row[n] for n in pre['job_features']])
            mechanics, probe = {}, {}
            for arm, v, names in [('corrected_job', x, pre['baseline_features']), ('observation', z, pre['job_features'])]:
                for head in ['participation', 'conditional_pa']:
                    m = models[arm, y, k, head]
                    t = logit_trace(m, v, names) if head == 'participation' else trace(m, v, names)
                    value = t['linked_probability'] if head == 'participation' else t['raw_prediction']
                    col = arm + ('_raw_p' if head == 'participation' else '_raw_conditional_pa')
                    assert np.isclose(value, r[col], atol=1e-8, rtol=0)
                    mechanics[arm + '_' + head] = t
                    if arm == 'corrected_job':
                        probe[head] = float(m.predict_proba(z[None, :])[0, 1]) if head == 'participation' else float(m.predict(z[None, :])[0])
            probe['expected_PA'] = 0. if row['status_hard_unavailable'] or row['status_retired'] else (
                probe['participation'] * float(np.clip(probe['conditional_pa'], 1, 800)))
            cases.append(dict(origin=r, selection=reason, source_observation=source_details.get(key),
                prior_source_walk=old_source.get(key),
                domestic_counts=stints.filter((pl.col('player_id') == pid) &
                    pl.col('season').is_between(y - 2, y)).sort('season', 'bucket', 'team_id').to_dicts(),
                foreign_counts=foreign.get(key), actual_future_MLB_counts=actual.get((y + 1, pid), np.zeros(8)).tolist(),
                model_inputs={n: row[n] for n in list(dict.fromkeys(pre['baseline_features'] + pre['job_features']))},
                input_changes={n: [row[n], row[OBS[n]]] for n in FIELDS if row[n] != row[OBS[n]]},
                head_mechanics=mechanics, baseline_parameters_new_input_probe=probe,
                probe_is_not_replacement_or_causal=True,
                actual_training_profiles=support.filter(pl.col('row_id') == rid).to_dicts(),
                origin_only_peers=peers.get(rid, []), unchanged_talent='Saved incumbent for original; fixed repaired-domestic fallback for additions'))
    save('player-walks.json', dict(cases=cases, player_walkthrough_status='machine_ready_manual_pending'))
    verify(before)
    outputs = [OUT / n for n in ['review-source-seal.json', 'scores.json', 'intervals.json',
               'case-selection.json', 'player-walks.json']]
    save('review-receipt.json', dict(heads_replayed=140, labels_independently_reconstructed=True,
        case_count=len(cases), player_walkthrough_status='pending', deployment_approved=False,
        completed_2026_evaluation_unchanged=True,
        hashes=before | {str(p.relative_to(ROOT)): sha256_file(p) for p in outputs}))
    print(__import__('json').dumps(dict(scopes=scores[:3], cases=len(cases))), flush=True)


if __name__ == '__main__':
    main()
