"""Seal a no-fit error budget and replay every selected player's three heads."""
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
from universal_baseball.hitter_error_budget import components,summary
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.mlb_event_logit import EVENTS
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_offense_risk as e
import diagnose_hitter_workload_location as location

ROOT=e.ROOT; CURRENT=e.current.OUT
OUT=ROOT/'reports/generated/hitter-error-budget'; EVIDENCE=ROOT/'reports/model-evidence/hitter-error-budget'
FIXED=[(592450,2024),(701762,2024),(694671,2023),(668804,2018),(456781,2022),
       (458015,2023),(474832,2023),(670867,2017)]


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True); path=OUT/name
    assert not path.exists(),f'Preserve receipt {path}'
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf8',newline='\n')


def prepare():
    for path in [location.OUT/'final-report.json',e.OUT/'final-report.json']:
        final=e.read(path); assert final['player_walkthrough_status']=='complete'
        for key in ['evidence_hashes','local_fit_hashes']:
            if key in final:e.check_hashes(final[key])
    paths=[Path(__file__),ROOT/'docs/hitter-error-budget-contract.md',ROOT/'src/universal_baseball/hitter_error_budget.py',
        ROOT/'tests/test_hitter_error_budget.py',location.OUT/'final-report.json',e.OUT/'final-report.json',
        e.OUT/'preflight.json',e.OUT/'fit-report.json',e.OUT/'outer-support.parquet',CURRENT/'features.parquet',
        CURRENT/'preflight.json',CURRENT/'profile-support.parquet',CURRENT/'scored-predictions.parquet',
        ROOT/'reports/generated/practical-hitter-v31/counts.parquet',ROOT/'scripts/prepare_practical_hitter_v33.py',
        ROOT/'src/universal_baseball/hitter_compatible_value.py']
    write('preflight.json',dict(new_fits=0,fixed_players=FIXED,previous_player_reviews_complete=True,
        source_hashes={str(p):sha256_file(p) for p in paths},protected_outcomes_used=False,current_candidate_changed=False))
    print('Completed reviews and source seals verified before error accounting.',flush=True)


