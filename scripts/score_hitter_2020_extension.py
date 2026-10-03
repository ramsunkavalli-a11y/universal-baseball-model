"""Replay the source-extension experiment and expose aggregate and player evidence."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_hitter_2020_extension as e
import prepare_practical_hitter_v33 as s
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.storage import sha256_file


def main():
    pre=e.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet')
    source=pl.read_parquet(e.SOURCE/'features.parquet');baseline=pl.read_parquet(e.BASE/'scored-predictions.parquet').sort('row_id')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    assert f.select(baseline.columns).equals(baseline), 'Baseline/evaluation fields changed'
    replay=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            raw=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']))
            assert not set(tr['player_id']) & set(te['player_id'])
            assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
            assert te.select('row_id','next_pa','next_value').equals(raw.select('row_id','next_pa','next_value'))
            assert int((tr['origin_year']==2020).sum())==c['added_origin_2020_rows']
            for note in e.r.read(e.OUT/f"fits-{c['year']}-{c['fold']}.json")['models']:
                assert sha256_file(Path(note['path']))==note['sha256']
                model=joblib.load(note['path']);metric=note['metric'];cols=note['features']
                pred=model.predict(s.safe_matrix(te,cols) if metric=='rate' else te.select(cols).to_numpy())
                if metric=='pa':pred=np.clip(pred,0,800);pred[te['hard_unavailable'].to_numpy()]=0
                assert np.allclose(pred,te['cohort_'+metric].to_numpy(),rtol=0,atol=1e-10)
                replay+=1
            if not c['added_origin_2020_rows']:
                for metric in ['pa','value','rate']:assert te['cohort_'+metric].equals(te['safe_ridge_'+metric])
    assert np.allclose(f['cohort_value'],f['cohort_pa']*(f['cohort_rate']/600+f['origin_replacement_rate']),rtol=0,atol=1e-10)
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null())
    assert len(public)==1789
    scopes=[('all',f,['safe_ridge']),('v24_matched',f.filter(pl.col('v24_pa').is_not_null()),['safe_ridge','v24']),
        ('legacy_n_matched',f.filter(pl.col('legacy_n_pa').is_not_null()),['safe_ridge','legacy_n']),('public_active',public,['safe_ridge','v24','steamer'])]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y),['safe_ridge']) for y in e.r.YEARS)
    scopes.extend(('stage_'+stage,f.filter(pl.col('stage')==stage),['safe_ridge']) for stage in sorted(f['stage'].unique()))
    for name,cond in [('current_absent',pl.col('pa_0')==0),('current_partial',pl.col('pa_0').is_between(1,399)),
        ('current_regular',pl.col('pa_0')>=400),('thin_entry',pl.col('recent_all_pa')<100)]:
        scopes.append((name,f.filter(cond),['safe_ridge']))
    scores=[];intervals=[]
    for name,g,refs in scopes:
        scores.append(dict(scope=name,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ['cohort']+refs},rate_scores={a:rate_score(g,a+'_rate') for a in ['cohort','safe_ridge']}))
        if name in ['all','v24_matched','legacy_n_matched','public_active']:
            for metric in ['pa','value']:intervals.append(dict(scope=name,**paired(g,'cohort','safe_ridge',metric)))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    e.write('verification.json',dict(replayed_new_heads=replay,all_baseline_fields_bit_exact=True,
        earlier_forecasts_bit_exact=True,source_hashes_unchanged=True,all_training_membership_checked=True,
        protected_outcomes_used=False,player_walkthrough_status='pending',predictive_certification=False))
    for g in scores[:4]:print(g['scope'],g['rows'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5)) for a,v in g['scores'].items()})
    fixed=[(592450,2021),(592450,2024),(665487,2022),(666158,2022),(666158,2023),(680574,2024),(701762,2024),
           (668715,2022),(691026,2023),(621566,2022),(643446,2018)]
    selected={}
    for pid,y in fixed:
        g=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y))
        if len(g):selected[g['row_id'][0]]=['Additional missed-season return contrast after scoring' if (pid,y)==(666158,2023) else 'Predeclared diagnostic']
    affected=f.filter(pl.col('origin_year')>=2021).with_columns(
        ((pl.col('safe_ridge_value')-pl.col('next_value'))**2-(pl.col('cohort_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('cohort_value')-pl.col('next_value')).alias('error'))
    for label,g in [('Largest gain',affected.sort('gain',descending=True)),('Largest harm',affected.sort('gain')),
        ('Largest false high',affected.sort('error',descending=True)),('Largest false low',affected.sort('error')),
        ('Ordinary affected',affected.filter(pl.col('next_pa').is_between(200,600)&((pl.col('cohort_pa')-pl.col('safe_ridge_pa')).abs()>5)).with_columns(pl.col('error').abs().alias('absolute_error')).sort('absolute_error'))]:
        rid=g['row_id'][0];selected.setdefault(rid,[]).append(label)
    raw=pl.read_parquet(e.r.OUT/'counts.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,selection in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];y,k=o['origin_year'],o['outer_fold']
            heads=e.r.read(e.OUT/f'fits-{y}-{k}.json')['models']
            if not heads:heads=[n for n in e.r.read(e.BASE/f'fits-{y}-{k}.json')['models'] if n['arm']=='safe_ridge']
            rate=next(n for n in heads if n['metric']=='rate');model=joblib.load(rate['path']);cols=rate['features']
            row=f.filter(pl.col('row_id')==rid);x=s.safe_matrix(row,cols)[0];terms=x*model.coef_
            order=np.argsort(-np.abs(terms))[:12]
            peers=f.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=o['player_id'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])).with_columns((
                ((pl.col('age')-o['age'])/5)**2+((pl.col('pa_0')-o['pa_0'])/300)**2+
                (pl.col('pooled_mlb_quality')-o['pooled_mlb_quality'])**2+
                (pl.col('draft_known')-o['draft_known'])**2+(pl.col('draft_rank')-o['draft_rank'])**2).alias('distance')).sort('distance','player_id').head(3)
            c=next(c for c in pre['cells'] if c['year']==y and c['fold']==k)
            training=source.filter(pl.col('row_id').is_in(c['training_row_ids']))
            cases.append(dict(origin=o,selection=selection,source_history=raw.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                unchanged_feature_vector={col:o[col] for col in cols},saved_rate_model=rate,
                linear_intercept=float(model.intercept_),linear_terms=[dict(feature=cols[i],raw=o[cols[i]],fixed_scaled=float(x[i]),coefficient=float(model.coef_[i]),contribution=float(terms[i])) for i in order],
                added_training_people=training.filter(pl.col('origin_year')==2020)['player_id'].n_unique(),
                source_extension_training_targets=dict(pa=float(training.filter(pl.col('origin_year')==2020)['next_pa'].sum())),
                peers=peers.select('player_id','player_name','age','pa_0','draft_known','pick_number','next_pa','next_value','distance').to_dicts()))
    e.write('cases.json',cases)
    print('Player cases prepared for manual judgment:',len(cases))


if __name__=='__main__':main()
