"""Sealed no-fit comparison with real player replay, not a new point candidate."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.storage import sha256_file
from universal_baseball.hitter_workload_location import scalar_median, location_score, paired_location
from universal_baseball.hitter_workload_risk import mixture_pmf
from universal_baseball.histogram_prediction_trace import trace
from evaluate_hitter_readiness_v49 import logit_trace

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT/'reports/generated/hitter-workload-risk'
CURRENT = ROOT/'reports/generated/hitter-preseason-readiness-v68'
OUT = ROOT/'reports/generated/hitter-workload-location-diagnostic'
EVIDENCE = ROOT/'reports/model-evidence/hitter-workload-location-diagnostic'
FIXED = [(592450, 2024), (701762, 2024), (694671, 2023), (624413, 2018),
         (668804, 2018), (474832, 2023), (677551, 2023), (670867, 2017)]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT/name
    assert not path.exists(), f'Preserve existing receipt: {path}'
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n', encoding='utf8', newline='\n')


def verify(paths):
    for path, h in paths.items():
        assert sha256_file(Path(path)) == h, path


def prepare():
    final = read(OLD/'final-report.json')
    assert final['player_walkthrough_status'] == 'complete' and final['all_current_forecasts_exact']
    verify(final['source_and_execution_hashes']); verify(final['review_hashes'])
    paths = [Path(__file__), ROOT/'docs/hitter-workload-location-diagnostic-contract.md',
             ROOT/'src/universal_baseball/hitter_workload_location.py',
             ROOT/'tests/test_hitter_workload_location.py', OLD/'final-report.json',
             OLD/'fit-report.json', OLD/'scored-predictions.parquet', OLD/'preflight.json',
             OLD/'profile-support.parquet', CURRENT/'scored-predictions.parquet',
             CURRENT/'features.parquet', CURRENT/'preflight.json',
             ROOT/'reports/generated/practical-hitter-v31/counts.parquet']
    write('preflight.json', dict(new_fits=0, saved_review_complete=True,
        source_hashes={str(p): sha256_file(p) for p in paths}, fixed_players=FIXED,
        protected_outcomes_used=False, current_candidate_changed=False))
    print('Existing completed source review verified and diagnostic sealed before scoring.', flush=True)


def public(frame):
    return frame.filter((pl.col('pa_0') > 0) & pl.col('steamer_index').is_not_null() & pl.col('zips_index').is_not_null())


def score():
    verify(read(OUT/'preflight.json')['source_hashes'])
    assert not (OUT/'scores.json').exists()
    q = pl.read_parquet(OLD/'scored-predictions.parquet').sort('row_id')
    anchor = pl.read_parquet(CURRENT/'scored-predictions.parquet').sort('row_id')
    assert q.select(anchor.columns).equals(anchor) and len(q) == 30506 and q['row_id'].n_unique() == len(q)
    assert q['target_year'].max() == 2025 and (q['target_year'] == q['origin_year']+1).all()
    assert np.allclose(q['preseason_pa'], q['preseason_p']*q['preseason_conditional_pa'], atol=1e-10, rtol=0)
    assert len(public(q)) == 2627 and public(q)['steamer_pa'].equals(public(q)['archive_steamer_pa'])
    cells = read(OLD/'fit-report.json')['cells']
    for cell in cells:
        g = q.filter((pl.col('origin_year') == cell['year']) & (pl.col('outer_fold') == cell['fold']))
        for batch in g.iter_slices(500):
            pmf = mixture_pmf(batch['preseason_p'].to_numpy(), batch['preseason_conditional_pa'].to_numpy(),
                              cell['concentration']['concentration'])
            assert np.array_equal((np.cumsum(pmf, axis=1) >= .5).argmax(axis=1), batch['risk_q50'])
    scopes = [('all', q), ('public', public(q)), ('current_MLB', q.filter(pl.col('pa_0') > 0)),
              ('absent_prior_debut', q.filter((pl.col('prior_debut') == 1) & (pl.col('pa_0') == 0))),
              ('upper_never_debut', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Upper minors'))),
              ('lower_never_debut', q.filter((pl.col('prior_debut') == 0) & (pl.col('stage') == 'Lower minors'))),
              ('thin_new_draftee', q.filter((pl.col('draft_known') == 1) & (pl.col('draft_year') == pl.col('origin_year')) &
                  (pl.sum_horizontal('minor_pa_0', 'minor_pa_1', 'minor_pa_2', 'pa_0', 'pa_1', 'pa_2') < 150)))]
    for lo, hi in [(1,199), (200,399), (400,599), (600,10000)]:
        scopes.append((f'current_PA_{lo}_{hi}', q.filter(pl.col('pa_0').is_between(lo, hi))))
    for y in sorted(q['origin_year'].unique()):
        g = q.filter(pl.col('origin_year') == y)
        scopes.extend([(f'origin_{y}', g), (f'public_origin_{y}', public(g))])
    summaries = []
    for name, g in scopes:
        if not len(g):
            continue
        arms = {'mean': 'preseason_pa', 'median': 'risk_q50'}
        if name.startswith('public'):
            arms['steamer'] = 'steamer_pa'
        summaries.append(dict(scope=name, rows=len(g), people=g['player_id'].n_unique(),
            actual_pa=int(g['next_pa'].sum()), actual_appearances=int((g['next_pa'] > 0).sum()),
            expected_appearances=float(g['preseason_p'].sum()), zero_medians=int((g['risk_q50'] == 0).sum()),
            scores={label: location_score(g, col) for label, col in arms.items()}))
    with threadpool_limits(limits=2):
        intervals = [dict(scope=name, **paired_location(g, absolute))
                     for name, g in [('all',q), ('public',public(q))] for absolute in [True, False]]
    write('scores.json', summaries); write('intervals.json', intervals)
    chosen = {}
    def choose(g, why):
        assert len(g), why
        chosen.setdefault(int(g['row_id'][0]), []).append(why)
    for pid, y in FIXED:
        choose(q.filter((pl.col('player_id') == pid) & (pl.col('origin_year') == y)), 'fixed before score')
    errors = q.with_columns((pl.col('risk_q50')-pl.col('next_pa')).alias('median_error'),
        ((pl.col('preseason_pa')-pl.col('next_pa')).abs()-(pl.col('risk_q50')-pl.col('next_pa')).abs()).alias('mae_gain'))
    choose(public(errors).sort('mae_gain','row_id',descending=[True,False]), 'largest public absolute-error gain')
    choose(public(errors).sort('mae_gain','row_id'), 'largest public absolute-error harm')
    choose(errors.sort('median_error','row_id',descending=[True,False]), 'largest median false high')
    choose(errors.sort('median_error','row_id'), 'largest median false low')
    choose(errors.filter(pl.col('next_pa').is_between(200,600)).with_columns(pl.col('median_error').abs().alias('absolute_error'))
        .sort('absolute_error','row_id'), 'ordinary active median')
    f = pl.read_parquet(CURRENT/'features.parquet'); names = read(OLD/'preflight.json')['features']
    counts = pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    support = pl.read_parquet(OLD/'profile-support.parquet'); cases = []; hashes = {}; replays = 0
    with threadpool_limits(limits=2):
        for rid, selection in chosen.items():
            r = q.filter(pl.col('row_id') == rid).row(0,named=True)
            y, k = r['origin_year'], r['outer_fold']; te = f.filter(pl.col('row_id') == rid)
            point_path = CURRENT/f'fit-{y}-{k}.json'; note = read(point_path)
            law = next(c for c in cells if c['year'] == y and c['fold'] == k)
            calibration_path = Path(law['calibration_path'])
            assert sha256_file(calibration_path) == law['calibration_sha256']
            hashes[str(point_path)] = sha256_file(point_path)
            hashes[str(calibration_path)] = law['calibration_sha256']
            paths = {}; x = te.select(names).to_numpy()
            for h in note['heads']:
                verify({h['path']: h['sha256']}); hashes[h['path']] = h['sha256']; m = joblib.load(h['path'])
                if h['head'] == 'participation':
                    assert np.isclose(m.predict_proba(x)[0,1],r['preseason_raw_p'],atol=1e-10,rtol=0)
                    paths[h['head']] = logit_trace(m,x[0],names)
                else:
                    assert np.isclose(m.predict(x)[0],r['preseason_raw_conditional_pa'],atol=1e-10,rtol=0)
                    paths[h['head']] = trace(m,x[0],names)
                replays += 1
            median = scalar_median(r['preseason_p'],r['preseason_conditional_pa'],law['concentration']['concentration'])
            assert median['median'] == r['risk_q50']
            peers = q.filter((pl.col('origin_year') == y) & (pl.col('stage') == r['stage']) &
                (pl.col('prior_debut') == r['prior_debut']) & (pl.col('player_id') != r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2 + ((pl.col('pa_0')-r['pa_0'])/250)**2 +
                 ((pl.col('AAA_0_pa')-r['AAA_0_pa'])/250)**2 + ((pl.col('AA_0_pa')-r['AA_0_pa'])/250)**2 +
                 ((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2 + (pl.col('quality_0')-r['quality_0'])**2 +
                 2*(pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2 +
                 (pl.col('source_position') != r['source_position']).cast(pl.Float64)).alias('distance')).sort('distance','player_id').head(4)
            cols = ['row_id','player_id','player_name','origin_year','target_year','outer_fold','age','stage','source_position',
                    'prior_debut','pa_0','pa_1','pa_2','minor_pa_0','AAA_0_pa','AA_0_pa','quality_0',
                    'new_scout_rank_score_0','preseason_raw_p','preseason_p','preseason_raw_conditional_pa',
                    'preseason_conditional_pa','preseason_pa','preseason_rate','preseason_value','risk_q50','next_pa',
                    'next_value','reported_retired','hard_unavailable','profile_people','steamer_pa']
            cases.append(dict(origin={col:r[col] for col in cols}, selection=selection,
                information_date=note['information_date'], source_history=counts.filter((pl.col('player_id') == r['player_id']) &
                    pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_inputs=te.select(names).row(0,named=True), point_fit_path=str(point_path), saved_point_paths=paths,
                calibration_path=str(calibration_path), calibration_sha256=law['calibration_sha256'],
                concentration=law['concentration'], scalar_median=median,
                profile_support=support.filter((pl.col('row_id') == rid) & (pl.col('scope') == 'outer')).to_dicts(),
                peers=peers.select(*cols,'distance').to_dicts(),
                peer_limit='Origin-known separate level exposure, age, position, rank and summary quality; not exact injury, employment, rights or complete contact skill matches'))
    write('cases.json',cases)
    outputs = ['scores.json','intervals.json','cases.json']
    write('verification.json',dict(rows=30506,public_rows=2627,all_current_columns_exact=True,all_medians_recomputed=True,
        point_heads_replayed=replays,scalar_CDF_crossings=len(cases),player_walkthrough_status='pending',new_fits=0,
        saved_model_and_calibration_hashes=hashes, output_hashes={str(OUT/p):sha256_file(OUT/p) for p in outputs},
        protected_outcomes_used=False,current_candidate_changed=False))
    for s in summaries[:11]:
        print(s['scope'],s['rows'],{a:tuple(round(v[m],3) for m in ['rmse','mae','bias','total']) for a,v in s['scores'].items()},flush=True)
    for c in cases:
        r=c['origin']; print(r['row_id'],r['player_name'],r['origin_year'], 'p/c',round(r['preseason_p'],4),round(r['preseason_conditional_pa'],2),
            'mean/median/actual',round(r['preseason_pa'],2),r['risk_q50'],r['next_pa'],c['selection'],flush=True)
    print('Provisional until actual player review; no point forecast or benchmark standards changed.',flush=True)


def finalize():
    verify(read(OUT/'preflight.json')['source_hashes']); check=read(OUT/'verification.json')
    verify(check['saved_model_and_calibration_hashes']); verify(check['output_hashes'])
    notes_path=ROOT/'config/hitter_workload_location_review.json'; notes=read(notes_path); cases=read(OUT/'cases.json')
    assert set(notes['players']) == {str(c['origin']['row_id']) for c in cases}
    assert all(len(s)>160 for s in notes['players'].values())
    assert not notes['current_candidate_changed'] and not notes['full_goal_complete']
    doc=ROOT/'docs/hitter-workload-location-diagnostic-result.md'; content=doc.read_text(encoding='utf8')
    assert all(c['origin']['player_name'] in content and str(c['origin']['row_id']) in content for c in cases)
    frozen=json.loads(subprocess.check_output([str(ROOT/'.venv/Scripts/python.exe'),'-X','utf8',
        str(ROOT/'scripts/verify_hitter_full_2026_freeze.py')],cwd=ROOT))
    assert frozen['status']=='verified' and frozen['protected_2026_opened'] is False
    paths=[OUT/'preflight.json',OUT/'verification.json',OUT/'scores.json',OUT/'intervals.json',OUT/'cases.json',doc,notes_path]
    write('final-report.json',dict(new_fits=0,rows=30506,public_rows=2627,player_walkthrough_status='complete',
        reviewed_cases=len(cases),disposition=notes['disposition'],next_step=notes['next_step'],
        current_candidate_changed=False,full_goal_complete=False,protected_outcomes_used=False,frozen_verification=frozen,
        evidence_hashes={str(p):sha256_file(p) for p in paths}))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for filename in ['preflight.json','scores.json','intervals.json','verification.json','final-report.json']:
        target=EVIDENCE/filename
        if target.exists(): assert sha256_file(target)==sha256_file(OUT/filename)
        else: shutil.copyfile(OUT/filename,target)
    print('Reviewed diagnostic complete; current means and protected forecast unchanged.',flush=True)


if __name__=='__main__':
    {'prepare':prepare,'score':score,'finalize':finalize}[sys.argv[1]]()