def score():
    e.check_hashes(e.read(OUT/'preflight.json')['source_hashes']); assert not (OUT/'scores.json').exists()
    q=pl.read_parquet(CURRENT/'scored-predictions.parquet').sort('row_id')
    assert len(q)==30506 and q['row_id'].n_unique()==30506 and q['target_year'].max()==2025
    actual=labels(q.select(['count_'+s for s in EVENTS]).to_numpy(),q.select(['origin_env_'+s for s in EVENTS]).to_numpy(),
        q.select(['target_env_'+s for s in EVENTS]).to_numpy(),q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(actual['pa'],q['next_pa'])
    assert np.allclose(actual['common_rate'],q['next_batting_rate'],atol=1e-10,rtol=0)
    assert np.allclose(actual['common_value'],q['next_value'],atol=1e-10,rtol=0)
    g=q['preseason_rate'].to_numpy()/600+q['origin_replacement_rate'].to_numpy()
    t=np.full(len(q),np.nan); active=q['next_pa'].to_numpy()>0
    t[active]=q['next_value'].to_numpy()[active]/q['next_pa'].to_numpy()[active]
    pa,value=components(q['preseason_p'],q['preseason_conditional_pa'],q['next_pa'],g,t)
    assert np.allclose(value.sum(1),q['preseason_value']-q['next_value'],atol=1e-10,rtol=0)
    names=['participation','workload','production']
    q=q.with_columns(*[pl.Series('pa_'+n,pa[:,i]) for i,n in enumerate(names[:2])],
        *[pl.Series('value_'+n,value[:,i]) for i,n in enumerate(names)],
        pl.Series('value_error',value.sum(1)),pl.Series('value_cancellation',abs(value).sum(1)-abs(value.sum(1))))
    scopes=[('all',q),('public',location.public(q)),('current_MLB',q.filter(pl.col('pa_0')>0)),
        ('absent_prior_debut',q.filter((pl.col('prior_debut')==1)&(pl.col('pa_0')==0))),
        ('upper_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',q.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('thin_new_draftee',q.filter((pl.col('draft_known')==1)&(pl.col('draft_year')==pl.col('origin_year'))&
            (pl.sum_horizontal('minor_pa_0','minor_pa_1','minor_pa_2','pa_0','pa_1','pa_2')<150))),
        ('current_MLB_listing0',q.filter((pl.col('pa_0')>0)&(pl.col('on_40man')==0))),
        ('current_MLB_listing1',q.filter((pl.col('pa_0')>0)&(pl.col('on_40man')==1)))]
    for lo,hi in [(1,199),(200,399),(400,599),(600,10000)]:
        scopes.append((f'current_PA_{lo}_{hi}',q.filter(pl.col('pa_0').is_between(lo,hi))))
    for year in sorted(q['origin_year'].unique()):scopes.append((f'origin_{year}',q.filter(pl.col('origin_year')==year)))
    assert len(location.public(q))==2627
    scores=[]; bins=[]
    for scope,frame in scopes:
        if not len(frame):continue
        years=frame['target_year'].to_numpy()
        scores.append(dict(scope=scope,rows=len(frame),people=frame['player_id'].n_unique(),
            predicted_pa=float(frame['preseason_pa'].sum()),actual_pa=int(frame['next_pa'].sum()),
            predicted_value=float(frame['preseason_value'].sum()),actual_value=float(frame['next_value'].sum()),
            pa=summary(frame.select('pa_participation','pa_workload').to_numpy(),years,names[:2]),
            value=summary(frame.select(['value_'+n for n in names]).to_numpy(),years,names)))
        if scope not in ['public','upper_never_debut','lower_never_debut']:continue
        for lo,hi in [(0,.01),(.01,.1),(.1,.5),(.5,.8),(.8,1.00001)]:
            b=frame.filter((pl.col('preseason_p')>=lo)&(pl.col('preseason_p')<hi)); a=b.filter(pl.col('next_pa')>0)
            if not len(b):continue
            bins.append(dict(scope=scope,p_lower=lo,p_upper=min(hi,1),rows=len(b),
                expected_arrivals=float(b['preseason_p'].sum()),actual_arrivals=len(a),
                actual_pa=int(b['next_pa'].sum()),expected_pa=float(b['preseason_pa'].sum()),
                active_conditional_pa=float(a['preseason_conditional_pa'].sum()),
                active_conditional_mae=float((a['preseason_conditional_pa']-a['next_pa']).abs().mean()) if len(a) else None,
                limit='Raw pooled descriptive bins; actual activity never generates forecasts'))
    write('scores.json',scores);write('probability-bins.json',bins)
    chosen={}
    def choose(frame,reason):
        assert len(frame); chosen.setdefault(int(frame['row_id'][0]),[]).append(reason)
    for pid,year in FIXED:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==year)),'fixed before accounting')
    choose(q.sort('value_error','row_id',descending=[True,False]),'largest false high value')
    choose(q.sort('value_error','row_id'),'largest false low value')
    choose(q.sort('value_cancellation','row_id',descending=[True,False]),'largest component cancellation')
    choose(q.filter(pl.col('next_pa').is_between(200,600)).with_columns(pl.col('value_error').abs().alias('ordinary_error'))
        .sort('ordinary_error','row_id'),'ordinary active value')
    features=e.context(); pa_names=e.read(CURRENT/'preflight.json')['pa_features']; rate_names=e.read(e.OUT/'preflight.json')['rate_features']
    counts=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/counts.parquet')
    support=pl.read_parquet(e.OUT/'outer-support.parquet'); fit=e.read(e.OUT/'fit-report.json')['cells']
    cases=[]; hashes={}; replays=0
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True); te=features.filter(pl.col('row_id')==rid)
            y,k=r['origin_year'],r['outer_fold']; note_path=CURRENT/f'fit-{y}-{k}.json'; note=e.read(note_path)
            hashes[str(note_path)]=sha256_file(note_path); paths={}
            for h in note['heads']:
                e.check_hashes({h['path']:h['sha256']}); hashes[h['path']]=h['sha256']; model=joblib.load(h['path']); x=te.select(pa_names).to_numpy()
                if h['head']=='participation':
                    assert np.isclose(model.predict_proba(x)[0,1],r['preseason_raw_p'],atol=1e-10,rtol=0)
                    paths[h['head']]=logit_trace(model,x[0],pa_names)
                else:
                    assert np.isclose(model.predict(x)[0],r['preseason_raw_conditional_pa'],atol=1e-10,rtol=0)
                    paths[h['head']]=trace(model,x[0],pa_names)
                replays+=1
            rh=next(c for c in fit if c['year']==y and c['fold']==k)['outer_rate_model']
            e.check_hashes({rh['path']:rh['sha256']});hashes[rh['path']]=rh['sha256']; model=joblib.load(rh['path']); x=safe_matrix(te,rate_names)[0]
            predicted=float(model.predict(x[None,:])[0]); assert np.isclose(predicted,r['preseason_rate'],atol=1e-10,rtol=0);replays+=1
            terms=x*model.coef_; assert np.isclose(terms.sum()+model.intercept_,predicted,atol=1e-10,rtol=0)
            peers=q.filter((pl.col('origin_year')==y)&(pl.col('stage')==r['stage'])&(pl.col('prior_debut')==r['prior_debut'])&
                (pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('pa_0')-r['pa_0'])/250)**2+((pl.col('AAA_0_pa')-r['AAA_0_pa'])/250)**2+
                 ((pl.col('AA_0_pa')-r['AA_0_pa'])/250)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+
                 (pl.col('quality_0')-r['quality_0'])**2+2*(pl.col('new_scout_rank_score_0')-r['new_scout_rank_score_0'])**2+
                 (pl.col('source_position')!=r['source_position']).cast(pl.Float64)).alias('distance')).sort('distance','player_id').head(4)
            cols=['row_id','player_id','player_name','origin_year','target_year','outer_fold','age','stage','source_position','prior_debut',
                'pa_0','pa_1','pa_2','minor_pa_0','preseason_p','preseason_conditional_pa','preseason_pa','preseason_rate','preseason_value',
                'next_pa','next_value','next_batting_rate','origin_replacement_rate','on_40man','needs_availability_scenario',
                'value_participation','value_workload','value_production','value_error','value_cancellation','pa_participation','pa_workload']
            origin={col:r[col] for col in cols};
            if r['next_pa']==0:origin['next_batting_rate']=None
            cases.append(dict(origin=origin,selection=reasons,information_date=note['information_date'],
                actual_pa_inputs=te.select(pa_names).row(0,named=True),actual_rate_inputs=te.select(rate_names).row(0,named=True),
                transformed_rate_inputs=dict(zip(rate_names,x.tolist())),saved_opportunity_paths=paths,
                rate_model=rh,rate_intercept=float(model.intercept_),rate_terms=dict(zip(rate_names,terms.tolist())),
                rate_profile_support=support.filter(pl.col('row_id')==rid).to_dicts(),
                source_history=counts.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_history=counts.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==y+1)&(pl.col('bucket')=='MLB')).to_dicts(),
                peers=peers.select(*cols,'distance').with_columns(pl.when(pl.col('next_pa')==0).then(None).otherwise(pl.col('next_batting_rate')).alias('next_batting_rate')).to_dicts(),
                peer_limit='Outcome-blind broad profile and separate level exposure; not identical injury, rights, foreign history or contact talent'))
    write('cases.json',cases)
    write('verification.json',dict(forecasts=30506,public_rows=2627,new_fits=0,point_heads_replayed=replays,
        raw_event_labels_recomputed=True,all_PA_and_value_identities_exact=True,all_MSE_MAE_allocations_exact=True,
        inactive_actual_rate_undefined=True,player_walkthrough_status='pending',current_candidate_changed=False,
        protected_outcomes_used=False,model_hashes=hashes,
        output_hashes={str(OUT/s):sha256_file(OUT/s) for s in ['scores.json','probability-bins.json','cases.json']}))
    for s in scores[:9]:print(s['scope'], 'PA MSE allocation',{n:round(v['mse_allocation'],3) for n,v in s['pa']['components'].items()},
        'value MSE allocation',{n:round(v['mse_allocation'],6) for n,v in s['value']['components'].items()},flush=True)
    for c in cases:
        r=c['origin']; print(r['row_id'],r['player_name'],r['origin_year'],'value mean/actual',round(r['preseason_value'],3),round(r['next_value'],3),
            'parts',[round(r['value_'+n],3) for n in names],'PA parts',[round(r['pa_'+n],2) for n in names[:2]],'rate',round(r['preseason_rate'],3),None if r['next_batting_rate'] is None else round(r['next_batting_rate'],3),flush=True)
    print('Player review pending; no predictive improvement claimed.',flush=True)


