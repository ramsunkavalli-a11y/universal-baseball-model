"""Independently reconstruct labels, replay fixed talent and walk actual evidence."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_compatible_value import labels
from universal_baseball.hitter_shared_production import FEATURES, assemble, profile
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from run_hitter_shared_production import ROOT,GEN,OUT,OLD,FIXED_NAMES,read,save,verify,source_data,tagged
from prepare_hitter_overseas_integration import annual_labels
from prepare_practical_hitter_v33 import safe_matrix
from review_hitter_overseas_integration import origin_weights
from review_hitter_evidence_representation import linear_trace, rate_interval
from supplement_hitter_overseas_scores import rate_score


def summary(g,arm):
    w=origin_weights(g);e=(g[arm+'_value']-g['actual_relative_value']).to_numpy()
    active=g.filter(pl.col('next_pa')>0)
    return dict(value_rmse=float(np.sqrt(w@(e*e))),value_mae=float(w@abs(e)),value_bias=float(w@e),
        expected_value=float(g[arm+'_value'].sum()),expected_PA=float(g[arm+'_pa'].sum()),
        rate_rmse=rate_score(active,arm+'_rate','actual_relative_rate',True) if active.height else None)


def value_interval(g):
    w=origin_weights(g);a=g['actual_relative_value'].to_numpy()
    delta=(g['shared_value'].to_numpy()-a)**2-(g['current_value'].to_numpy()-a)**2
    pid,ix=np.unique(g['player_id'].to_numpy(),return_inverse=True);n=len(pid);total=np.zeros(n);den=np.zeros(n)
    np.add.at(total,ix,w*delta);np.add.at(den,ix,w);rng=np.random.default_rng(84);draw=[]
    for _ in range(2000):
        c=np.bincount(rng.integers(n,size=n),minlength=n);draw.append(float(c@total/(c@den)))
    return dict(metric='delivered_value_mse',change=float(w@delta),lower=float(np.quantile(draw,.025)),upper=float(np.quantile(draw,.975)),nominal_development_interval=True)


def main():
    assert not (OUT/'review-receipt.json').exists(),'Preserve a completed review'
    pre=read(OUT/'preflight.json');verify(pre['source_hashes']);fit=read(OUT/'fit-report.json')
    assert sha256_file(OUT/'predictions.parquet')==fit['predictions_sha256']
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    actual,env=annual_labels(pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet'))
    raw=np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.iter_rows(named=True)])
    lab=labels(raw,np.array([env[y] for y in q['origin_year']]),np.array([env[y] for y in q['target_year']]),q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'],q['next_pa'])
    assert np.allclose(lab['relative_rate'],q['actual_relative_rate'],atol=1e-10)
    assert np.allclose(lab['relative_value'],q['actual_relative_value'],atol=1e-10)
    q=q.with_columns(pl.Series('actual_common_rate',lab['common_rate']))
    anchor=pl.read_parquet(GEN/'hitter-minor-statcast-precision/scored-predictions.parquet').select('row_id','steamer_rate','steamer_index','common_zips_rate','zips_index')
    q=q.join(anchor,on='row_id',how='left',validate='1:1');fmap={k:pl.read_parquet(OUT/f'features-{k}.parquet') for k in range(5)}
    models={};replays=0;directions=[]
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            y,k=c['origin'],c['fold'];verify(c['hashes']);g=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)).sort('row_id')
            f=fmap[k].filter(pl.col('row_id').is_in(g['row_id'])).sort('row_id');pred={}
            for h in c['heads']:
                m=joblib.load(h['path']);models[y,k,h['arm']]=(m,h['features']);pred[h['arm']]=m.predict(safe_matrix(f,h['features']));replays+=1
                names=h['features'];other=m.coef_[names.index('shared_event_other')]
                directions.append(dict(origin=y,fold=k,arm=h['arm'],
                    HR_replaces_other=float(m.coef_[names.index('shared_event_HR')]-other),
                    K_replaces_other=float(m.coef_[names.index('shared_event_K')]-other),
                    interpretation='Fixed other inputs; coherent shared-profile contrast, not a causal intervention'))
            routed=np.where(f['prior_debut'].to_numpy()==0,pred['prospect'],np.where(f['sc_tracked'].to_numpy(),pred['tracking'],pred['base']))
            assert np.allclose(routed,g['shared_rate'],atol=1e-10,rtol=0)
            assert np.allclose(g['shared_value'],g['shared_pa']*(g['shared_rate']/600+g['origin_replacement_rate']),atol=1e-10,rtol=0)
    original=q.filter(~pl.col('source_addition'));added=q.filter(pl.col('source_addition'))
    assert original.height==30506 and added.height==13 and original['shared_pa'].equals(original['current_pa'])
    public=original.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert public.height==2627
    foreign_ids=fmap[0].filter(pl.col('evidence_foreign_source_present')>0)['row_id']
    scopes=[('all',original),('public',public),('foreign',original.filter(pl.col('row_id').is_in(foreign_ids))),
        ('current_MLB',original.filter(pl.col('pa_0')>0)),
        ('upper_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('no_arrival',original.filter(pl.col('next_pa')==0)),('additions',added)]
    scopes += [('origin_'+str(y),original.filter(pl.col('origin_year')==y)) for y in sorted(original['origin_year'].unique())]
    scores=[];triggers=[]
    for name,g in scopes:
        arms=['shared','repaired_overseas'] if name=='additions' else ['current','shared','repaired_overseas']
        s=dict(scope=name,rows=g.height,players=g['player_id'].n_unique(),actual_PA=int(g['next_pa'].sum()),actual_value=float(g['actual_relative_value'].sum()),scores={a:summary(g,a) for a in arms})
        scores.append(s)
        if name!='additions' and s['scores']['current']['rate_rmse'] is not None:
            if s['scores']['shared']['rate_rmse']>1.05*s['scores']['current']['rate_rmse']:triggers.append(name+' hitting RMSE worsens >5%')
    intervals=dict(rate=rate_interval(original,'shared','current'),value=value_interval(original))
    active=public.filter(pl.col('next_pa')>0)
    pub=dict(rows=public.height,active_rows=active.height,common_rate_rmse={a:rate_score(active,col,'actual_common_rate',True)
        for a,col in [('current','current_rate'),('shared','shared_rate'),('steamer','steamer_rate'),('zips','common_zips_rate')]},
        qualification='Archived public rate forecasts; vintage, park and future league environment differ. No certified ZiPS workload comparison.')
    bad=[r for r in directions if r['HR_replaces_other']<=0 or r['K_replaces_other']>=0]
    if bad:triggers.append('Shared event direction warnings in '+str(len(bad))+' heads')
    save('event-directions.json',dict(heads=directions,warnings=bad))
    save('scores.json',dict(scopes=scores,intervals=intervals,public=pub,review_triggers=triggers,player_walkthrough_status='pending'))
    chosen={}
    for name,y in FIXED_NAMES:
        z=q.filter((pl.col('player_name')==name)&(pl.col('origin_year')==y))
        assert z.height==1,(name,y)
        chosen[int(z['row_id'][0])]=['fixed before fitting']
    z=original.with_columns(((pl.col('shared_value')-pl.col('actual_relative_value'))**2-(pl.col('current_value')-pl.col('actual_relative_value'))**2).alias('change'),
        (pl.col('shared_value')-pl.col('actual_relative_value')).alias('error'))
    for part,why in [(z.sort('change'),'largest gain'),(z.sort('change',descending=True),'largest harm'),
        (z.sort('error'),'false low'),(z.sort('error',descending=True),'false high'),
        (z.filter(pl.col('next_pa').is_between(200,399)).sort(pl.col('error').abs()),'ordinary')]:
        chosen.setdefault(int(part['row_id'][0]),[]).append(why)
    _,history,sources,foreign=source_data();support=pl.read_parquet(OUT/'profile-support.parquet');cases=[];source_checks=0
    with threadpool_limits(limits=2):
        for rid,why in chosen.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True);y,k,pid=o['origin_year'],o['outer_fold'],o['player_id']
            f=fmap[k];one=f.filter(pl.col('row_id')==rid);a=one.row(0,named=True);key=f'{y}:{pid}'
            graph=read(OUT/f'graphs-{k}.json')[f'{y}:{k}']
            values,note=profile(history[pid],graph,sources.get(key),foreign.get((key,k)),origin=y,outer_fold=k,own_fold=k)
            for n,v in values.items():assert np.isclose(v,a[n],atol=1e-12);source_checks+=1
            arm=o['shared_branch'];m,names=models[y,k,arm];x=safe_matrix(one,names)[0];trace=linear_trace(m,x,names)
            assert np.isclose(trace['prediction'],o['shared_rate'],atol=1e-10)
            probes={}
            for family in ['minor','foreign']:
                vv=assemble(note['contributions'],note['reference'],note['observed_precision_PA'],remove=family)
                changed=one.with_columns([pl.lit(v).alias(n) for n,v in vv.items()])
                probes[family]=dict(prediction=float(m.predict(safe_matrix(changed,names))[0]),
                    change=float(m.predict(safe_matrix(changed,names))[0]-o['shared_rate']),
                    held_model=True,interpretation='Remove supported source mass, retain observed source-coverage denominator; artificial diagnostic, not causal')
            c=next(c for c in pre['cells'] if c['year']==y and c['fold']==k)
            tr=tagged(f.filter(pl.col('row_id').is_in(c['training_row_ids'])))
            people=tr.filter((pl.col('prior_debut')==a['prior_debut'])&(pl.col('stage')==a['stage']))
            people=people.with_columns(((pl.col('age')-a['age']).abs()/5+
                (pl.col('pa_0')-a['pa_0']).abs()/600+
                (pl.col('draft_rank')-a['draft_rank']).abs()+
                (pl.col('scout_rank_score_0')-a['scout_rank_score_0']).abs()).alias('origin_distance')).sort('origin_distance','player_id','origin_year').unique('player_id',maintain_order=True).head(3)
            peercols=['row_id','player_id','player_name','origin_year','age','pa_0','minor_pa_0','draft_rank','scout_rank_score_0','origin_distance','next_pa','actual_relative_rate']
            cases.append(dict(row_id=rid,why=why,forecast=o,information_date=a['ctx_information_date'],age=a['age'],
                branch=arm,source=note,source_features=values,raw_history=[r for r in history[pid] if y-2<=r['season']<=y],
                linear_trace=trace,probes=probes,support=support.filter((pl.col('row_id')==rid)&(pl.col('arm')==arm)).to_dicts(),
                origin_selected_training_comparisons=people.select(peercols).to_dicts(),
                peer_qualification='Origin-known distance, distinct training people; outcomes shown after selection. Training analogues are not independent forecasts.'))
    save('player-walks.json',dict(cases=cases,selection='Fixed seven plus largest gain/harm, false high/low and ordinary; no removal of inconvenient cases',walkthrough_status='pending_readable_review'))
    save('review-receipt.json',dict(heads_replayed=replays,source_feature_checks=source_checks,
        labels_independently_reconstructed=True,PA_exactly_fixed=True,player_walkthrough_status='pending_readable_review',
        protected_outcomes_used=False,deployment_approved=False,hashes={str(p):sha256_file(p) for p in [
            __import__('pathlib').Path(__file__),OUT/'scores.json',OUT/'player-walks.json',OUT/'fit-report.json',OUT/'event-directions.json',
            GEN/'practical-hitter-v31/dated-stints.parquet',GEN/'hitter-minor-statcast-precision/scored-predictions.parquet']}))
    print('105 talent heads replayed; scores and player source/coefficient walks saved for manual review.',flush=True)


if __name__=='__main__':main()
