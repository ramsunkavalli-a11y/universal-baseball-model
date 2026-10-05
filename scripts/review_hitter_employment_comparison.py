"""Matched scores and exact source-to-head player traces, pending human judgment."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from run_hitter_employment_comparison import ROOT,GEN,OLD,OUT,FIX,read,save,verify
from universal_baseball.employment_comparison import profiles
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.storage import sha256_file
from prepare_hitter_overseas_integration import ANCHOR,annual_labels
from review_hitter_overseas_integration import score,origin_weights
from review_hitter_evidence_representation import interval
from evaluate_hitter_readiness_v49 import logit_trace


def main():
    if (OUT/'review-receipt.json').exists(): raise ValueError('Preserve reviewed execution')
    pre=read(OUT/'preflight.json');verify(pre['hashes']);fit=read(OUT/'fit-report.json')
    assert sha256_file(OUT/'predictions.parquet')==fit['predictions_sha256']
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    original=q.filter(~pl.col('source_addition'));assert original.height==30506
    stints=pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet')
    assert stints['season'].max()<=2025
    actual,env=annual_labels(stints)
    raw=np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.to_dicts()])
    lab=labels(raw,np.array([env[y] for y in q['origin_year']]),np.array([env[y] for y in q['target_year']]),
        q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'],q['next_pa'])
    assert np.allclose(lab['relative_value'],q['actual_relative_value'],atol=1e-10,rtol=0)
    assert np.allclose(lab['relative_rate'],q['actual_relative_rate'],atol=1e-10,rtol=0)
    for arm in ['old_job','corrected_job']:
        assert np.allclose(q[arm+'_value'],q[arm+'_pa']*(q[arm+'_rate']/600+q['origin_replacement_rate']),atol=1e-10)
    assert q['old_job_rate'].equals(q['corrected_job_rate'])
    models={};replays=0
    oldfit=read(OLD/'fit-report.json')
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y,k=c['origin'],c['fold'];g=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)).sort('row_id')
            for h in c['heads']:
                path=ROOT/h['path'];assert sha256_file(path)==h['sha256'];m=joblib.load(path)
                f=pl.read_parquet(OUT/f'features-{k}.parquet',columns=['row_id',*h['features']]).filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert f['row_id'].equals(g['row_id']);x=f.select(h['features']).to_numpy()
                v=m.predict_proba(x)[:,1] if h['head']=='participation' else m.predict(x)
                column='corrected_job_raw_p' if h['head']=='participation' else 'corrected_job_raw_conditional_pa'
                assert np.allclose(v,g[column],atol=1e-10,rtol=0);replays+=1
                models['corrected_job',y,k,h['head']]=m
            for h in next(r for r in oldfit['cells'] if (r['origin'],r['fold'])==(y,k))['heads']:
                if h['arm']=='common':
                    assert sha256_file(Path(h['path']))==h['sha256']
                    models['old_job',y,k,h['head']]=joblib.load(h['path'])
    assert replays==70
    selector=['row_id','player_id','player_name','origin_year','age','pa_0','stage','prior_debut',
              'professional_work_0','last_first_team_known','evidence_foreign_source_present','status_major_link',
              'status_minor_agreement','status_agreement_unspecified','status_released','status_acquisition_only',
              'status_employment_unknown','status_hard_unavailable','status_unresolved_nonmedical','status_finite_nonmedical']
    origin=profiles(pl.read_parquet(OUT/'features-0.parquet',columns=selector)).filter(pl.col('row_id').is_in(q['row_id'].to_list()))
    foreign_ids=origin.filter(pl.col('foreign_source'))['row_id'].to_list()
    anchor=pl.read_parquet(ANCHOR,columns=['row_id','steamer_pa','steamer_rate','steamer_index','zips_index','common_zips_rate'])
    public=original.join(anchor,on='row_id',how='left',validate='1:1').filter(
        (pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert public.height==2627
    scopes=[('original_all',original),('additions',q.filter(pl.col('source_addition'))),('public',public),
        ('foreign',q.filter(pl.col('row_id').is_in(foreign_ids))),
        ('affected_original',original.filter(pl.col('employment_input_changed'))),
        ('unaffected_original',original.filter(~pl.col('employment_input_changed'))),
        ('current_regular',original.filter(pl.col('pa_0')>=400)),
        ('current_partial',original.filter(pl.col('pa_0').is_between(1,399))),
        ('absent_prior_debut',original.filter((pl.col('pa_0')==0)&(pl.col('prior_debut')>0)))]
    scopes += [('origin_'+str(y),original.filter(pl.col('origin_year')==y)) for y in sorted(original['origin_year'].unique())]
    scopes += [('stage_'+s,original.filter(pl.col('stage')==s)) for s in sorted(original['stage'].unique())]
    scopes += [('never_'+s,original.filter((pl.col('stage')==s)&(pl.col('prior_debut')==0))) for s in ['Upper minors','Lower minors']]
    scored=[]
    for name,g in scopes:
        if not len(g):continue
        arms=['old_job','corrected_job']+([] if g['source_addition'].any() else ['current'])
        actualyes=g['next_pa']>0
        scored.append(dict(scope=name,rows=g.height,people=g['player_id'].n_unique(),actual_PA=int(g['next_pa'].sum()),
            actual_participants=int(actualyes.sum()),actual_value=float(g['actual_relative_value'].sum()),
            scores={a:score(g,a) for a in arms},allocation={a:dict(
                PA_to_participants=float(g.filter(actualyes)[a+'_pa'].sum()),
                PA_to_nonparticipants=float(g.filter(~actualyes)[a+'_pa'].sum())) for a in arms}))
    pe=public['steamer_pa'].to_numpy()-public['next_pa'].to_numpy();w=origin_weights(public)
    ve=public['steamer_pa'].to_numpy()*(public['steamer_rate'].to_numpy()/600+public['origin_replacement_rate'].to_numpy())-public['actual_relative_value'].to_numpy()
    benchmark=dict(rows=2627,PA_RMSE=float(np.sqrt(w@(pe**2))),PA_MAE=float(w@abs(pe)),
        batting_contribution_RMSE=float(np.sqrt(w@(ve**2))),
        qualification='Existing qualified prior-MLB cohort; release-date and park/rate-reference differences remain. ZiPS PA not unconditional; missing overseas rows not zero.')
    save('scores.json',dict(scopes=scored,public_steamer=benchmark,fixed_talent_no_rate_improvement_test=True))
    with threadpool_limits(limits=2):
        comparisons=[dict(scope=name,candidate='corrected_job',baseline=b,
            intervals=interval(g,'corrected_job',b)) for name,g,b in [
                ('original_all',original,'old_job'),('original_all',original,'current'),
                ('affected_original',original.filter(pl.col('employment_input_changed')),'old_job'),
                ('public',public,'old_job')]]
    save('intervals.json',dict(seed=84,repetitions=2000,comparisons=comparisons))
    selected={r['origin']['row_id']:['retained domestic diagnostic'] for r in read(OLD/'reviewed-cases.json')['cases']}
    for r in read(GEN/'overseas-opportunity-inventory/inventory.json')['walks']:
        selected.setdefault(r['row_id'],[]).append('retained overseas focal or outcome-blind peer')
    for key in [('2016',400018),('2017',430652)]:
        g=q.filter((pl.col('origin_year')==int(key[0]))&(pl.col('player_id')==key[1]))
        assert g.height==1;selected.setdefault(g['row_id'][0],[]).append('ordinary assignment source control')
    diagnostic=[]
    def choose(g,why):
        if g.height:
            rid=int(g['row_id'][0]);selected.setdefault(rid,[]).append(why);diagnostic.append(rid)
    for baseline in ['old_job','current']:
        z=original.with_columns(((pl.col('corrected_job_value')-pl.col('actual_relative_value'))**2-
            (pl.col(baseline+'_value')-pl.col('actual_relative_value'))**2).alias('delta'),
            (pl.col('corrected_job_value')-pl.col('actual_relative_value')).alias('error'))
        choose(z.sort('delta','row_id'),baseline+' largest gain');choose(z.sort('delta','row_id',descending=[True,False]),baseline+' largest harm')
        choose(z.sort('error','row_id'),baseline+' false low');choose(z.sort('error','row_id',descending=[True,False]),baseline+' false high')
        choose(z.filter(pl.col('next_pa').is_between(200,399)).with_columns(pl.col('error').abs().alias('abs_error')).sort('abs_error','row_id'),baseline+' ordinary')
    peers={}
    for rid in sorted(set(diagnostic)):
        r=origin.filter(pl.col('row_id')==rid).row(0,named=True)
        pool=origin.filter((pl.col('origin_year')==r['origin_year'])&(pl.col('row_id')!=rid)&
            (pl.col('prior_debut')==r['prior_debut'])&(pl.col('stage')==r['stage'])&
            (pl.col('employment_category')==r['employment_category']))
        distance=(((pl.col('age')-r['age'])/5)**2+((pl.col('pa_0')-r['pa_0'])/250)**2+
            (pl.col('professional_work_0')-r['professional_work_0'])**2)
        p=pool.with_columns(distance.alias('distance')).sort('distance','player_id','row_id').head(3)
        peers[rid]=p.select('row_id','player_id','age','stage','employment_category','pa_0','professional_work_0','distance').to_dicts()
        for v in peers[rid]:selected.setdefault(v['row_id'],[]).append('origin-only peer of '+str(rid))
    # Freeze selection before walking, preserving losers and ordinary controls.
    save('case-selection.json',dict(selected={str(k):v for k,v in selected.items()},peers={str(k):v for k,v in peers.items()},
        peer_rule='Same origin, debut, stage and corrected employment; nearest age, prior PA and professional work, then IDs; no future result in distance'))
    oldrows={};newrows={}
    for k in range(5):
        ids=q.filter((pl.col('outer_fold')==k)&pl.col('row_id').is_in(list(selected)))['row_id'].to_list()
        for path,mapping in [(OLD/f'features-{k}.parquet',oldrows),(OUT/f'features-{k}.parquet',newrows)]:
            f=pl.read_parquet(path,columns=list(dict.fromkeys(['row_id',*pre['job_features'],*selector,'status_retired'])))
            mapping.update({r['row_id']:r for r in f.filter(pl.col('row_id').is_in(ids)).to_dicts()})
    delta={r['candidate_key']:r for r in read(FIX/'employment-deltas.json')['rows']}
    foreign={r['candidate_key']:r for r in read(GEN/'foreign-origin-inputs/origin-inputs.json')['rows']}
    support_rows=pl.read_parquet(OUT/'profile-support.parquet'); cases=[]
    with threadpool_limits(limits=2):
        for rid,why in sorted(selected.items()):
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);y,k=r['origin_year'],r['outer_fold'];key=f'{y}:{r["player_id"]}'
            a,b=oldrows[rid],newrows[rid];names=pre['job_features'];x=np.array([a[n] for n in names]);z=np.array([b[n] for n in names])
            mechanics={};probe={}
            for arm,v in [('old_job',x),('corrected_job',z)]:
                for head in ['participation','conditional_pa']:
                    m=models[arm,y,k,head]
                    t=logit_trace(m,v,names) if head=='participation' else trace(m,v,names)
                    value=t['linked_probability'] if head=='participation' else t['raw_prediction']
                    col=('repaired_domestic_' if arm=='old_job' else 'corrected_job_')+('raw_p' if head=='participation' else 'raw_conditional_pa')
                    assert np.isclose(value,r[col],atol=1e-8,rtol=0)
                    mechanics[arm+'_'+head]=t
                    if arm=='old_job': probe[head]=float(m.predict_proba(z[None,:])[0,1]) if head=='participation' else float(m.predict(z[None,:])[0])
            probe['expected_PA']=0. if a['status_hard_unavailable'] or a['status_retired'] else probe['participation']*float(np.clip(probe['conditional_pa'],1,800))
            cases.append(dict(origin=r,selection=why,source_employment_delta=delta.get(key),
                domestic_counts=stints.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket','team_id').to_dicts(),
                foreign_counts=foreign.get(key),actual_future_MLB_counts=actual.get((y+1,r['player_id']),np.zeros(8)).tolist(),
                old_model_inputs=a,corrected_model_inputs=b,input_changes={n:[a[n],b[n]] for n in names if a[n]!=b[n]},
                head_mechanics=mechanics,old_parameters_corrected_input_probe=probe,
                probe_is_not_replacement_or_causal=True,
                unchanged_talent_provenance='Saved current incumbent for original; saved repaired-domestic research fallback for addition. No talent refit.',
                actual_training_profiles=support_rows.filter(pl.col('row_id')==rid).to_dicts(),origin_only_peers=peers.get(rid,[])))
    save('player-walks.json',dict(cases=cases,player_walkthrough_status='machine_ready_manual_pending'))
    save('review-receipt.json',dict(corrected_heads_replayed=70,baseline_heads_replayed_before_fit=70,
        actual_labels_independently_reconstructed=True,case_count=len(cases),scores_provisional=True,
        player_walkthrough_status='pending',deployment_approved=False,protected_outcomes_read=False,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [Path(__file__),ANCHOR,
            OUT/'preflight.json',OUT/'fit-report.json',OUT/'predictions.parquet',OUT/'scores.json',
            OUT/'intervals.json',OUT/'case-selection.json',OUT/'player-walks.json']}))
    print(__import__('json').dumps(dict(scopes=scored[:3],cases=len(cases))),flush=True)


if __name__=='__main__':main()
