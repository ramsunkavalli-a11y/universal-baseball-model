"""Replay both heads and expose sources, coefficients, paths and complete cohorts."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import prepare_hitter_draft_age_v42 as e
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file


def ridge_trace(model,x,cols):
    terms=x*model.coef_;order=np.argsort(-abs(terms));raw=float(model.intercept_+terms.sum())
    assert np.isclose(raw,model.predict(x.reshape(1,-1))[0],atol=1e-8)
    return dict(reference=float(model.intercept_),raw_prediction=raw,
        feature_effects=[dict(feature=cols[j],scaled_input=float(x[j]),coefficient=float(model.coef_[j]),path_effect=float(terms[j])) for j in order],
        draft_block_accounting=float(sum(t for c,t in zip(cols,terms) if c.startswith('draft_'))),
        interpretation='Exact coefficient accounting from the scaled-zero reference; not causal or an independently validated feature effect.')


def old_notes(y,k):
    n=e.r.read(e.base.OUT/f'fits-{y}-{k}.json')['models']
    if not n:
        alln=e.r.read(e.base.BASE/f'fits-{y}-{k}.json')['models']
        n=[q for q in alln if (q['metric']=='pa' and q['arm']=='pedigree') or (q['metric']=='rate' and q['arm']=='safe_ridge')]
    return n


def main():
    pre=e.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.OUT/'features.parquet')
    base=pl.read_parquet(e.base.OUT/'predictions.parquet').sort('row_id');assert f.select(base.columns).equals(base)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    heads=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert not set(tr['player_id'])&set(te['player_id'])
            assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
            for n in e.r.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")['models']:
                assert sha256_file(Path(n['path']))==n['sha256'];m=joblib.load(n['path']);metric=n['metric']
                x=te.select(pre['features']).to_numpy() if metric=='pa' else e.scale.safe_matrix(te,pre['features'])
                p=m.predict(x)
                if metric=='pa':p=np.clip(p,0,800);p[te['hard_unavailable'].to_numpy()]=0
                assert np.allclose(p,q['draft_age_'+metric],atol=1e-9,rtol=0);heads+=1
    for a in ['draft_age','age_pa_only','age_rate_only']:
        assert np.allclose(f[a+'_value'],f[a+'_pa']*(f[a+'_rate']/600+f['origin_replacement_rate']),atol=1e-10,rtol=0)
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    q=f.join(source.select('row_id','draft_age_proxy','draft_age_known'),on='row_id',validate='1:1')
    scopes=[('all',q),('public_active',q.filter(pl.col('row_id').is_in(public['row_id']))),
        ('limited_drafted_never',q.filter((pl.col('prior_debut')==0)&(pl.col('draft_known')==1)&(pl.col('recent_all_pa')<150))),
        ('brief_debut',q.filter(pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300))),
        ('absent_prior_debut',q.filter((pl.col('pa_0')==0)&(pl.col('prior_debut')==1))),
        ('first_older_top_draft',q.filter((pl.col('prior_debut')==0)&(pl.col('recent_all_pa')<150)&
            (pl.col('draft_year')==pl.col('origin_year'))&(pl.col('pick_number')<=15)&
            (pl.col('draft_age_known')==1)&(pl.col('draft_age_proxy')>=20)))]
    scopes.extend(('origin_'+str(y),q.filter(pl.col('origin_year')==y)) for y in e.r.YEARS)
    scopes.extend(('stage_'+s,q.filter(pl.col('stage')==s)) for s in sorted(q['stage'].unique()))
    scores=[];intervals=[]
    for name,g in scopes:
        arms=['draft_age','age_pa_only','age_rate_only','cohort','safe_ridge']+(['steamer'] if name=='public_active' else [])
        scores.append(dict(scope=name,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),
            actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms},
            rate_scores={a:rate_score(g,a+'_rate') for a in ['draft_age','cohort','safe_ridge']}))
        if name in ['all','public_active','limited_drafted_never','brief_debut'] and len(g):
            for metric in ['pa','value']:intervals.append(dict(scope=name,**paired(g,'draft_age','cohort',metric)))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    selected={}
    for pid,y in e.FIXED:
        z=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(z)==1;selected[z['row_id'][0]]=['Fixed diagnostic']
    for metric in ['pa','value']:
        z=f.with_columns(((pl.col('cohort_'+metric)-pl.col('next_'+metric))**2-(pl.col('draft_age_'+metric)-pl.col('next_'+metric))**2).alias('gain'),
            (pl.col('draft_age_'+metric)-pl.col('next_'+metric)).alias('error'))
        for label,g in [('largest gain',z.sort('gain',descending=True)),('largest harm',z.sort('gain')),('false high',z.sort('error',descending=True)),
            ('false low',z.sort('error')),('ordinary',z.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:selected.setdefault(g['row_id'][0],[]).append(metric+' '+label)
    cases=[];raw=pl.read_parquet(e.r.OUT/'counts.parquet');support=pl.read_parquet(e.OUT/'support.parquet')
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);s=te.to_dicts()[0];y,k=o['origin_year'],o['outer_fold'];accounts={}
            old=old_notes(y,k);new=e.r.read(e.OUT/f'fit-{y}-{k}.json')['models']
            for label,notes,cols in [('control',old,pre['old_features']),('candidate',new,pre['features'])]:
                accounts[label]={}
                for metric in ['pa','rate']:
                    n=next(n for n in notes if n['metric']==metric);m=joblib.load(n['path']);x=te.select(cols).to_numpy()[0] if metric=='pa' else e.scale.safe_matrix(te,cols)[0]
                    t=trace(m,x,cols) if metric=='pa' else ridge_trace(m,x,cols);accounts[label][metric]=t
                    expected=o[('cohort' if label=='control' else 'draft_age')+'_'+metric];p=t['raw_prediction']
                    if metric=='pa':p=float(np.clip(p,0,800))*(not o['hard_unavailable'])
                    assert np.isclose(p,expected,atol=1e-8)
            peers=source.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=o['player_id'])&
                (pl.col('prior_debut')==o['prior_debut'])&(pl.col('stage')==o['stage']))
            distance=sum(((pl.col(c)-s[c])/v)**2 for c,v in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25),('draft_known',1),('recent_all_pa',600)])
            peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
            peers=peers.join(f.select('row_id','cohort_pa','cohort_rate','draft_age_pa','draft_age_rate'),on='row_id',validate='1:1')
            cases.append(dict(origin=o,selection=reasons,source_history=raw.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                actual_inputs={c:s[c] for c in set(pre['old_features']+pre['features'])},draft_age_proxy=s['draft_age_proxy'],
                accounting=accounts,training_profile=support.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','stage','draft_age_proxy','pick_number','recent_all_pa','pa_0','AAA_0_pa','AA_0_pa',
                    'cohort_pa','draft_age_pa','cohort_rate','draft_age_rate','next_pa','next_batting_rate','next_value','distance').to_dicts()))
    e.write('cases.json',cases)
    e.write('verification.json',dict(replayed_heads=heads,baseline_fields_bit_exact=True,identical_training_membership=True,
        target_independent_draft_age=True,source_hashes_unchanged=True,player_walkthrough_status='pending',protected_outcomes_used=False))
    for s in scores[:6]:print(s['scope'],s['rows'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],6)) for a,v in s['scores'].items()},flush=True)
    print('Prepared',len(cases),'player walks; final disposition remains pending.',flush=True)


if __name__=='__main__':main()
