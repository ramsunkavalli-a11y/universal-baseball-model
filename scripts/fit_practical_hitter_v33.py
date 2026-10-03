"""Fixed direct pooled/pedigree candidates and contribution-weighted rates."""
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
    pre=r.read(s.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    manifest=s.OUT/'fit-contract.json'
    if not manifest.exists():s.write(manifest.name,dict(runner_sha256=sha256_file(Path(__file__)),preflight_sha256=sha256_file(s.OUT/'preflight.json'),before_fitting=True))
    assert r.read(manifest)['runner_sha256']==sha256_file(Path(__file__))
    assert r.read(manifest)['preflight_sha256']==sha256_file(s.OUT/'preflight.json')
    f=pl.read_parquet(s.OUT/'features.parquet');frames=[];fits=[]
    with threadpool_limits(limits=2):
        for cell in pre['cells']:
            year,fold=cell['year'],cell['fold'];path=s.OUT/f'forecast-{year}-{fold}.parquet'
            if path.exists():
                n=r.read(s.OUT/f'fits-{year}-{fold}.json');assert n['prediction_sha256']==sha256_file(path)
                for m in n['models']:assert sha256_file(Path(m['path']))==m['sha256']
                frames.append(pl.read_parquet(path));fits.extend(n['models']);continue
            tr=f.filter(pl.col('row_id').is_in(cell['training_row_ids']));te=f.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('player_id')
            q=te;models=[]
            for arm,features in pre['features'].items():
                for metric in ['pa','value','rate']:
                    sub=tr.filter(pl.col('next_pa')>0) if metric=='rate' else tr
                    w=weights(sub)
                    if metric=='rate':w*=sub['next_pa'].to_numpy();w*=len(w)/w.sum()
                    target='next_batting_rate' if metric=='rate' else 'next_'+metric
                    model=tree();model.fit(sub.select(features).to_numpy(),sub[target].to_numpy(),sample_weight=w)
                    mp=s.OUT/f'{arm}-{metric}-{year}-{fold}.joblib';joblib.dump(model,mp,compress=3)
                    pred=model.predict(te.select(features).to_numpy());assert np.isfinite(pred).all()
                    if metric=='pa':pred=np.clip(pred,0,800)
                    if metric!='rate':pred[te['hard_unavailable'].to_numpy()]=0
                    q=q.with_columns(pl.Series(arm+'_'+metric,pred))
                    models.append(dict(arm=arm,metric=metric,path=str(mp),sha256=sha256_file(mp),features=features,training_rows=len(sub),training_players=sub['player_id'].n_unique(),
                        maximum_target_year=int(sub['target_year'].max()),future_pa_weight=metric=='rate'))
                q=q.with_columns(pl.when(pl.col(arm+'_pa')==0).then(0).otherwise(pl.col(arm+'_value')).alias(arm+'_value'),
                    pl.col(arm+'_pa').alias(arm+'_product_pa'),(pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_product_value'))
            features=pre['features']['pedigree'];active=tr.filter(pl.col('next_pa')>0);w=weights(active)*active['next_pa'].to_numpy();w*=len(w)/w.sum()
            model=Ridge(alpha=100);model.fit(s.safe_matrix(active,features),active['next_batting_rate'].to_numpy(),sample_weight=w)
            mp=s.OUT/f'safe_ridge-rate-{year}-{fold}.joblib';joblib.dump(model,mp,compress=3);pred=model.predict(s.safe_matrix(te,features));assert np.isfinite(pred).all()
            q=q.with_columns(pl.Series('safe_ridge_rate',pred),pl.col('pedigree_pa').alias('safe_ridge_pa'),
                (pl.col('pedigree_pa')*(pl.Series(pred)/600+pl.col('origin_replacement_rate'))).alias('safe_ridge_value'))
            models.append(dict(arm='safe_ridge',metric='rate',path=str(mp),sha256=sha256_file(mp),features=features,
                training_rows=len(active),training_players=active['player_id'].n_unique(),maximum_target_year=int(active['target_year'].max()),future_pa_weight=True))
            assert q.select('next_pa','next_value').equals(te.select('next_pa','next_value'))
            q.write_parquet(path);s.write(f'fits-{year}-{fold}.json',dict(models=models,prediction_sha256=sha256_file(path)))
            frames.append(q);fits.extend(models);print(f'Finished {year}/{fold}: {len(q)} forecasts, 7 heads',flush=True)
    q=pl.concat(frames).sort('origin_year','player_id');assert len(q)==30506 and q['row_id'].n_unique()==len(q)
    q.write_parquet(s.OUT/'predictions.parquet');s.write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    s.write('fit-report.json',dict(fits=len(fits),rows=len(q),player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))

if __name__=='__main__':main()
