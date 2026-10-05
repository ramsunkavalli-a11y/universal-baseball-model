"""Independent replay, arithmetic scores and required source/model player walks."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.hitter_count_baseline import past_profile,assemble,probabilities
from universal_baseball.mlb_event_logit import batting_rate
from universal_baseball.storage import sha256_file
from run_hitter_count_baseline import ROOT,GEN,OUT,SHARED,FIXED,FEATURES,EVENTS,REF,TARGET,read,save,verify,source_data,matrix,offset,tagged
from prepare_hitter_overseas_integration import annual_labels
from review_hitter_overseas_integration import origin_weights
from review_hitter_evidence_representation import rate_interval
from supplement_hitter_overseas_scores import rate_score


def summary(g,arm):
    w=origin_weights(g);e=(g[arm+'_value']-g['actual_relative_value']).to_numpy();active=g.filter(pl.col('next_pa')>0)
    return dict(value_rmse=float(np.sqrt(w@(e*e))),value_mae=float(w@abs(e)),value_bias=float(w@e),
        expected_value=float(g[arm+'_value'].sum()),expected_PA=float(g[arm+'_pa'].sum()),
        rate_rmse=rate_score(active,arm+'_rate','actual_relative_rate',True) if active.height else None)


def value_interval(g):
    w=origin_weights(g);a=g['actual_relative_value'].to_numpy()
    delta=(g['count_value'].to_numpy()-a)**2-(g['current_value'].to_numpy()-a)**2
    pid,ix=np.unique(g['player_id'].to_numpy(),return_inverse=True);n=len(pid);total=np.zeros(n);den=np.zeros(n)
    np.add.at(total,ix,w*delta);np.add.at(den,ix,w);rng=np.random.default_rng(84);draw=[]
    for _ in range(2000):
        c=np.bincount(rng.integers(n,size=n),minlength=n);draw.append(float(c@total/(c@den)))
    return dict(metric='delivered_value_mse',change=float(w@delta),lower=float(np.quantile(draw,.025)),upper=float(np.quantile(draw,.975)),nominal_development_interval=True)


def event_score(g, column=None):
    if not g.height:return None
    p=g.select([f'count_probability_{e}' for e in EVENTS]).to_numpy() if column is None else np.asarray(g[column].to_list())
    c=g.select(TARGET).to_numpy();w=np.zeros(g.height);years=g['origin_year'].to_numpy();pa=g['next_pa'].to_numpy()
    for y in np.unique(years):
        mask=years==y;w[mask]=pa[mask]/pa[mask].sum()/len(np.unique(years))
    observed=c/c.sum(1,keepdims=True)
    return dict(log_loss=float(w@(-np.sum(observed*np.log(p),1))),
        brier=float(w@(np.sum(p*p,1)-2*np.sum(observed*p,1)+1)),
        frequencies={e:dict(predicted=float(w@p[:,i]),actual=float(w@observed[:,i])) for i,e in enumerate(EVENTS)},
        interpretation='Conditional event calibration using actual target PA weights; not forecast playing time')


def main():
    assert not (OUT/'review-receipt.json').exists()
    pre=read(OUT/'preflight.json');verify(pre['source_hashes']);fit=read(OUT/'fit-report.json')
    assert sha256_file(OUT/'predictions.parquet')==fit['predictions_sha256']
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    actual,env=annual_labels(pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet'))
    raw=np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.iter_rows(named=True)])
    lab=labels(raw,np.array([env[y] for y in q['origin_year']]),np.array([env[y] for y in q['target_year']]),q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'],q['next_pa']) and np.allclose(lab['relative_rate'],q['actual_relative_rate'],atol=1e-10)
    assert np.allclose(lab['relative_value'],q['actual_relative_value'],atol=1e-10)
    q=q.with_columns(pl.Series('actual_common_rate',lab['common_rate']),*[pl.Series(n,raw[:,i]) for i,n in enumerate(TARGET)])
    anchor=pl.read_parquet(GEN/'hitter-minor-statcast-precision/scored-predictions.parquet').select('row_id','steamer_rate','steamer_index','common_zips_rate','zips_index')
    shared=pl.read_parquet(SHARED/'predictions.parquet').select('row_id','shared_rate','shared_value','shared_pa')
    direct=pl.read_parquet(GEN/'hitter-direct-events/predictions.parquet').select('row_id','direct_foreign_rate','direct_foreign_value','direct_foreign_pa','direct_foreign_probability','direct_foreign_supported')
    q=q.join(anchor,on='row_id',how='left',validate='1:1').join(shared,on='row_id',validate='1:1').join(direct,on='row_id',validate='1:1')
    frames={k:pl.read_parquet(OUT/f'features-{k}.parquet') for k in range(5)};models={};replays=0
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y,k=c['origin'],c['fold'];verify(c['hashes']);g=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)).sort('row_id')
            f=frames[k].filter(pl.col('row_id').is_in(g['row_id'])).sort('row_id');ps={}
            assert np.array_equal(f.select(TARGET).to_numpy(),g.select(TARGET).to_numpy())
            for h in c['heads']:
                m=joblib.load(h['path']);assert m['optimizer']['success'];models[y,k,h['arm']]=(m,h['features'])
                ps[h['arm']]=probabilities(m['beta'],matrix(f,h['features']),offset(f));replays+=1
            p=np.where((f['prior_debut'].to_numpy()==0)[:,None],ps['prospect'],np.where(f['sc_tracked'].to_numpy()[:,None],ps['tracking'],ps['base']))
            assert np.allclose(p,g.select([f'count_probability_{e}' for e in EVENTS]),atol=1e-12,rtol=0)
            assert np.allclose(batting_rate(p,f.select(REF).to_numpy()),g['count_rate'],atol=1e-10,rtol=0)
            assert np.allclose(g['count_value'],g['count_pa']*(g['count_rate']/600+g['origin_replacement_rate']),atol=1e-10,rtol=0)
    original=q.filter(~pl.col('source_addition'));added=q.filter(pl.col('source_addition'))
    assert original.height==30506 and added.height==13 and original['count_pa'].equals(original['current_pa'])
    public=original.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert public.height==2627
    ids=frames[0].filter(pl.col('evidence_foreign_source_present')>0)['row_id']
    scopes=[('all',original),('public',public),('foreign',original.filter(pl.col('row_id').is_in(ids))),
        ('current_MLB',original.filter(pl.col('pa_0')>0)),
        ('upper_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('no_arrival',original.filter(pl.col('next_pa')==0)),('additions',added)]
    scopes += [('origin_'+str(y),original.filter(pl.col('origin_year')==y)) for y in sorted(original['origin_year'].unique())]
    scores=[];triggers=[]
    for name,g in scopes:
        arms=['count','repaired_overseas','shared','direct_foreign'] if name=='additions' else ['current','count','shared','repaired_overseas','direct_foreign']
        s=dict(scope=name,rows=g.height,players=g['player_id'].n_unique(),actual_PA=int(g['next_pa'].sum()),actual_value=float(g['actual_relative_value'].sum()),
            scores={a:summary(g,a) for a in arms},count_events=event_score(g.filter(pl.col('next_pa')>0)))
        h=g.filter((pl.col('next_pa')>0)&pl.col('direct_foreign_supported'))
        s['matched_supported_events']=dict(rows=h.height,count=event_score(h),old_future_direct=event_score(h,'direct_foreign_probability'),
            qualification='Old future profile evaluated for all supported rows; old value branch kept established MLB Ridge. Profile and value comparisons have different routing.')
        scores.append(s)
        if name!='additions' and s['scores']['current']['rate_rmse'] is not None and s['scores']['count']['rate_rmse']>1.05*s['scores']['current']['rate_rmse']:
            triggers.append(name+' hitting worsens >5%')
    active=public.filter(pl.col('next_pa')>0)
    pub=dict(rows=public.height,active_rows=active.height,common_rate_rmse={a:rate_score(active,col,'actual_common_rate',True)
        for a,col in [('current','current_rate'),('count','count_rate'),('shared','shared_rate'),('steamer','steamer_rate'),('zips','common_zips_rate')]},
        qualification='Archived public rate forecasts; release, park and future league environment differ. No certified ZiPS workload comparison.')
    save('scores.json',dict(scopes=scores,intervals=dict(rate=rate_interval(original,'count','current'),value=value_interval(original)),
        public=pub,review_triggers=triggers,player_walkthrough_status='pending'))
    chosen={}
    for name,y in FIXED:
        g=q.filter((pl.col('player_name')==name)&(pl.col('origin_year')==y));assert g.height==1
        chosen[int(g['row_id'][0])]=['fixed before fitting']
    z=original.with_columns(((pl.col('count_value')-pl.col('actual_relative_value'))**2-(pl.col('current_value')-pl.col('actual_relative_value'))**2).alias('change'),
        (pl.col('count_value')-pl.col('actual_relative_value')).alias('error'))
    for part,why in [(z.sort('change'),'largest gain'),(z.sort('change',descending=True),'largest harm'),(z.sort('error'),'false low'),
        (z.sort('error',descending=True),'false high'),(z.filter(pl.col('next_pa').is_between(200,399)).sort(pl.col('error').abs()),'ordinary')]:
        chosen.setdefault(int(part['row_id'][0]),[]).append(why)
    _,history,sources,foreign=source_data();support=pl.read_parquet(OUT/'profile-support.parquet');ranges=read(OUT/'feature-ranges.json');cases=[];checks=0
    with threadpool_limits(limits=2):
        for rid,why in chosen.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True);y,k,pid=o['origin_year'],o['outer_fold'],o['player_id']
            f=frames[k];one=f.filter(pl.col('row_id')==rid);a=one.row(0,named=True);key=f'{y}:{pid}'
            graph=read(SHARED/f'graphs-{k}.json')[f'{y}:{k}']
            values,note=past_profile(history[pid],graph,sources.get(key),foreign.get((key,k)),origin=y,outer_fold=k,own_fold=k)
            for nm,v in values.items():assert np.isclose(v,a[nm],atol=1e-12);checks+=1
            m,names=models[y,k,o['count_branch']];x=matrix(one,names)[0];terms=x[:,None]*m['beta'][1:];correction=m['beta'][0]+terms.sum(0)
            p=probabilities(m['beta'],matrix(one,names),offset(one))[0]
            assert np.isclose(batting_rate(p[None,:],np.array([note['reference']]))[0],o['count_rate'],atol=1e-10)
            probes={}
            for family in ['minor','foreign']:
                vv,pp=assemble(note['contributions'],note['reference'],note['observed_precision_PA'],remove=family)
                changed=one.with_columns([pl.lit(v).alias(nm) for nm,v in vv.items()]);out=probabilities(m['beta'],matrix(changed,names),offset(changed))
                rate=float(batting_rate(out,changed.select(REF).to_numpy())[0]);probes[family]=dict(rate=rate,change=rate-o['count_rate'],past_probability=pp.tolist(),
                    interpretation='Fixed fitted model; remove source mass and recompute derived inputs, retain coverage denominator. Artificial, not causal.')
            c=next(c for c in pre['cells'] if c['year']==y and c['fold']==k);tr=tagged(f.filter(pl.col('row_id').is_in(c['training_row_ids'])))
            peers=tr.filter((pl.col('prior_debut')==a['prior_debut'])&(pl.col('stage')==a['stage']))
            foreign_present=a['count_NPB_share']+a['count_KBO_share']>0
            if foreign_present:
                peers=peers.filter((pl.col('has_NPB')==(a['count_NPB_share']>0))&(pl.col('has_KBO')==(a['count_KBO_share']>0)))
            peers=peers.with_columns(((pl.col('age')-a['age']).abs()/5+(pl.col('pa_0')-a['pa_0']).abs()/600+
                (pl.col('draft_rank')-a['draft_rank']).abs()+(pl.col('scout_rank_score_0')-a['scout_rank_score_0']).abs()).alias('origin_distance')).sort('origin_distance','player_id','origin_year').unique('player_id',maintain_order=True).head(3)
            peercols=['row_id','player_id','player_name','origin_year','age','pa_0','minor_pa_0','draft_rank','scout_rank_score_0','origin_distance','next_pa','actual_relative_rate']
            cases.append(dict(row_id=rid,why=why,forecast=o,information_date=a['ctx_information_date'],age=a['age'],branch=o['count_branch'],
                source=note,raw_history=[r for r in history[pid] if y-2<=r['season']<=y],
                past_baseline_rate=float(batting_rate(np.array([note['past_probability']]),np.array([note['reference']]))[0]),
                fitted_event_logit_correction=correction.tolist(),logit_intercept=m['beta'][0].tolist(),
                feature_logit_terms=[dict(feature=nm,input=float(xx),effects=vv.tolist()) for nm,xx,vv in zip(names,x,terms,strict=True)],
                predicted_probability=p.tolist(),actual_counts=o and [o[nm] for nm in TARGET],probes=probes,
                support=support.filter((pl.col('row_id')==rid)&(pl.col('arm')==o['count_branch'])).to_dicts(),
                feature_extrapolations=[r for r in ranges if r['origin']==y and r['fold']==k and r['arm']==o['count_branch'] and rid in r['row_ids']],
                origin_selected_training_comparisons=peers.select(peercols).to_dicts(),
                peer_qualification='Origin-known distance, distinct training people, same debut/stage and foreign league presence where relevant. Future outcomes not used in selection; not independent forecast validation.'))
    save('player-walks.json',dict(cases=cases,selection='Ten fixed cases plus largest gain/harm, false high/low and ordinary; preserve all',walkthrough_status='pending_readable_review'))
    save('review-receipt.json',dict(heads_replayed=replays,source_feature_checks=checks,labels_independently_reconstructed=True,PA_exactly_fixed=True,
        player_walkthrough_status='pending_readable_review',protected_outcomes_used=False,deployment_approved=False,
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'scores.json',OUT/'player-walks.json',OUT/'fit-report.json',
            GEN/'practical-hitter-v31/dated-stints.parquet',GEN/'hitter-minor-statcast-precision/scored-predictions.parquet',GEN/'hitter-direct-events/predictions.parquet']}))
    print('All 105 heads, event probabilities, labels and value products replayed; read player walks before disposition.',flush=True)


if __name__=='__main__':main()
