"""Persist stats, pooled transformations, draft probes and origin-only peers."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import prepare_practical_hitter_v31 as r
import prepare_practical_hitter_v33 as s
from score_practical_hitter_v33 import ARMS
from universal_baseball.practical_hitter_v30 import EVENTS

FIXED=[(621566,2017),(643446,2018),(668715,2022),(691026,2023),(592450,2016),(592450,2021),
    (667670,2022),(680574,2024),(665487,2022),(120074,2016),(443558,2018),(805811,2024),(701762,2024),(815908,2024),(815888,2024)]

def main():
    import sys
    repaired='--repaired' in sys.argv
    if repaired:s.OUT=r.ROOT/'reports/generated/practical-hitter-v33b'
    control='repaired_direct' if repaired else 'direct_detail'
    assert r.read(s.OUT/'verification.json')['saved_heads_replayed']==(315 if repaired else 245)
    f=pl.read_parquet(s.OUT/'scored-predictions.parquet');pre=r.read(s.OUT/'preflight.json');support=pl.read_parquet(s.OUT/'support.parquet')
    counts=pl.read_parquet(r.OUT/'counts.parquet');chosen={}
    def add(g,reason):
        if len(g):chosen.setdefault(g['row_id'][0],[]).append(reason)
    for pid,y in FIXED:add(f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)),'fixed diagnostic')
    for arm in ARMS:
        q=f.with_columns(((pl.col(arm+'_value')-pl.col('next_value'))**2-(pl.col(control+'_value')-pl.col('next_value'))**2).alias('_change'),
            (pl.col(arm+'_value')-pl.col('next_value')).alias('_error'))
        add(q.sort('_change'),arm+' largest gain vs '+control);add(q.sort('_change',descending=True),arm+' largest harm vs '+control)
        add(q.sort('_error'),arm+' false low');add(q.sort('_error',descending=True),arm+' false high')
        add(q.filter(pl.col('next_pa').is_between(200,399)).sort(pl.col('_error').abs()),arm+' ordinary partial workload')
    add(f.sort(pl.col('safe_ridge_rate').abs(),descending=True),'largest absolute fixed-scale linear rate')
    cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            o=f.filter(pl.col('row_id')==rid).row(0,named=True);y,k=o['origin_year'],o['outer_fold'];features=pre['features']['pedigree']
            fitnotes=r.read(s.OUT/f'fits-{y}-{k}.json')['models']
            def load(arm,metric):return joblib.load(next(n['path'] for n in fitnotes if n['arm']==arm and n['metric']==metric))
            q=f.filter(pl.col('row_id')==rid);neutral=q.with_columns(*[pl.lit(1 if c=='draft_class_unknown' else 0).alias(c) for c in s.PED])
            probes={}
            for metric in ['pa','value','rate']:
                m=load('pedigree',metric);v=float(m.predict(neutral.select(features).to_numpy())[0])
                if metric=='pa':v=float(np.clip(v,0,800))
                if metric!='rate' and o['hard_unavailable']:v=0
                probes[metric]=v
            if probes['pa']==0:probes['value']=0
            m=load('safe_ridge','rate');x=s.safe_matrix(q,features)[0];terms=x*m.coef_
            assert np.isclose(terms.sum()+m.intercept_,o['safe_ridge_rate'],atol=1e-9)
            idx=np.argsort(abs(terms))[::-1][:8]
            history=counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts()
            pooled=[]
            for b in r.BUCKETS:
                h=[(1 if v['season']==y else .8 if v['season']==y-1 else .6,v) for v in history if v['bucket']==b]
                if not h:continue
                for ev,(num,den,prior) in EVENTS.items():
                    n=sum(w*v[num] for w,v in h);d=sum(w*v[den] for w,v in h);value=(n+100*prior)/(d+100)
                    assert np.isclose(value,o[f'pooled_{b}_{ev}'],atol=1e-12)
                    pooled.append(dict(bucket=b,event=ev,weighted_events=n,weighted_opportunities=d,prior=prior,input=value))
            pool=f.filter((pl.col('origin_year')==y)&(pl.col('row_id')!=rid)&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
            # Pedigree now enters peer matching; school/draft knownness is not future success.
            distance=sum(((pl.col(c)-o[c])/scale)**2 for c,scale in [('age',5),('elapsed',5),('pa_0',200),('AAA_0_pa',200),
                ('AA_0_pa',200),('minor_pa_0',300),('quality_0',1),('draft_known',1),('draft_rank',.25),('draft_college',1)])
            peers=pool.with_columns(distance.alias('origin_distance')).sort('origin_distance','player_id').head(3).select(
                'player_id','player_name','age','pa_0','AAA_0_pa','AA_0_pa','recent_all_pa','draft_known','pick_number','draft_school_class',
                'pedigree_pa','pedigree_value','next_pa','next_value','origin_distance').to_dicts()
            cases.append(dict(origin=o,selection=reasons,raw_level_history=history,actual_features={c:o[c] for c in features},
                pooled_transformations=pooled,pedigree_neutral_probe=probes,conditional_support=support.filter(pl.col('row_id')==rid).to_dicts(),
                safe_ridge_terms=dict(intercept=float(m.intercept_),terms=[dict(feature=features[i],raw=o[features[i]],fixed_scaled=float(x[i]),
                    coefficient=float(m.coef_[i]),contribution=float(terms[i])) for i in idx]),comparisons=peers))
    s.write('cases.json',cases)
    s.write('case-manifest.json',dict(cases=len(cases),player_walkthrough_status='pending',
        selection='Fixed cases; each arm largest V31-direct value gain/harm, false high/low, ordinary partial-workload case; largest linear rating.',
        peers='Same origin/stage/debut, nearest origin age/exposure/quality/draft-known/rank/college; no next outcomes.',
        probe='Saved pedigree fit, all draft inputs set to unknown. Artificial counterfactual, not causal or a replacement forecast.'))
    for c in cases:
        o=c['origin'];print(o['player_name'],o['origin_year'],o['next_pa'],round(o['next_value'],2),
            'control',round(o[control+'_pa']),round(o[control+'_value'],2),'pooled',round(o['pooled_pa']),round(o['pooled_value'],2),
            'ped',round(o['pedigree_pa']),round(o['pedigree_value'],2),'linear',round(o['safe_ridge_rate'],2),'probe',c['pedigree_neutral_probe'])

if __name__=='__main__':main()
