"""One fixed source-extension comparison; preserve baseline and hard players."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
import prepare_practical_hitter_v31 as r
import prepare_practical_hitter_v33 as s
from fit_practical_hitter_v31 import tree,weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

SOURCE=r.ROOT/'reports/generated/hitter-2020-cohort'
BASE=r.ROOT/'reports/generated/practical-hitter-v33b'
OUT=r.ROOT/'reports/generated/practical-hitter-v34'


def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=str),encoding='utf8')


def prepare():
    assert r.read(SOURCE/'source-review.json')['player_walkthrough_status']=='complete'
    assert r.read(BASE/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists()
    OUT.mkdir(parents=True,exist_ok=True)
    f=pl.read_parquet(SOURCE/'features.parquet');old=r.read(BASE/'preflight.json')
    features=old['features']['pedigree'];cells=[];support=[]
    fresh=f.filter(pl.col('origin_year')==2020)
    for c in old['cells']:
        year,fold=c['year'],c['fold']
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']))
        if year>=2021:tr=pl.concat([tr,fresh.filter(pl.col('outer_fold')!=fold)])
        tr=tr.sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
        _,note=preflight(tr,te,cutoff=year,fold=fold,features=features,
            expected_keys=te.select('row_id','horizon').iter_rows())
        assert tr.unique('row_id').height==len(tr)
        for head,sub in [('all',tr),('active',tr.filter(pl.col('next_pa')>0))]:
            def profile(g):return g.with_columns((pl.col('age')//5).alias('age_group'),
                (pl.sum_horizontal([pl.col(f'{b}_{lag}_pa') for b in r.BUCKETS for lag in range(3)])<100).alias('thin_entry'))
            keys=['stage','prior_debut','age_group','draft_known','thin_entry']
            counts=profile(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_players'))
            support.append(profile(te).select('row_id',*keys).join(counts,on=keys,how='left',validate='m:1').with_columns(
                pl.col('profile_players').fill_null(0),pl.lit(head).alias('head'),pl.lit(year).alias('origin_year'),pl.lit(fold).alias('fold')))
        cells.append(dict(year=year,fold=fold,**note,training_row_ids=tr['row_id'].to_list(),test_row_ids=c['test_row_ids'],
            added_origin_2020_rows=int((tr['origin_year']==2020).sum())))
    pl.concat(support).write_parquet(OUT/'support.parquet')
    paths=[SOURCE/'features.parquet',SOURCE/'source-review.json',BASE/'preflight.json',BASE/'scored-predictions.parquet',
        OUT/'support.parquet',Path(__file__),r.ROOT/'docs/practical-hitter-2020-extension-test.md']
    write('preflight.json',dict(before_fitting=True,features=features,cells=cells,
        input_hashes={str(p):sha256_file(p) for p in paths},evaluation_rows=30506,source_extension_only=True))
    print('All 35 all/active training-cell audits saved before fitting.',flush=True)


def fit():
    pre=r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(SOURCE/'features.parquet');base=pl.read_parquet(BASE/'scored-predictions.parquet')
    features=pre['features'];frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            te=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            if path.exists():
                n=r.read(OUT/f'fits-{y}-{k}.json');assert sha256_file(path)==n['prediction_sha256']
                for h in n['models']:assert sha256_file(Path(h['path']))==h['sha256']
                frames.append(pl.read_parquet(path));fits.extend(n['models']);continue
            q=te;notes=[]
            if not c['added_origin_2020_rows']:
                q=q.with_columns(pl.col('safe_ridge_pa').alias('cohort_pa'),
                    pl.col('safe_ridge_rate').alias('cohort_rate'),pl.col('safe_ridge_value').alias('cohort_value'))
            else:
                tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
                for metric in ['pa','rate']:
                    sub=tr.filter(pl.col('next_pa')>0) if metric=='rate' else tr;w=weights(sub)
                    if metric=='rate':w*=sub['next_pa'].to_numpy();w*=len(w)/w.sum()
                    model=Ridge(alpha=100) if metric=='rate' else tree()
                    x=s.safe_matrix(sub,features) if metric=='rate' else sub.select(features).to_numpy()
                    model.fit(x,sub['next_batting_rate' if metric=='rate' else 'next_pa'].to_numpy(),sample_weight=w)
                    artifact=OUT/f'cohort-{metric}-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
                    testx=s.safe_matrix(te,features) if metric=='rate' else te.select(features).to_numpy()
                    pred=model.predict(testx);assert np.isfinite(pred).all()
                    if metric=='pa':pred=np.clip(pred,0,800);pred[te['hard_unavailable'].to_numpy()]=0
                    q=q.with_columns(pl.Series('cohort_'+metric,pred))
                    notes.append(dict(metric=metric,path=str(artifact),sha256=sha256_file(artifact),features=features,
                        training_rows=len(sub),training_players=sub['player_id'].n_unique(),maximum_target_year=int(sub['target_year'].max())))
                q=q.with_columns((pl.col('cohort_pa')*(pl.col('cohort_rate')/600+pl.col('origin_replacement_rate'))).alias('cohort_value'))
            q.write_parquet(path);write(f'fits-{y}-{k}.json',dict(models=notes,prediction_sha256=sha256_file(path)))
            frames.append(q);fits.extend(notes)
            print(f'{y}/{k}: {len(q)} unchanged forecasts; {len(notes)} new heads',flush=True)
    q=pl.concat(frames).sort('row_id');assert len(q)==30506
    assert q.select('row_id','next_pa','next_value').equals(base.select('row_id','next_pa','next_value').sort('row_id'))
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    write('fit-report.json',dict(new_heads=len(fits),rows=len(q),earlier_baseline_reused_rows=int(q.filter(pl.col('origin_year')<2020).height),
        source_extension_only=True,player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=='__main__':
    import sys
    prepare() if '--prepare' in sys.argv else fit()
