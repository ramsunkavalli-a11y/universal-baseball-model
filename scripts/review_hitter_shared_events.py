"""Independent replay, source-label reconstruction and concrete fit accounting."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_compatible_value import labels
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_shared_events import PROFILE
from prepare_practical_hitter_v33 import safe_matrix
from prepare_hitter_overseas_integration import ANCHOR,annual_labels
from review_hitter_overseas_integration import score
from review_hitter_evidence_representation import interval,rate_interval,linear_trace
from supplement_hitter_overseas_scores import rate_score
from prepare_hitter_shared_events import OUT,GEN,PREVIOUS,read,save,verify

ARMS=['shared_domestic','shared_foreign']


def main():
    assert not (OUT/'review-receipt.json').exists(),'Preserve completed review'
    pre=read(OUT/'preflight.json');verify(pre['input_hashes']);fit=read(OUT/'fit-report.json')
    assert sha256_file(OUT/'predictions.parquet')==fit['predictions_sha256']
    q=pl.read_parquet(OUT/'predictions.parquet').sort('row_id')
    previous=pl.read_parquet(PREVIOUS/'predictions.parquet').sort('row_id')
    assert q.select(previous.columns).equals(previous)
    source_cases={c['row_id']:c for c in read(OUT/'source-cases.json')['cases']}
    frames={(a,k):pl.read_parquet(OUT/f'{a}-features-{k}.parquet') for a in pre['arms'] for k in range(5)}
    stints=pl.read_parquet(GEN/'practical-hitter-v31/dated-stints.parquet')
    assert stints['season'].max()<=2025
    actual,env=annual_labels(stints)
    raw=np.array([actual.get((r['target_year'],r['player_id']),np.zeros(8)) for r in q.to_dicts()])
    lab=labels(raw,np.array([env[y] for y in q['origin_year']]),np.array([env[y] for y in q['target_year']]),q['origin_replacement_rate'].to_numpy())
    assert np.array_equal(lab['pa'],q['next_pa'])
    assert np.allclose(lab['relative_rate'],q['actual_relative_rate'],atol=1e-10)
    assert np.allclose(lab['relative_value'],q['actual_relative_value'],atol=1e-10)
    q=q.with_columns(pl.Series('actual_common_rate',lab['common_rate']))
    origin_peer_inputs=frames['foreign',0].select('row_id','minor_pa_0','scout_rank_score_0')
    q=q.join(origin_peer_inputs,on='row_id',how='left',validate='1:1')
    heads={};replayed=0
    with threadpool_limits(limits=2):
        for c in fit['cells']:
            verify(c['hashes']);y,k=c['origin'],c['fold']
            g=q.filter((pl.col('origin_year')==y)&(pl.col('outer_fold')==k)).sort('row_id')
            for h in c['heads']:
                a=h['arm'];te=frames[a,k].filter(pl.col('row_id').is_in(g['row_id'])).sort('row_id')
                m=joblib.load(h['path']);heads[a,y,k]=m
                assert np.allclose(m.predict(safe_matrix(te,pre['names'])),g['shared_'+a+'_raw_rate'],atol=1e-10,rtol=0)
                original=g.filter(~pl.col('source_addition'));mlb=original.filter(pl.col('prior_debut')>0)
                assert mlb['shared_'+a+'_rate'].equals(mlb['current_rate'])
                assert original['shared_'+a+'_pa'].equals(original['current_pa'])
                assert original['shared_'+a+'_p'].equals(original['current_p'])
                assert np.allclose(g['shared_'+a+'_value'],g['shared_'+a+'_pa']*(g['shared_'+a+'_rate']/600+g['origin_replacement_rate']),atol=1e-10)
                replayed+=1
    original=q.filter(~pl.col('source_addition'));added=q.filter(pl.col('source_addition'))
    assert (original.height,added.height)==(30506,13)
    foreign_ids=frames['foreign',0].filter(pl.col('evidence_foreign_source_present')>0)['row_id'].to_list()
    scopes=[('original_all',original),('additions',added),
        ('upper_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Upper minors'))),
        ('lower_never_debut',original.filter((pl.col('prior_debut')==0)&(pl.col('stage')=='Lower minors'))),
        ('foreign_never_debut',original.filter((pl.col('prior_debut')==0)&pl.col('row_id').is_in(foreign_ids))),
        ('all_never_debut',original.filter(pl.col('prior_debut')==0)),
        ('original_no_arrival',original.filter(pl.col('next_pa')==0))]
    scopes += [('origin_'+str(y),original.filter(pl.col('origin_year')==y)) for y in sorted(original['origin_year'].unique())]
    scores=[];uncertainty=[]
    for name,g in scopes:
        active=g.filter(pl.col('next_pa')>0)
        arms=ARMS+([] if name=='additions' else ['current'])
        scores.append(dict(scope=name,rows=g.height,people=g['player_id'].n_unique(),actual_PA=int(g['next_pa'].sum()),actual_value=float(g['actual_relative_value'].sum()),
            scores={a:score(g,a) for a in arms},
            PA_weighted_rate={a:rate_score(active,a+'_rate','actual_relative_rate',True) if active.height else None for a in arms}))
        if name in ['original_all','upper_never_debut','lower_never_debut','foreign_never_debut']:
            for a in ARMS:
                uncertainty.append(dict(scope=name,arm=a,value=interval(g,a,'current'),rate=rate_interval(g,a,'current') if active.height else None))
    anchor=pl.read_parquet(ANCHOR).select('row_id','steamer_index','zips_index','steamer_rate','common_zips_rate')
    public=original.join(anchor,on='row_id',how='left',validate='1:1').filter((pl.col('pa_0')>0)&pl.col('steamer_index').is_not_null()&pl.col('zips_index').is_not_null())
    assert public.height==2627
    assert all(public[a+'_rate'].equals(public['current_rate']) and public[a+'_pa'].equals(public['current_pa']) for a in ARMS)
    pa=public.filter(pl.col('next_pa')>0)
    public_result=dict(rows=public.height,unchanged_current_forecast=True,PA_weighted_common_rate_rmse={a:rate_score(pa,n,'actual_common_rate',True)
        for a,n in [('current','current_rate'),('steamer','steamer_rate'),('zips','common_zips_rate')]},
        limit='Existing raw-public conversion, release and park/environment qualifications apply; no PA improvement in this experiment')
    selected={rid:['retained fixed prior diagnostic'] for rid in source_cases}
    eligible=original.filter(pl.col('prior_debut')==0)
    for a in ARMS:
        g=eligible.with_columns(((pl.col('current_value')-pl.col('actual_relative_value'))**2-(pl.col(a+'_value')-pl.col('actual_relative_value'))**2).alias('gain'),
             (pl.col(a+'_value')-pl.col('actual_relative_value')).alias('error'))
        for why,z in [('largest gain',g.sort('gain',descending=True)),('largest harm',g.sort('gain')),
            ('false high',g.sort('error',descending=True)),('false low',g.sort('error')),
            ('ordinary',g.filter(pl.col('next_pa').is_between(100,600)).sort(pl.col('error').abs()))]:
            selected.setdefault(z['row_id'][0],[]).append(a+' '+why)
    support=pl.read_parquet(OUT/'profile-support.parquet');cases=[]
    raw_source=pl.read_parquet(GEN/'practical-hitter-v31/counts.parquet')
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            r=q.filter(pl.col('row_id')==rid).row(0,named=True);y,k=r['origin_year'],r['outer_fold']
            traces={};probes={};inputs={}
            for a in pre['arms']:
                row=frames[a,k].filter(pl.col('row_id')==rid);x=safe_matrix(row,pre['names'])[0];m=heads[a,y,k]
                traces[a]=linear_trace(m,x,pre['names']);inputs[a]=row.select(pre['names']).to_dicts()[0]
                # Coherent 0.1 percentage-point probability transfers; no model refit.
                moves={}
                for event in ['HR','UBB','K','1B']:
                    z=x.copy();z[pre['names'].index('shared_other')]-=.01;z[pre['names'].index('shared_'+event)]+=.01
                    moves[event]=float(m.predict(z[None,:])[0]-m.predict(x[None,:])[0])
                probes[a]=dict(transfers=moves,units='Batting wins per 600 change for 0.001 probability transferred from other',
                              deployed_new_head=(r['prior_debut']==0 or r['source_addition']),limit='Fixed-fit local mechanics, not causal or validated replacement forecasts')
            peers=original.filter((pl.col('origin_year')==y)&(pl.col('prior_debut')==r['prior_debut'])&(pl.col('stage')==r['stage'])&(pl.col('player_id')!=r['player_id'])).with_columns(
                (((pl.col('age')-r['age'])/3)**2+((pl.col('minor_pa_0')-r['minor_pa_0'])/250)**2+(pl.col('scout_rank_score_0')-r['scout_rank_score_0'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(row_id=rid,selection=reasons,origin={n:r[n] for n in ['player_id','player_name','origin_year','target_year','age','stage','prior_debut','outer_fold','source_addition']},
                source=source_cases.get(rid),source_history=raw_source.filter((pl.col('player_id')==r['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_history=raw_source.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')==y+1)&(pl.col('bucket')=='MLB')).to_dicts(),
                forecasts={a:{n:r[a+'_'+n] for n in ['pa','rate','value','p','conditional_pa']} for a in ARMS+([] if r['source_addition'] else ['current'])},
                actual=dict(PA=r['next_pa'],rate=r['actual_relative_rate'] if r['next_pa']>0 else None,value=r['actual_relative_value']),
                fitted_traces=traces,actual_inputs=inputs,coherent_direction_probes=probes,training_support=support.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','minor_pa_0','scout_rank_score_0','current_pa','current_rate','shared_foreign_rate','shared_foreign_value','next_pa','actual_relative_rate','actual_relative_value').to_dicts()))
    save('scores.json',dict(scopes=scores,public=public_result));save('intervals.json',uncertainty);save('reviewed-cases.json',dict(cases=cases,player_walkthrough_status='pending'))
    save('review-receipt.json',dict(heads_replayed=replayed,compatible_labels_reconstructed=True,original_PA_unchanged=True,
        original_established_talent_unchanged=True,rows=q.height,player_walkthrough_status='pending',protected_outcomes_used=False,
        artifact_hashes={str(OUT/n):sha256_file(OUT/n) for n in ['predictions.parquet','scores.json','intervals.json','reviewed-cases.json']}))
    for s in scores:print(s['scope'],{a:(round(v['value_rmse'],6),round(s['PA_weighted_rate'][a],5) if s['PA_weighted_rate'][a] is not None else None) for a,v in s['scores'].items()},flush=True)
    print('Seventy heads replayed. Player review pending; no disposition yet.',flush=True)


if __name__=='__main__':main()
