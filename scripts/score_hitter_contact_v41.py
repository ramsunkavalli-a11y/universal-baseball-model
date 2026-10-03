"""Replay fixed rate heads; score MLB outcomes and export actual player mechanics."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_hitter_contact_v41 as e
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file

ARMS=['contact_ridge','contact_hist']


def ridge_trace(model,x,names,shape=()):
    ref=np.zeros(len(names))
    for j,c in enumerate(names):
        if c in shape and not c.endswith(('_log_n','_coverage','_available')):ref[j]=1
    reference=float(model.intercept_+model.coef_@ref);effects=(x-ref)*model.coef_;raw=float(reference+effects.sum())
    assert np.isclose(raw,model.predict(x.reshape(1,-1))[0],atol=1e-8)
    order=np.argsort(-abs(effects))
    return dict(reference=reference,raw_prediction=raw,contact_block_accounting=float(sum(v for c,v in zip(names,effects) if c.startswith('shape_'))),
        feature_effects=[dict(feature=names[j],scaled_input=float(x[j]),path_effect=float(effects[j])) for j in order[:16]],
        interpretation='Exact centered coefficient accounting, not causal effect or a fixed-input ablation; refitting changes the other coefficients too.')


def main():
    pre=e.e.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.OUT/'features.parquet')
    base=pl.read_parquet(e.e.base.OUT/'predictions.parquet').sort('row_id');assert f.select(base.columns).equals(base)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    heads=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert not set(tr['player_id'])&set(te['player_id'])
            assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
            notes=e.e.r.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")['models'];usable=q['contact_supported'].to_numpy()
            for arm in ARMS:
                assert q[arm+'_pa'].equals(q['cohort_pa'])
                assert q.filter(~pl.col('contact_supported'))[arm+'_rate'].equals(q.filter(~pl.col('contact_supported'))['cohort_rate'])
                assert np.allclose(q[arm+'_value'],q['cohort_pa']*(q[arm+'_rate']/600+q['origin_replacement_rate']),atol=1e-10,rtol=0)
                if usable.any():
                    n=next(n for n in notes if n['arm']==arm);assert sha256_file(Path(n['path']))==n['sha256']
                    model=joblib.load(n['path']);pred=model.predict(e.matrix(te,pre,arm));assert np.allclose(pred[usable],q[arm+'_rate'].to_numpy()[usable],atol=1e-9,rtol=0);heads+=1
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',f),('contact_supported',f.filter(pl.col('contact_supported'))),('public_active',public),
        ('current_mlb',f.filter(pl.col('pa_0')>0)),('never_debut',f.filter(pl.col('prior_debut')==0)),
        ('brief_debut',f.filter(pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300)))]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y)) for y in e.e.r.YEARS)
    scopes.extend(('stage_'+s,f.filter(pl.col('stage')==s)) for s in sorted(f['stage'].unique()))
    scores=[];intervals=[]
    for name,g in scopes:
        arms=ARMS+['cohort','safe_ridge']+(['steamer'] if name=='public_active' else [])
        scores.append(dict(scope=name,rows=len(g),players=g['player_id'].n_unique(),contact_supported_rows=int(g['contact_supported'].sum()),
            actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms},
            rate_scores={a:rate_score(g,a+'_rate') for a in ARMS+['cohort']}))
        if name in ['all','contact_supported','public_active','current_mlb','brief_debut']:
            for arm in ARMS:intervals.append(dict(scope=name,**paired(g,arm,'cohort','value')))
    e.e.write('scores.json',scores);e.e.write('intervals.json',intervals)
    e.e.write('verification.json',dict(replayed_rate_heads=heads,old_columns_bit_exact=True,workload_bit_exact=True,unsupported_rate_fallback_exact=True,
        player_walkthrough_status='pending',protected_outcomes_used=False,predictive_certification=False))
    for s in scores[:4]:print(s['scope'],{a:(round(v['value_rmse'],6),round(s['rate_scores'][a]['rmse'],5) if a in s['rate_scores'] else None) for a,v in s['scores'].items()},flush=True)
    chosen={}
    for pid,y in e.e.FIXED:
        row=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(row)==1;chosen[row['row_id'][0]]=['Fixed case']
    for arm in ARMS:
        q=f.filter(pl.col('contact_supported')).with_columns(((pl.col('cohort_value')-pl.col('next_value'))**2-(pl.col(arm+'_value')-pl.col('next_value'))**2).alias('gain'),
            (pl.col(arm+'_value')-pl.col('next_value')).alias('error'))
        for label,g in [('largest value gain',q.sort('gain',descending=True)),('largest value harm',q.sort('gain')),('false high',q.sort('error',descending=True)),
            ('false low',q.sort('error')),('ordinary',q.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:chosen.setdefault(g['row_id'][0],[]).append(arm+' '+label)
    cases=[];official=pl.read_parquet(e.e.r.OUT/'counts.parquet');contacts=pl.read_parquet(e.OUT/'league-contact-counts.parquet')
    with threadpool_limits(limits=2):
        for rid,reasons in chosen.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);y,k=o['origin_year'],o['outer_fold']
            notes=e.e.r.read(e.OUT/f'fit-{y}-{k}.json')['models'];old=e.e.r.read(e.e.base.OUT/f'fits-{y}-{k}.json')['models']
            if not old:old=[n for n in e.e.r.read(e.e.base.BASE/f'fits-{y}-{k}.json')['models'] if n['arm']=='safe_ridge']
            oldnote=next(n for n in old if n['metric']=='rate');oldmodel=joblib.load(oldnote['path'])
            oldtrace=ridge_trace(oldmodel,e.scale.safe_matrix(te,pre['old_features'])[0],pre['old_features']);assert np.isclose(oldtrace['raw_prediction'],o['cohort_rate'],atol=1e-8)
            traces={};names=pre['old_features']+pre['added_features']
            for arm in ARMS:
                if not o['contact_supported']:traces[arm]=dict(fallback=True,raw_prediction=o['cohort_rate'],reason='No observed bucket with actual active-player training support');continue
                n=next(n for n in notes if n['arm']==arm);model=joblib.load(n['path']);x=e.matrix(te,pre,arm)[0]
                traces[arm]=ridge_trace(model,x,names,pre['added_features']) if arm=='contact_ridge' else trace(model,x,names)
                assert np.isclose(traces[arm]['raw_prediction'],o[arm+'_rate'],atol=1e-8)
            peers=source.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=o['player_id'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
            distance=sum(((pl.col(c)-o[c])/s)**2 for c,s in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25),('draft_known',1)])
            peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3).join(
                f.select('row_id','cohort_pa','cohort_rate',*[a+'_rate' for a in ARMS]),on='row_id',validate='1:1')
            cases.append(dict(origin=o,selection=reasons,batting_history=official.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                raw_contact_history=contacts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','league_id','core_bin').to_dicts(),
                actual_inputs={c:te[c][0] for c in names},benchmark_accounting=oldtrace,candidate_accounting=traces,
                peers=peers.select('player_id','player_name','age','pa_0','AAA_0_pa','AA_0_pa','draft_known','pick_number','cohort_pa','cohort_rate',*[a+'_rate' for a in ARMS],'next_pa','next_batting_rate','next_value','distance').to_dicts()))
    e.e.write('cases.json',cases);print('Prepared',len(cases),'actual stats-to-prediction reviews; disposition pending.',flush=True)


if __name__=='__main__':main()
