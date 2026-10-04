"""Inventory the actual candidate and existing availability evidence, without fitting."""
from datetime import date
from pathlib import Path
import argparse
import gzip
import json
import shutil
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_observed_return import as_of
from universal_baseball.histogram_prediction_trace import trace
from score_hitter_compatible_value_v63 import linear_trace
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_value_integration_v76 as e

ROOT=e.ROOT
OUT=ROOT/'reports/generated/hitter-candidate-integration-audit'
CURRENT=e.previous.OUT
STATUS=ROOT/'reports/generated/practical-hitter-opportunity-status-v59'
RETURN=ROOT/'reports/generated/hitter-observed-return-v60'
RATE=ROOT/'reports/generated/practical-hitter-numeric-repair-v53'
FIXED=[('Fernando Tatis Jr.',2022),('Matt McLain',2024),('Gavin Lux',2023),
    ('Wander Franco',2023),('Brandon Belt',2023),('Tucupita Marcano',2024),('Eric Thames',2016)]
CASE_TEAMS=[135,113,119,139,141,135,158]
REVIEW=ROOT/'config/hitter_candidate_integration_review.json'
DOCUMENT=ROOT/'docs/hitter-candidate-integration-audit.md'


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8')


def main():
    completed=e.read(e.OUT/'report.json')
    assert completed['player_walkthrough_status']=='complete'
    e.verify(completed['review_hashes']);e.verify(completed['source_and_execution_hashes'])
    pre=e.read(CURRENT/'preflight.json');e.verify(pre['input_hashes'])
    returned=e.read(RETURN/'report.json')
    assert returned['player_walkthrough_status']=='complete'
    e.verify(returned['input_hashes']);e.verify(returned['output_hashes'])
    f=pl.read_parquet(CURRENT/'features.parquet')
    q=pl.read_parquet(CURRENT/'scored-predictions.parquet')
    state=pl.read_parquet(RETURN/'observation-states.parquet')
    context=pl.read_parquet(STATUS/'context.parquet')
    assert len(f)==len(context)==len(state)==63282 and len(q)==30506
    keys=['row_id','player_id','origin_year']
    assert f.select(keys).sort('row_id').equals(state.select(keys).sort('row_id'))
    assert f.select(keys).sort('row_id').equals(context.select(keys).sort('row_id'))
    fields=['availability_state','hard_reason','nonmedical_reason','finite_ineligibility_end',
        'context_capture_scope','retired_evidence','foreign_performance_missing','context_acquired',
        'context_minor_contract','context_scope_exit','context_nonmedical_unresolved']
    j=q.join(context.select(*keys,*fields),on=keys,validate='1:1').join(state,on=keys,validate='1:1')
    assert len(j)==len(q)
    actual_inputs=set(pre['pa_features'])
    modeled_status=[n for n in actual_inputs if n.startswith(('status_','op_','il_','context_'))]
    assert modeled_status==[]
    assert j.filter(pl.col('availability_state')=='permanent_ineligible')['preseason_pa'].sum()==0
    groups=j.group_by('availability_state').agg(pl.len().alias('rows'),
        pl.col('player_id').n_unique().alias('people'),pl.col('preseason_pa').sum().alias('expected_pa'),
        pl.col('next_pa').sum().alias('actual_pa')).sort('rows',descending=True)
    absent=j.filter((pl.col('pa_0')==0)&(pl.col('prior_debut')==1))
    absentgroups=absent.group_by('availability_state').agg(pl.len().alias('rows'),
        pl.col('player_id').n_unique().alias('people'),pl.col('preseason_pa').sum().alias('expected_pa'),
        pl.col('next_pa').sum().alias('actual_pa')).sort('rows',descending=True)
    hist=pl.read_parquet(e.COUNTS)
    broad=pl.read_parquet(CURRENT/'support.parquet')
    refined=pl.read_parquet(CURRENT/'profile-support.parquet')
    ledger=e.read(STATUS/'records.json')
    ratenames=e.read(RATE/'preflight.json')['rate_features']
    cases=[];paths=[]
    with threadpool_limits(limits=2):
        for (name,y),team in zip(FIXED,CASE_TEAMS,strict=True):
            g=j.filter((pl.col('player_name')==name)&(pl.col('origin_year')==y));assert len(g)==1
            r=g.row(0,named=True);s=f.filter(pl.col('row_id')==r['row_id']);k=r['outer_fold']
            saved={}
            for h in e.read(CURRENT/f'fit-{y}-{k}.json')['heads']:
                e.verify({h['path']:h['sha256']});m=joblib.load(h['path']);x=s.select(pre['pa_features']).to_numpy()
                if h['head']=='participation':
                    pred=m.predict_proba(x)[0,1]
                    assert np.isclose(pred,r['preseason_raw_p'],atol=1e-10)
                    saved[h['head']]=logit_trace(m,x[0],pre['pa_features'])
                else:
                    pred=m.predict(x)[0];assert np.isclose(pred,r['preseason_raw_conditional_pa'],atol=1e-10)
                    saved[h['head']]=trace(m,x[0],pre['pa_features'])
                paths.append(Path(h['path']))
            h=next(h for h in e.read(RATE/f'fit-{y}-{k}.json')['heads'] if h['head']=='rate')
            e.verify({h['path']:h['sha256']});m=joblib.load(h['path']);x=safe_matrix(s,ratenames)
            assert np.isclose(m.predict(x)[0],r['preseason_rate'],atol=1e-10)
            saved['rate']=linear_trace(m,x[0],ratenames);paths.append(Path(h['path']))
            hard=r['hard_unavailable'] or r['reported_retired']
            prob=0 if hard else r['preseason_raw_p']
            assert np.isclose(prob*np.clip(r['preseason_raw_conditional_pa'],1,800),r['preseason_pa'],atol=1e-10)
            eligible=j.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==r['prior_debut'])&
                (pl.col('stage')==r['stage'])&(pl.col('player_id')!=r['player_id']))
            distance=((pl.col('age')-r['age'])/3)**2+sum(((pl.col('pa_'+str(lag))-r['pa_'+str(lag)])/250)**2 for lag in range(3))
            peer=eligible.with_columns(distance.alias('distance')).sort('distance','player_id').head(4)
            peerfields=['player_name','age','stage','pa_0','pa_1','pa_2','availability_state',
                'preseason_pa','next_pa','distance']
            dated=as_of(ledger.get(str(r['player_id']),[]),date(y,12,31))
            assert all(z['available_date']<=date(y,12,31) for z in dated)
            rosterpath=ROOT/f'reports/generated/hitter-arrival-source-repair-v1/captures/roster/{y}/{team}.json.gz'
            with gzip.open(rosterpath,'rt',encoding='utf8') as handle: capture=json.load(handle)
            assert capture['params']=={'rosterType':'40Man','season':y,'date':f'{y}-12-31'}
            membership=[z for z in capture['payload']['roster'] if z['person']['id']==r['player_id']]
            assert bool(membership)==bool(r['on_40man'])
            paths.append(rosterpath)
            cases.append(dict(origin={n:r[n] for n in ['row_id','player_id','player_name','origin_year','outer_fold',
                'age','stage','prior_debut','pa_0','pa_1','pa_2','on_40man','hard_unavailable','reported_retired',
                'preseason_raw_p','preseason_p','preseason_conditional_pa','preseason_pa','preseason_rate',
                'preseason_value','next_pa','next_value',*fields,*[n for n in state.columns if n not in keys]]},
                actual_inputs=s.select(pre['pa_features']).row(0,named=True),saved_current_paths=saved,
                dated_records=dated,source_history=hist.filter((pl.col('player_id')==r['player_id'])&
                    pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                roster_capture=dict(path=str(rosterpath),params=capture['params'],returned_case_rows=membership,
                    claim_limit='Returned-set presence only; request date does not certify complete historical reserve rights'),
                broad_opportunity_support=broad.filter(pl.col('row_id')==r['row_id']).to_dicts(),
                refined_opportunity_support=refined.filter(pl.col('row_id')==r['row_id']).to_dicts(),
                peers=peer.select(peerfields).to_dicts(),
                peer_limit='Origin-only generic workload controls, not matched medical, finite suspension, foreign talent or positional jobs'))
    inputs=[CURRENT/'preflight.json',CURRENT/'features.parquet',CURRENT/'scored-predictions.parquet',
        STATUS/'context.parquet',STATUS/'records.json',RETURN/'report.json',RETURN/'observation-states.parquet',
        RATE/'preflight.json',CURRENT/'support.parquet',CURRENT/'profile-support.parquet',
        e.OUT/'report.json',Path(__file__),*paths]
    write('cases.json',cases)
    write('report.json',dict(candidate_opportunity_predictors=pre['pa_features'],candidate_rate_predictors=ratenames,
        modeled_status_features=modeled_status,
        source_rows=63282,evaluation_rows=30506,availability_groups=groups.to_dicts(),
        absent_prior_mlb_groups=absentgroups.to_dicts(),current_saved_heads_replayed=21,
        corrected_medical_observation_in_current_predictors=False,
        availability_state_in_current_predictors=False,permanent_and_reported_retired_wrappers_present=True,
        new_models_fitted=False,predictions_changed=False,protected_outcomes_used=False,
        individual_case_interpretation='Evidence inventory; no status effect or new predictive gain established',
        player_walkthrough_status='pending_manual_review',
        input_hashes={str(p):sha256_file(p) for p in inputs},case_sha256=sha256_file(OUT/'cases.json')))
    print(groups,flush=True)
    print('Absent prior MLB',absentgroups,flush=True)
    for c in cases:
        r=c['origin'];print(r['player_name'],r['origin_year'],r['availability_state'],
            'continuing_medical_observation',r['recorded_unresolved'],
            'PA',round(r['preseason_pa'],2),r['next_pa'],flush=True)


def validate_manual_review(cases,review):
    expected={c['origin']['row_id'] for c in cases}
    notes=review['cases']
    ids=[n['row_id'] for n in notes]
    if len(ids)!=len(set(ids)) or set(ids)!=expected:
        raise ValueError('Review must cover every saved case exactly once')
    required=('source_interpretation','forecast_interpretation','support_and_peers_limit','disposition')
    for note in notes:
        if any(not isinstance(note.get(field),str) or not note[field].strip() for field in required):
            raise ValueError('A case lacks actual source, forecast, support or disposition review')
    if review.get('new_predictive_gain_claimed') is not False:
        raise ValueError('This inventory cannot establish a new predictive gain')


def finalize():
    report=e.read(OUT/'report.json');e.verify(report['input_hashes'])
    assert sha256_file(OUT/'cases.json')==report['case_sha256']
    cases=e.read(OUT/'cases.json');review=e.read(REVIEW)
    validate_manual_review(cases,review)
    text=DOCUMENT.read_text(encoding='utf8')
    assert all(c['origin']['player_name'] in text for c in cases)
    final=dict(report,player_walkthrough_status='complete',review_kind='Source and current-model inventory, not a new experiment',
        review_hashes={str(p):sha256_file(p) for p in [REVIEW,DOCUMENT]},
        next_action=review['next_action'],candidate_changed=False,deployment_approved=False)
    write('reviewed-cases.json',review)
    write('final-report.json',final)
    dest=ROOT/'reports/model-evidence/hitter-candidate-integration-audit';dest.mkdir(parents=True,exist_ok=True)
    for name in ['cases.json','report.json','reviewed-cases.json','final-report.json']:
        shutil.copy2(OUT/name,dest/name)
        assert sha256_file(OUT/name)==sha256_file(dest/name)
    print('Seven player reviews complete; no fitted model or forecast changed',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--finalize',action='store_true');args=parser.parse_args()
    finalize() if args.finalize else main()