def finalize():
    e.check_hashes(e.read(OUT/'preflight.json')['source_hashes']); check=e.read(OUT/'verification.json')
    e.check_hashes(check['model_hashes']);e.check_hashes(check['output_hashes'])
    review=ROOT/'config/hitter_error_budget_review.json'; notes=e.read(review); cases=e.read(OUT/'cases.json')
    assert set(notes['players'])=={str(c['origin']['row_id']) for c in cases}
    assert all(len(v)>160 for v in notes['players'].values())
    doc=ROOT/'docs/hitter-error-budget-result.md';text=doc.read_text(encoding='utf8')
    assert all(c['origin']['player_name'] in text and str(c['origin']['row_id']) in text for c in cases)
    freeze=json.loads(subprocess.check_output([str(ROOT/'.venv/Scripts/python.exe'),'-X','utf8',str(ROOT/'scripts/verify_hitter_full_2026_freeze.py')],cwd=ROOT))
    assert freeze['status']=='verified' and freeze['protected_2026_opened'] is False
    paths=[OUT/s for s in ['preflight.json','scores.json','probability-bins.json','cases.json','verification.json']]+[doc,review]
    write('final-report.json',dict(player_walkthrough_status='complete',reviewed_cases=len(cases),new_fits=0,
        disposition=notes['disposition'],next_step=notes['next_step'],current_candidate_changed=False,full_goal_complete=False,
        protected_outcomes_used=False,frozen_verification=freeze,evidence_hashes={str(p):sha256_file(p) for p in paths}))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for name in ['preflight.json','scores.json','probability-bins.json','cases.json','verification.json','final-report.json']:
        target=EVIDENCE/name
        assert not target.exists();shutil.copyfile(OUT/name,target)
    print('Completed player error review; candidate and protected forecast unchanged.',flush=True)


if __name__=='__main__':{'prepare':prepare,'score':score,'finalize':finalize}[sys.argv[1]]()
