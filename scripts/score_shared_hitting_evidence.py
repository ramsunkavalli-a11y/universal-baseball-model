"""Replay the relative-evidence fits and expose all losses and player mechanics."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_shared_hitting_evidence as e
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import EVENTS,score
from universal_baseball.storage import sha256_file

ARMS=['shared','rate_only','pa_only']


def main():
    pre=e.old.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet')
    source=pl.read_parquet(e.OUT/'features.parquet');baseline=pl.read_parquet(e.old.OUT/'predictions.parquet').sort('row_id')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    assert f.select(baseline.columns).equals(baseline)
    replay=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']))
            assert not set(tr['player_id']) & set(te['player_id'])
            assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
            assert q.select('row_id','next_pa','next_value').equals(te.select('row_id','next_pa','next_value'))
            for n in e.old.r.read(e.OUT/f"fits-{c['year']}-{c['fold']}.json")['models']:
                assert sha256_file(Path(n['path']))==n['sha256']
                model=joblib.load(n['path']);metric=n['metric'];cols=n['features']
                pred=model.predict(e.s.safe_matrix(te,cols) if metric=='rate' else te.select(cols).to_numpy())
                if metric=='pa':pred=np.clip(pred,0,800);pred[te['hard_unavailable'].to_numpy()]=0
                assert np.allclose(pred,q['shared_'+metric],rtol=0,atol=1e-10);replay+=1
    for a in ARMS:assert np.allclose(f[a+'_value'],f[a+'_pa']*(f[a+'_rate']/600+f['origin_replacement_rate']),rtol=0,atol=1e-10)
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null())
    assert len(public)==1789
    scopes=[('all',f,['cohort','safe_ridge']),('v24_matched',f.filter(pl.col('v24_pa').is_not_null()),['cohort','safe_ridge','v24']),
        ('legacy_n_matched',f.filter(pl.col('legacy_n_pa').is_not_null()),['cohort','legacy_n']),('public_active',public,['cohort','safe_ridge','steamer'])]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y),['cohort']) for y in e.old.r.YEARS)
    scopes.extend(('stage_'+stage,f.filter(pl.col('stage')==stage),['cohort']) for stage in sorted(f['stage'].unique()))
    for name,cond in [('current_absent',pl.col('pa_0')==0),('current_partial',pl.col('pa_0').is_between(1,399)),
        ('current_regular',pl.col('pa_0')>=400),('brief_debut',pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300)),
        ('thin_entry',pl.col('recent_all_pa')<100)]:scopes.append((name,f.filter(cond),['cohort']))
    scores=[];intervals=[]
    for name,g,refs in scopes:
        scores.append(dict(scope=name,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ARMS+refs},rate_scores={a:rate_score(g,a+'_rate') for a in ['shared','cohort']}))
        if name in ['all','v24_matched','legacy_n_matched','public_active','brief_debut']:
            for a in ARMS:
                for metric in ['pa','value']:intervals.append(dict(scope=name,**paired(g,a,'cohort',metric)))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    e.write('verification.json',dict(replayed_new_heads=replay,baseline_fields_bit_exact=True,unchanged_training_membership=True,
        source_hashes_unchanged=True,protected_outcomes_used=False,player_walkthrough_status='pending',predictive_certification=False))
    for g in scores[:4]:print(g['scope'],g['rows'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5)) for a,v in g['scores'].items()},flush=True)
    print('Weighted rate scores:',scores[0]['rate_scores'],flush=True)
    fixed=[(643446,2018),(668715,2022),(691026,2023),(701762,2024),(621566,2022),
        (592450,2024),(666158,2023),(680574,2024),(665487,2022)]
    selected={}
    for pid,y in fixed:
        q=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(q)==1
        selected[q['row_id'][0]]=['Predeclared diagnostic']
    for a in ARMS:
        q=f.with_columns(((pl.col('cohort_value')-pl.col('next_value'))**2-(pl.col(a+'_value')-pl.col('next_value'))**2).alias('gain'),
            (pl.col(a+'_value')-pl.col('next_value')).alias('error'))
        for label,g in [('largest gain',q.sort('gain',descending=True)),('largest harm',q.sort('gain')),
            ('false high',q.sort('error',descending=True)),('false low',q.sort('error')),
            ('ordinary',q.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:
            selected.setdefault(g['row_id'][0],[]).append(a+' '+label)
    raw=pl.read_parquet(e.old.r.OUT/'counts.parquet');cases=[];cols=pre['features']
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);new=te.to_dicts()[0];y,k=o['origin_year'],o['outer_fold']
            n=next(n for n in e.old.r.read(e.OUT/f'fits-{y}-{k}.json')['models'] if n['metric']=='rate');model=joblib.load(n['path'])
            x=e.s.safe_matrix(te,cols)[0];terms=x*model.coef_;assert np.isclose(terms.sum()+model.intercept_,o['shared_rate'],atol=1e-9)
            order=np.argsort(-abs(terms))[:12]
            oldheads=e.old.r.read(e.old.OUT/f'fits-{y}-{k}.json')['models']
            if not oldheads:oldheads=[n for n in e.old.r.read(e.old.BASE/f'fits-{y}-{k}.json')['models'] if n['arm']=='safe_ridge']
            oldrate=next(n for n in oldheads if n['metric']=='rate');oldmodel=joblib.load(oldrate['path'])
            probe=float(oldmodel.predict(e.s.safe_matrix(te,cols))[0])
            peers=f.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=o['player_id'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
            distance=sum(((pl.col(c)-o[c])/scale)**2 for c,scale in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('pooled_mlb_quality',1),('draft_rank',.25),('draft_known',1)])
            peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
            h=raw.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts();transforms=[]
            for ev,(num,den,prior) in EVENTS.items():
                total=sum((1. if v['season']==y else .8 if v['season']==y-1 else .6)*v[den] for v in h)
                for b in e.old.r.BUCKETS:
                    relevant=[v for v in h if v['bucket']==b]
                    if not relevant:continue
                    d=sum((1. if v['season']==y else .8 if v['season']==y-1 else .6)*v[den] for v in relevant)
                    events=sum((1. if v['season']==y else .8 if v['season']==y-1 else .6)*v[num] for v in relevant)
                    transforms.append(dict(bucket=b,event=ev,weighted_events=events,weighted_opportunities=d,total_opportunities=total,
                        prior=prior,old=o[f'pooled_{b}_{ev}'],new=new[f'pooled_{b}_{ev}']))
            cases.append(dict(origin=o,selection=reasons,source_history=h,transformations=transforms,new_actual_features={c:new[c] for c in cols},
                saved_rate_model=n,linear_intercept=float(model.intercept_),linear_terms=[dict(feature=cols[i],raw=new[cols[i]],fixed_scaled=float(x[i]),
                    coefficient=float(model.coef_[i]),contribution=float(terms[i])) for i in order],
                fixed_old_model_new_encoding_probe=probe,probe_claim='Mechanical distribution-shift diagnostic; no retraining, not causal or a replacement forecast.',
                peers=peers.select('player_id','player_name','age','pa_0','AAA_0_pa','AA_0_pa','draft_known','pick_number','next_pa','next_value','distance').to_dicts()))
    e.write('cases.json',cases);print('Prepared',len(cases),'player reviews.',flush=True)


if __name__=='__main__':main()
