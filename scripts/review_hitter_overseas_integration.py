"""Replay saved forecasts, score fixed populations, and trace player mechanics."""
from pathlib import Path
import json

import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.hitter_compatible_value import UNIT, labels
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file
from evaluate_hitter_readiness_v49 import logit_trace
from prepare_hitter_overseas_integration import ROOT,OUT,ANCHOR,STATUS,ADDITIONS,FOREIGN,read,write,verify,annual_labels

ARMS=['current','domestic','overseas']


def origin_weights(g):
    years=g['origin_year'].to_numpy();n=len(g);u,c=np.unique(years,return_counts=True)
    return np.array([1/(len(u)*c[np.where(u==y)[0][0]]) for y in years])


def errors(g,arm):
    pa=g[arm+'_pa'].to_numpy();actual=g['next_pa'].to_numpy();value=g[arm+'_value'].to_numpy()
    prob=g[arm+'_p'].to_numpy();yes=(actual>0).astype(float);lp=np.clip(prob,1e-12,1-1e-12)
    return np.column_stack([(pa-actual)**2,abs(pa-actual),pa-actual,
        (value-g['actual_relative_value'].to_numpy())**2,abs(value-g['actual_relative_value'].to_numpy()),
        value-g['actual_relative_value'].to_numpy(),(prob-yes)**2,-yes*np.log(lp)-(1-yes)*np.log1p(-lp)])


def score(g,arm):
    z=origin_weights(g)@errors(g,arm)
    active=g.filter(pl.col('next_pa')>0)
    rate=origin_weights(active)@((active[arm+'_rate']-active['actual_relative_rate']).to_numpy()**2) if active.height else None
    return dict(pa_rmse=float(np.sqrt(z[0])),pa_mae=float(z[1]),pa_bias=float(z[2]),value_rmse=float(np.sqrt(z[3])),
        value_mae=float(z[4]),value_bias=float(z[5]),brier=float(z[6]),logloss=float(z[7]),
        conditional_rate_rmse=float(np.sqrt(rate)) if rate is not None else None,
        expected_pa=float(g[arm+'_pa'].sum()),expected_arrivals=float(g[arm+'_p'].sum()),expected_value=float(g[arm+'_value'].sum()))


def interval(g,candidate,baseline):
    delta=errors(g,candidate)-errors(g,baseline);w=origin_weights(g)
    people,pi=np.unique(g['player_id'].to_numpy(),return_inverse=True)
    total=np.zeros((len(people),delta.shape[1]));den=np.zeros(len(people))
    np.add.at(total,pi,delta*w[:,None]);np.add.at(den,pi,w)
    rng=np.random.default_rng(104);draws=[]
    for b in range(2000):
        counts=np.bincount(rng.integers(0,len(people),len(people)),minlength=len(people))
        z=counts@total/(counts@den);draws.append(z)
        if b<10:assert np.allclose(z,(delta*(w*counts[pi])[:,None]).sum(0)/(w*counts[pi]).sum(),atol=1e-8)
    draws=np.array(draws);point=w@delta
    return [dict(metric=n,change=float(point[i]),lower=float(np.quantile(draws[:,i],.025)),upper=float(np.quantile(draws[:,i],.975)),
        fixed_original_origin_weights=True,nominal_exposed_development_interval=True)
        for i,n in enumerate(['pa_mse','pa_mae','pa_bias','value_mse','value_mae','value_bias','brier','logloss'])]


def ridge_trace(model,x,names):
    scaler,reg=model.steps[0][1],model.steps[1][1]
    z=scaler.transform(x[None,:])[0];effects=z*reg.coef_;raw=float(reg.intercept_+effects.sum())
    assert np.isclose(raw,model.predict(x[None,:])[0],atol=1e-10,rtol=0)
    order=np.argsort(-abs(effects))
    return dict(intercept=float(reg.intercept_),raw_prediction=raw,
        foreign_feature_effect=float(sum(v for n,v in zip(names,effects) if n.startswith('foreign_'))),
        feature_effects=[dict(feature=names[i],input=float(x[i]),standardized_input=float(z[i]),coefficient=float(reg.coef_[i]),effect=float(effects[i])) for i in order[:20]],
        interpretation='Exact standardized ridge accounting, not causal attribution')


