"""Refit corrected pooled/draft candidates and matched direct control."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
import prepare_practical_hitter_v31 as r
import prepare_practical_hitter_v33 as s
from fit_practical_hitter_v31 import tree,weights
from universal_baseball.storage import sha256_file

def main():
    original=s.OUT;s.OUT=r.ROOT/'reports/generated/practical-hitter-v33b';pre=r.read(s.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    mp=s.OUT/'fit-contract.json'
    if not mp.exists():s.write(mp.name,dict(runner_sha256=sha256_file(Path(__file__)),preflight_sha256=sha256_file(s.OUT/'preflight.json'),before_fitting=True))
    assert r.read(mp)['runner_sha256']==sha256_file(Path(__file__)) and r.read(mp)['preflight_sha256']==sha256_file(s.OUT/'preflight.json')
    f=pl.read_parquet(s.OUT/'features.parquet');fits=[];frames=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=s.OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                n=r.read(s.OUT/f'fits-{y}-{k}.json');assert n['prediction_sha256']==sha256_file(path)
                for h in n['models']:assert sha256_file(Path(h['path']))==h['sha256']
                frames.append(pl.read_parquet(path));fits.extend(n['models']);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');q=te;models=[]
            assert (tr['origin_year']!=2020).all()
            if c['early_cell_identical']:
                q=pl.read_parquet(original/f'forecast-{y}-{k}.parquet');models=r.read(original/f'fits-{y}-{k}.json')['models']
                assert q.select('row_id','next_pa','next_value').equals(te.select('row_id','next_pa','next_value'))
            else:
                for arm,features in pre['features'].items():
                    for metric in ['pa','value','rate']:
                        sub=tr.filter(pl.col('next_pa')>0) if metric=='rate' else tr;w=weights(sub)
                        if metric=='rate':w*=sub['next_pa'].to_numpy();w*=len(w)/w.sum()
                        target='next_batting_rate' if metric=='rate' else 'next_'+metric;m=tree()
                        m.fit(sub.select(features).to_numpy(),sub[target].to_numpy(),sample_weight=w)
                        artifact=s.OUT/f'{arm}-{metric}-{y}-{k}.joblib';joblib.dump(m,artifact,compress=3)
                        pred=m.predict(te.select(features).to_numpy());assert np.isfinite(pred).all()
                        if metric=='pa':pred=np.clip(pred,0,800)
                        if metric!='rate':pred[te['hard_unavailable'].to_numpy()]=0
                        q=q.with_columns(pl.Series(arm+'_'+metric,pred))
                        models.append(dict(arm=arm,metric=metric,path=str(artifact),sha256=sha256_file(artifact),features=features,training_rows=len(sub),training_players=sub['player_id'].n_unique(),maximum_target_year=int(sub['target_year'].max()),future_pa_weight=metric=='rate'))
                    q=q.with_columns(pl.when(pl.col(arm+'_pa')==0).then(0).otherwise(pl.col(arm+'_value')).alias(arm+'_value'),
                        pl.col(arm+'_pa').alias(arm+'_product_pa'),(pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_product_value'))
                features=pre['features']['pedigree'];active=tr.filter(pl.col('next_pa')>0);w=weights(active)*active['next_pa'].to_numpy();w*=len(w)/w.sum()
                m=Ridge(alpha=100);m.fit(s.safe_matrix(active,features),active['next_batting_rate'].to_numpy(),sample_weight=w)
                artifact=s.OUT/f'safe_ridge-rate-{y}-{k}.joblib';joblib.dump(m,artifact,compress=3);pred=m.predict(s.safe_matrix(te,features));assert np.isfinite(pred).all()
                q=q.with_columns(pl.Series('safe_ridge_rate',pred),pl.col('pedigree_pa').alias('safe_ridge_pa'),
                    (pl.col('pedigree_pa')*(pl.Series(pred)/600+pl.col('origin_replacement_rate'))).alias('safe_ridge_value'))
                models.append(dict(arm='safe_ridge',metric='rate',path=str(artifact),sha256=sha256_file(artifact),features=features,training_rows=len(active),training_players=active['player_id'].n_unique(),maximum_target_year=int(active['target_year'].max()),future_pa_weight=True))
            for metric in ['pa','value']:
                features=pre['control_features'];artifact=r.OUT/f'direct_detail-{metric}-{y}-{k}.joblib' if c['early_cell_identical'] else s.OUT/f'repaired_direct-{metric}-{y}-{k}.joblib'
                if c['early_cell_identical']:m=joblib.load(artifact)
                else:
                    m=tree();m.fit(tr.select(features).to_numpy(),tr['next_'+metric].to_numpy(),sample_weight=weights(tr));joblib.dump(m,artifact,compress=3)
                pred=m.predict(te.select(features).to_numpy())
                if metric=='pa':pred=np.clip(pred,0,800)
                pred[te['hard_unavailable'].to_numpy()]=0
                q=q.with_columns(pl.Series('repaired_direct_'+metric,pred))
                models.append(dict(arm='repaired_direct',metric=metric,path=str(artifact),sha256=sha256_file(artifact),features=features,
                    training_rows=len(tr),training_players=tr['player_id'].n_unique(),maximum_target_year=int(tr['target_year'].max()),future_pa_weight=False))
            q=q.with_columns(pl.when(pl.col('repaired_direct_pa')==0).then(0).otherwise(pl.col('repaired_direct_value')).alias('repaired_direct_value'))
            q.write_parquet(path);s.write(f'fits-{y}-{k}.json',dict(models=models,prediction_sha256=sha256_file(path)))
            frames.append(q);fits.extend(models);print(f'Corrected {y}/{k}: {len(q)} forecasts / {len(models)} saved heads',flush=True)
    q=pl.concat(frames).sort('origin_year','player_id');assert len(q)==30506
    q.write_parquet(s.OUT/'predictions.parquet');s.write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    s.write('fit-report.json',dict(saved_heads=len(fits),new_fits=180,reused_heads=135,rows=len(q),player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))

if __name__=='__main__':main()
