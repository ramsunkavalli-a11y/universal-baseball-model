"""Additive metadata repair and independent review, without refitting or rescoring."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_minor_statcast_forecast import route
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import EVENTS, VALUES
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
import prepare_hitter_minor_statcast_next_year as prep

META = ['draft_known','draft_rank','scout_listed_0','scout_rank_score_0',
        *[f'pooled_{b}_pa' for b in ['AAA','AA','Aplus','A','DSL']]]
ARMS = ['preseason','ridge_measurements','combined','minor_coverage','minor_measurements']


def repaired_rows(q, pre):
    rows = []
    for k in range(5):
        f = pl.read_parquet(prep.OUT/f'features-{k}.parquet')
        ids = [rid for c in pre['cells'] if c['fold']==k for rid in c['test_row_ids']]
        rows.append(f.filter(pl.col('row_id').is_in(ids)).select('row_id',*META))
    actual = pl.concat(rows).sort('row_id')
    assert q['row_id'].equals(actual['row_id'])
    changed = {}
    for n in META:
        assert q[n+'_right'].equals(actual[n]), n
        changed[n] = int((q[n]!=actual[n]).sum())
    return q.with_columns([actual[n] for n in META]), changed


def distance(o):
    d = ((pl.col('age')-o['age'])/3)**2+((pl.col('pa_0')-o['pa_0'])/300)**2
    for b in ['AAA','AA','Aplus','A','DSL']:
        d += ((pl.col(f'pooled_{b}_pa')-o[f'pooled_{b}_pa'])/300)**2
    d += (pl.col('scout_rank_score_0')-o['scout_rank_score_0'])**2
    d += (pl.col('draft_rank')-o['draft_rank'])**2
    return d+.25*(pl.col('draft_known')-o['draft_known'])**2


def peers():
    out=prep.OUT
    assert not (out/'peer-reporting-repair.json').exists(), 'Preserve additive repair'
    q=pl.read_parquet(out/'scored-predictions.parquet').sort('row_id')
    pre=prep.read(out/'preflight.json')
    fixed, changed=repaired_rows(q,pre)
    cases=prep.read(out/'cases.json')
    dated=pl.read_parquet(prep.ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    for c in cases['cases']:
        o=fixed.filter(pl.col('row_id')==c['origin']['row_id']).row(0,named=True)
        pool=fixed.filter((pl.col('origin_year')==o['origin_year']) &
             (pl.col('prior_debut')==o['prior_debut']) & (pl.col('player_id')!=o['player_id']))
        selected=pool.with_columns(distance(o).alias('peer_distance')).sort('peer_distance','player_id').head(4)
        c['original_origin_metadata']=c['origin']
        c['origin']=o
        if not o['next_pa']: c['origin']['actual_future_relative_rate']=None
        c['original_peers']=c['peers']
        fields=['row_id','player_id','player_name','age','snapshot_level','msc_eligible','msc_own_ev_n',
                *META,'preseason_pa','combined_rate','minor_coverage_rate','minor_measurements_rate',
                'combined_value','minor_measurements_value','next_pa','next_value','peer_distance']
        corrected=[]
        for p in selected.iter_rows(named=True):
            corrected.append(dict(**{n:p[n] for n in fields},
                actual_future_relative_rate=p['actual_future_relative_rate'] if p['next_pa'] else None,
                dated_production=dated.filter((pl.col('player_id')==p['player_id']) &
                    pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).to_dicts()))
        c['peers']=corrected
        print(o['player_name'],o['origin_year'],'=>',[(p['player_name'],p['next_pa']) for p in corrected],flush=True)
    cases['original_peer_rule']=cases['peer_rule']
    cases['peer_rule']='Same original distance formula; actual fold feature metadata replaces inherited ranking/level metadata. Future results never enter distance.'
    cases['player_walkthrough_status']='pending_readable_review'
    prep.write('peer-reporting-repair.json',cases)
    prep.write('peer-reporting-repair-receipt.json',dict(new_fits=0,forecasts_changed=False,
        primary_scores_changed=False,metadata_difference_counts=changed,
        original_cases_sha256=sha256_file(out/'cases.json'),original_scores_sha256=sha256_file(out/'scores.json'),
        repaired_cases_sha256=sha256_file(out/'peer-reporting-repair.json'),
        amendment_sha256=sha256_file(prep.ROOT/'docs/hitter-minor-statcast-reporting-amendment.md'),
        runner_sha256=sha256_file(Path(__file__))))


def scope(q, name):
    e=q.filter(pl.col('msc_eligible'))
    if name=='all': return q
    if name=='eligible': return e
    if name=='eligible_predebut': return e.filter(pl.col('prior_debut')==0)
    if name=='eligible_prior_MLB': return e.filter(pl.col('prior_debut')==1)
    if name=='never_debut': return q.filter(pl.col('prior_debut')==0)
    if name=='public': return q.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    if name=='fallback': return q.filter(~pl.col('msc_eligible'))
    if name.startswith('origin_'): return q.filter(pl.col('origin_year')==int(name.split('_')[-1]))
    if name.startswith('eligible_origin_'): return e.filter(pl.col('origin_year')==int(name.split('_')[-1]))
    if name.startswith('eligible_league_'): return e.filter(pl.col(f'msc_{name.split("_")[-1]}_ev_n')>0)
    if name.startswith('eligible_sample_'): return e.filter(pl.col('msc_sample_band')==name.removeprefix('eligible_sample_'))
    if name.startswith('eligible_exposure_'): return e.filter(pl.col('msc_exposure_band')==name.removeprefix('eligible_exposure_'))
    if name=='eligible_absent_profile': return e.filter(pl.col('minimum_profile_people')==0)
    if name=='eligible_sparse_profile': return e.filter(pl.col('minimum_profile_people')<20)
    if name=='eligible_upper_minors': return e.filter(pl.col('stage')=='Upper minors')
    if name=='eligible_lower_minors': return e.filter(pl.col('stage')=='Lower minors')
    raise ValueError(name)


def independent(g,arm,kind):
    if kind=='rate': g=g.filter(pl.col('next_pa')>0)
    result=[]
    for _,part in g.group_by('origin_year'):
        actual=part['actual_future_relative_rate' if kind=='rate' else 'next_value'].to_numpy()
        pred=part[arm+'_'+kind].to_numpy()
        w=part['next_pa'].to_numpy() if kind=='rate' else np.ones(len(part))
        err=pred-actual
        result.append([np.average(err**2,weights=w),np.average(np.abs(err),weights=w),np.average(err,weights=w)])
    return np.mean(result,axis=0)


def final():
    out=prep.OUT
    assert not (out/'final-review.json').exists(), 'Preserve final receipt'
    pre=prep.read(out/'preflight.json');fit=prep.read(out/'fit-report.json');scores=prep.read(out/'scores.json')
    prep.verify_hashes(pre['input_hashes'])
    assert sha256_file(out/'predictions.parquet')==fit['predictions_sha256']
    assert sha256_file(prep.ROOT/'scripts/score_hitter_minor_statcast_next_year.py')==scores['score_runner_sha256']
    q=pl.read_parquet(out/'scored-predictions.parquet').sort('row_id')
    anchor=pl.read_parquet(out/'anchor.parquet').sort('row_id')
    assert q.select(anchor.columns).equals(anchor) and len(q)==30506
    assert q['row_id'].n_unique()==30506 and q['target_year'].max()==2025
    counts=q.select(['count_'+e for e in EVENTS]).to_numpy()
    n=q['next_pa'].to_numpy(); active=n>0
    actual=np.zeros(len(q))
    index=counts@VALUES
    actual[active]=UNIT*(index[active]/n[active]-q.select(['target_env_'+e for e in EVENTS]).to_numpy()[active]@VALUES)
    assert np.array_equal(counts.sum(1),n)
    assert np.allclose(actual,q['actual_future_relative_rate'],atol=1e-10,rtol=0)
    common=np.zeros(len(q))
    common[active]=UNIT*(index[active]/n[active]-q.select(['origin_env_'+e for e in EVENTS]).to_numpy()[active]@VALUES)
    assert np.allclose(n*(common/600+q['origin_replacement_rate'].to_numpy()),q['next_value'],atol=1e-10,rtol=0)
    replays=0
    with threadpool_limits(limits=2):
        for k in range(5):
            f=pl.read_parquet(out/f'features-{k}.parquet')
            for c in [c for c in pre['cells'] if c['fold']==k]:
                tr,te,context,disabled=route(f,c['training_row_ids'],c['test_row_ids'],pre['minimum_context_people'])
                assert context==c['league_context'] and disabled==c['disabled_features']
                assert tr['target_year'].max()<=c['year'] and not set(tr['player_id'])&set(te['player_id'])
                got=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert te['row_id'].equals(got['row_id']) and te['msc_eligible'].equals(got['msc_eligible'])
                receipt=prep.read(out/f'fit-{c["year"]}-{k}.json');prep.verify_hashes(receipt['output_hashes'])
                for h in receipt['heads']:
                    replay=joblib.load(h['path']).predict(safe_matrix(te,h['features']))
                    assert np.allclose(replay,got[h['arm']+'_raw_rate'],atol=1e-12,rtol=0);replays+=1
    assert replays==20
    for arm in pre['arms']:
        fallback=q.filter(~pl.col('msc_eligible'))
        for kind in ['rate','value']: assert fallback[arm+'_'+kind].equals(fallback['combined_'+kind])
        assert np.allclose(q['preseason_pa']*(q[arm+'_rate']/600+q['origin_replacement_rate']),q[arm+'_value'],atol=1e-12,rtol=0)
    verified_scores=0
    for s in scores['scopes']:
        g=scope(q,s['scope']);assert len(g)==s['rows']
        assert np.isclose(g['next_value'].sum(),s['actual_value'],atol=1e-10)
        assert np.isclose(g['preseason_pa'].sum(),s['predicted_pa'],atol=1e-10)
        assert g['next_pa'].sum()==s['actual_pa']
        for kind,key in [('rate','participant_rate'),('value','contribution')]:
            for arm,reported in (s[key] or {}).items():
                assert np.allclose(independent(g,arm,kind),[reported['mse'],reported['mae'],reported['bias']],atol=1e-12,rtol=0)
                if kind=='value': assert np.isclose(g[arm+'_value'].sum(),reported['predicted_total'],atol=1e-10)
                verified_scores+=1
    review=prep.read(out/'peer-reporting-repair.json');manual=prep.read(prep.ROOT/'config/hitter_minor_statcast_next_year_review.json')
    assert {str(c['origin']['row_id']) for c in review['cases']}==set(manual) and len(review['cases'])==16
    fixed,changed=repaired_rows(q,pre)
    reasons={r for c in review['cases'] for r in c['selection']}
    assert {'largest gain','largest harm','false high','false low','ordinary active'}<=reasons
    for c in review['cases']:
        o=c['origin'];c['baseball_review']=manual[str(o['row_id'])]
        assert len(c['baseball_review'])>200 and len(c['peers'])==4
        assert all(x['season']<=o['origin_year'] for x in c['source_history']+c['launch_history'])
        assert all(x['season']==o['target_year'] for x in c['actual_history'])
        for name,tr in c['saved_traces'].items():
            expected=o['combined_rate'] if name=='combined_benchmark' else o[name+'_raw_rate']
            assert np.isclose(tr['intercept']+sum(t['signed_term'] for t in tr['all_terms']),expected,atol=1e-10)
        pool=fixed.filter((pl.col('origin_year')==o['origin_year']) & (pl.col('prior_debut')==o['prior_debut']) & (pl.col('player_id')!=o['player_id']))
        selected=pool.with_columns(distance(o).alias('peer_distance')).sort('peer_distance','player_id').head(4)
        assert selected['row_id'].to_list()==[p['row_id'] for p in c['peers']]
        for p in c['peers']:
            assert all(x['season']<=o['origin_year'] for x in p['dated_production'])
            if p['next_pa']==0: assert p['actual_future_relative_rate'] is None
    review['player_walkthrough_status']='complete'
    prep.write('reviewed-cases.json',review)
    freeze=subprocess.run([sys.executable,'-X','utf8',str(prep.ROOT/'scripts/verify_hitter_full_2026_freeze.py')],cwd=prep.ROOT,check=True,capture_output=True,text=True)
    tests=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-p','no:cacheprovider',
        'tests/test_hitter_minor_statcast_forecast.py','tests/test_hitter_minor_statcast_source.py',
        'tests/test_hitter_minor_statcast_review.py','tests/test_hitter_statcast_next_year.py',
        'tests/test_hitter_statcast_measurement.py','tests/test_hitter_statcast_history.py',
        'tests/test_mlb_contact_history.py','-q'],cwd=prep.ROOT,check=True,capture_output=True,text=True)
    doc=prep.ROOT/'docs/hitter-minor-statcast-next-year-result.md'
    assert doc.exists()
    paths=[out/n for n in ['preflight.json','fit-report.json','scores.json','cases.json','reviewed-cases.json',
        'scored-predictions.parquet','peer-reporting-repair.json','peer-reporting-repair-receipt.json']]
    paths += [doc,Path(__file__),prep.ROOT/'config/hitter_minor_statcast_next_year_review.json',
        prep.ROOT/'docs/hitter-minor-statcast-reporting-amendment.md']
    prep.write('final-review.json',dict(execution_integrity=True,independently_reconstructed_labels=True,
        independent_scores_verified=verified_scores,score_scopes=len(scores['scopes']),replayed_heads=replays,
        forecasts=30506,eligible_forecasts=3116,exact_combined_fallbacks=len(fallback),playing_time_unchanged=True,
        player_walkthrough_status='complete',case_origins=16,distinct_case_people=len({c['origin']['player_id'] for c in review['cases']}),
        original_case_metadata_preserved=True,corrected_peer_metadata_difference_counts=changed,
        predictive_success=False,reasonability='fails tiny-minor-sample influence; sparse comparable support remains',
        full_profile_validation=False,original_provider_vintage_known=False,independent_confirmation=False,
        disposition='do_not_adopt_this_joint_minor_head; repair precision and role separation before another fit',
        blanket_rejection_of_statcast=False,prior_positive_MLB_branch_unchanged=True,deployment_approved=False,
        protected_outcomes_used=False,protected_freeze=json.loads(freeze.stdout),focused_tests=tests.stdout,
        walkthrough_path=str(doc),artifact_hashes={str(p):sha256_file(p) for p in paths}))
    dest=prep.ROOT/'reports/model-evidence/hitter-minor-statcast-next-year';dest.mkdir(parents=True,exist_ok=True)
    compact=[n for n in q.columns if n in ['row_id','player_id','player_name','origin_year','target_year','outer_fold','age','prior_debut','stage',
        'preseason_pa','next_pa','next_value','actual_future_relative_rate','msc_eligible','msc_own_ev_n','minimum_profile_people',
        'origin_replacement_rate'] or n in [a+'_'+s for a in ARMS for s in ['rate','value']]]
    target=dest/'scored-predictions-compact.parquet';assert not target.exists()
    q.select(compact).write_parquet(target)
    assert pl.read_parquet(target).equals(q.select(compact))
    pack=[out/n for n in ['annual-launch-features.parquet','preflight.json','fit-report.json','scores.json','cases.json',
        'reviewed-cases.json','peer-reporting-repair-receipt.json','final-review.json','profile-support.parquet',
        'support.parquet','feature-ranges.json','prefit-development-errors.json']]
    pack += list(out.glob('calibration-*.json'))+list(out.glob('fit-*-*.json'))+list(out.glob('*.joblib'))
    for p in pack:
        target=dest/p.name;assert not target.exists();shutil.copyfile(p,target)
        assert sha256_file(target)==sha256_file(p)
    manifest=dict(copied_hashes={str(dest/p.name):sha256_file(dest/p.name) for p in pack},
        compact_sha256=sha256_file(dest/'scored-predictions-compact.parquet'),
        full_scored_local_path=str(out/'scored-predictions.parquet'),full_scored_sha256=sha256_file(out/'scored-predictions.parquet'),
        feature_frames_retained_locally_not_duplicated_in_git={str(out/f'features-{k}.parquet'):sha256_file(out/f'features-{k}.parquet') for k in range(5)})
    assert not (dest/'evidence-manifest.json').exists()
    (dest/'evidence-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
    print('Review complete: 20 heads replayed,',verified_scores,'scores independently checked; no deployment.',flush=True)
    print(tests.stdout,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['peers','final'],required=True)
    args=parser.parse_args()
    peers() if args.phase=='peers' else final()