def main():
    assert not (OUT/'review-receipt.json').exists(),'Preserve completed review'
    pre=read(OUT/'preflight.json');verify(pre['source_hashes']);fit=read(OUT/'fit-report.json')
    assert sha256_file(OUT/'predictions.parquet')==fit['output_sha256']
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    stints=pl.read_parquet(ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    actual,env=annual_labels(stints)
    raw=np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.to_dicts()])
    lab=labels(raw,np.array([env[y] for y in q['origin_year']]),np.array([env[y] for y in q['target_year']]),q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'],q['next_pa']) and np.allclose(lab['relative_value'],q['actual_relative_value'],atol=1e-10)
    assert np.allclose(lab['relative_rate'],q['actual_relative_rate'],atol=1e-10)
    with threadpool_limits(limits=2):
        for cell in fit['cells']:
            y,k=cell['year'],cell['fold'];verify(cell['hashes'])
            f=pl.read_parquet(OUT/f'features-{y}-{k}.parquet')
            g=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k))
            test=f.filter(pl.col('row_id').is_in(g['row_id'].to_list())).sort('row_id')
            assert test['row_id'].equals(g['row_id'])
            for h in cell['heads']:
                model=joblib.load(h['path']);x=test.select(h['features']).to_numpy()
                replay=model.predict_proba(x)[:,1] if h['head']=='participation' else model.predict(x)
                suffix='raw_p' if h['head']=='participation' else 'raw_'+h['head']
                assert np.allclose(replay,g[h['arm']+'_'+suffix],atol=1e-10,rtol=0)
            for arm in ['domestic','overseas']:
                assert np.allclose(g[arm+'_pa'],g[arm+'_p']*g[arm+'_conditional_pa'],atol=1e-10)
                assert np.allclose(g[arm+'_value'],g[arm+'_pa']*(g[arm+'_rate']/600+g['origin_replacement_rate']),atol=1e-10)
            print(f'Replayed all six heads and complete value products: {y}/{k}',flush=True)
    anchor=pl.read_parquet(ANCHOR).select('row_id','steamer_pa','steamer_rate','steamer_index','zips_index','common_zips_rate',
        'origin_index','pooled_mlb_quality','AAA_0_pa','AA_0_pa','minor_pa_0','scout_rank_score_0')
    q=q.join(anchor,on='row_id',how='left',validate='1:1')
    original=q.filter(~pl.col('source_addition'));added=q.filter(pl.col('source_addition'))
    public=original.filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null());assert public.height==2627
    scopes=[('original_all',original),('additions',added),('public',public),('original_foreign',original.filter(pl.col('row_id').is_in(pl.read_parquet(OUT/'features.parquet').filter(pl.col('ctx_foreign_history_known'))['row_id'].to_list()))),
        ('original_current_MLB',original.filter(pl.col('pa_0')>0)),('original_upper_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('original_lower_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('original_no_arrival',original.filter(pl.col('next_pa')==0))]
    scopes += [('origin_'+str(y),original.filter(pl.col('origin_year')==y)) for y in sorted(original['origin_year'].unique())]
    scores=[];intervals=[]
    for name,g in scopes:
        if not g.height:continue
        arms=ARMS if name!='additions' else ARMS[1:]
        mechanical={}
        for arm in ['domestic','overseas']:
            if name=='additions':continue
            for head in ['workload_only','talent_only']:
                err=(g[arm+'_'+head+'_value']-g['actual_relative_value']).to_numpy()
                mechanical[arm+'_'+head]=dict(value_rmse=float(np.sqrt(origin_weights(g)@(err**2))),value_bias=float(origin_weights(g)@err))
        scores.append(dict(scope=name,rows=g.height,players=g['player_id'].n_unique(),actual_pa=int(g['next_pa'].sum()),actual_arrivals=int((g['next_pa']>0).sum()),
            actual_value=float(g['actual_relative_value'].sum()),scores={arm:score(g,arm) for arm in arms},mechanical_diagnostics=mechanical))
        if name in ['original_all','public','original_foreign','additions']:
            comparisons=[('overseas','domestic')]+([] if name=='additions' else [('overseas','current'),('domestic','current')])
            with threadpool_limits(limits=2):
                for a,b in comparisons:intervals.append(dict(scope=name,candidate=a,baseline=b,intervals=interval(g,a,b)))
    err=(public['steamer_pa']-public['next_pa']).to_numpy();w=origin_weights(public)
    public_value=public['steamer_pa']*(public['steamer_rate']/600+public['origin_replacement_rate'])
    public_error=(public_value-public['actual_relative_value']).to_numpy()
    benchmark=dict(rows=public.height,pa_rmse=float(np.sqrt(w@(err**2))),pa_mae=float(w@abs(err)),
        value_rmse=float(np.sqrt(w@(public_error**2))),qualification='Public rate/value environment and snapshot differences prevent talent-superiority claims; fixed matched MLB sample')
    write('scores.json',dict(scopes=scores,public_steamer=benchmark));write('intervals.json',dict(comparisons=intervals))
    chosen={}
    def choose(g,why):
        if g.height:chosen.setdefault(int(g['row_id'][0]),[]).append(why)
    fixed=[(808975,2024),(808982,2024),(673490,2022),(519346,2016),(592450,2024),(701762,2024),(680757,2021),(691406,2024)]
    for r in read(STATUS/'reviewed-cases.json').get('cases',[]):
        pid=r.get('player_id');y=r.get('origin_year')
        if pid is not None and y is not None:fixed.append((pid,y))
    for r in read(ADDITIONS/'origin-inputs.json')['rows']:
        if r['qualified_for_batting_input']:fixed.append((r['player_id'],r['origin_year']))
    for pid,y in fixed:choose(q.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed or admission diagnostic')
    for arm in ['domestic','overseas']:
        z=original.with_columns(((pl.col(arm+'_value')-pl.col('actual_relative_value'))**2-(pl.col('current_value')-pl.col('actual_relative_value'))**2).alias('change'),
            (pl.col(arm+'_value')-pl.col('actual_relative_value')).alias('error'))
        choose(z.sort('change'),arm+' largest gain');choose(z.sort('change',descending=True),arm+' largest harm')
        choose(z.sort('error'),arm+' false low');choose(z.sort('error',descending=True),arm+' false high')
        choose(z.filter(pl.col('next_pa').is_between(200,399)).sort(pl.col('error').abs()),arm+' ordinary')
    status={r['candidate_key']:r for r in read(STATUS/'status-ledger.json')['rows']}
    foreign={r['candidate_key']:r for r in read(FOREIGN/'origin-inputs.json')['rows']}
    support=pl.read_parquet(OUT/'profile-support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,why in chosen.items():
            o=q.filter(pl.col('row_id')==rid).row(0,named=True);y,k=o['origin_year'],o['outer_fold'];key=f'{y}:{o["player_id"]}'
            cell=next(c for c in fit['cells'] if c['year']==y and c['fold']==k)
            f=pl.read_parquet(OUT/f'features-{y}-{k}.parquet');one=f.filter(pl.col('row_id')==rid)
            a=one.row(0,named=True);mechanics={};probes={}
            for h in cell['heads']:
                m=joblib.load(h['path']);x=one.select(h['features']).to_numpy()[0]
                mechanics[h['arm']+'_'+h['head']]=logit_trace(m,x,h['features']) if h['head']=='participation' else trace(m,x,h['features']) if h['head']=='conditional_pa' else ridge_trace(m,x,h['features'])
                if h['head']!='rate':
                    mechanics[h['arm']+'_'+h['head']]['foreign_splits_in_entire_model']=sum(
                        h['features'][int(v)].startswith('foreign_') for ts in m._predictors
                        for v in ts[0].nodes['feature_idx'][~ts[0].nodes['is_leaf'].astype(bool)])
                if h['arm']=='overseas':
                    probe=x.copy()
                    for j,n in enumerate(h['features']):
                        if n.startswith('foreign_'):probe[j]=0.
                    probes[h['head']]=float(m.predict_proba(probe[None,:])[0,1] if h['head']=='participation' else m.predict(probe[None,:])[0])
            pool=f.filter((pl.col('row_id')!=rid)&(pl.col('row_id').is_in(q.filter(pl.col('origin_year')==y)['row_id'].to_list()))&
                (pl.col('prior_debut')==a['prior_debut'])&(pl.col('status_major_link')==a['status_major_link'])&(pl.col('on_40man')==a['on_40man']))
            distance=(((pl.col('age')-a['age'])/5)**2+((pl.col('pa_0')-a['pa_0'])/250)**2+
                ((pl.col('foreign_recent_pa')-a['foreign_recent_pa'])/2)**2+
                ((pl.col('scout_rank_score_0')-a['scout_rank_score_0'])/.3)**2)
            peer=pool.with_columns(distance.alias('origin_distance')).sort('origin_distance','player_id').head(3).select('row_id','player_id','player_name','age','on_40man','status_major_link','pa_0','foreign_recent_pa','origin_distance')
            peer=peer.join(q.select('row_id','next_pa','actual_relative_value','overseas_p','overseas_pa','overseas_rate','overseas_value'),on='row_id',validate='1:1')
            cases.append(dict(origin=o,selection=why,dated_status=status[key],foreign_history=foreign.get(key),
                domestic_history=stints.filter((pl.col('player_id')==o['player_id'])&(pl.col('season')<=y)).sort('season','bucket','team_id').to_dicts(),
                actual_future_MLB_counts=actual.get((y+1,o['player_id']),np.zeros(8)).tolist(),actual_model_inputs=a,
                mechanics=mechanics,foreign_zero_input_probe=probes,
                borrowed_foreign_rate_input=float(np.array([a['foreign_translated_'+e] for e in __import__('universal_baseball.mlb_event_logit',fromlist=['EVENTS']).EVENTS])@VALUES*UNIT),
                borrowed_foreign_rate_qualification='Saved translated probability minus its own known MLB reference, not a new joint forecast; absent/missing translation is masked, not zero talent',
                probe_qualification='Same-fit zero-input mechanics, not a causal effect or validated alternative; jobs and domestic evidence retained, profile may be artificial',
                profile_support=support.filter(pl.col('row_id')==rid).to_dicts(),origin_only_peers=peer.to_dicts()))
            print(f'Player trace ready: {o["player_name"]} {y}.',flush=True)
    write('reviewed-cases.json',dict(cases=cases,player_walkthrough_status='machine_ready_manual_pending',
        peer_rule='Same origin, debut, dated major-link and literal listing; nearest age, MLB/foreign exposure and prospect rank; no future results'))
    write('review-receipt.json',dict(saved_heads_replayed=210,labels_independently_reconstructed=True,
        scores_provisional=True,case_count=len(cases),player_walkthrough_status='pending',deployment_approved=False,
        input_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [Path(__file__),OUT/'preflight.json',OUT/'fit-report.json',OUT/'predictions.parquet']},
        output_hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'scores.json',OUT/'intervals.json',OUT/'reviewed-cases.json']}))
    print(json.dumps(scores[:3],indent=2),flush=True)


if __name__=='__main__':main()
