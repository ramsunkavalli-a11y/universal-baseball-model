"""Fixed broad-population architectures with saved conditional intermediates."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
import prepare_practical_hitter_v31 as r
from universal_baseball.storage import sha256_file

def weights(g):
    years=g['origin_year'].to_numpy();u,c=np.unique(years,return_counts=True)
    w=np.array([len(g)/(len(u)*c[np.where(u==y)[0][0]]) for y in years]);return w
def tree(classify=False):
    cls=HistGradientBoostingClassifier if classify else HistGradientBoostingRegressor
    return cls(max_iter=250,max_depth=3,min_samples_leaf=30,learning_rate=.05,l2_regularization=10,early_stopping=False,random_state=31)
def save_fit(model,g,features,target,path,kind,pa_weight=False):
    x=g.select(features).to_numpy();y=g[target].to_numpy();w=weights(g)
    if pa_weight:w*=g['next_pa'].to_numpy();w*=len(w)/w.sum()
    model.fit(x,y,**({'ridge__sample_weight':w} if kind=='ridge' else {'sample_weight':w}))
    joblib.dump(model,path,compress=3)
    return dict(path=str(path),sha256=sha256_file(path),kind=kind,features=features,target=target,training_rows=len(g),training_players=g['player_id'].n_unique(),
        minimum_target_year=int(g['target_year'].min()),maximum_target_year=int(g['target_year'].max()),future_pa_weight=pa_weight)
def main():
    pre=r.read(r.OUT/'preflight-ready.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    manifest=r.OUT/'fit-contract.json'
    if not manifest.exists():r.write('fit-contract.json',dict(preflight_sha256=sha256_file(r.OUT/'preflight-ready.json'),runner_sha256=sha256_file(Path(__file__)),
        contract_sha256=sha256_file(r.ROOT/'docs/practical-hitter-v31-contract.md'),prefit_correction_sha256=sha256_file(r.ROOT/'docs/practical-hitter-v31-prefit-source-correction.md'),before_fitting=True))
    contract=r.read(manifest);assert contract['runner_sha256']==sha256_file(Path(__file__))
    assert contract['preflight_sha256']==sha256_file(r.OUT/'preflight-ready.json')
    f=pl.read_parquet(pre['ready_features']);fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];cellpath=r.OUT/f'forecast-{y}-{k}.parquet';fitpath=r.OUT/f'fits-{y}-{k}.json'
            if cellpath.exists():
                old=r.read(fitpath)
                assert old['prediction_hash']==sha256_file(cellpath)
                for n in old['models']:assert sha256_file(Path(n['path']))==n['sha256']
                fits.extend(old['models']);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids']));te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            heads=[];q=te
            for arm,features in [('base_hurdle',pre['base_features']),('detail_hurdle',pre['detail_features'])]:
                model=tree(True);path=r.OUT/f'{arm}-state-{y}-{k}.joblib';note=save_fit(model,tr,features,'next_state',path,'classifier');heads.append(dict(arm=arm,head='state',**note))
                probs=model.predict_proba(te.select(features).to_numpy());assert model.classes_.tolist()==[0,1,2,3]
                assert np.allclose(probs.sum(1),1)
                hard=te['hard_unavailable'].to_numpy();probs[hard]=[1,0,0,0]
                pa=np.zeros(len(te));value=np.zeros(len(te))
                for state in range(4):q=q.with_columns(pl.Series(f'{arm}_p{state}',probs[:,state]))
                for state in [1,2,3]:
                    sub=tr.filter(pl.col('next_state')==state)
                    for metric in ['pa','value']:
                        model=tree();path=r.OUT/f'{arm}-{metric}{state}-{y}-{k}.joblib';note=save_fit(model,sub,features,'next_'+metric,path,'regressor')
                        heads.append(dict(arm=arm,head=metric+str(state),**note));prediction=model.predict(te.select(features).to_numpy())
                        if metric=='pa':prediction=np.clip(prediction,0,800);pa+=probs[:,state]*prediction
                        else:value+=probs[:,state]*prediction
                        q=q.with_columns(pl.Series(f'{arm}_conditional_{metric}{state}',prediction))
                q=q.with_columns(pl.Series(arm+'_pa',pa),pl.Series(arm+'_value',value))
            for metric in ['pa','value']:
                model=tree();path=r.OUT/f'direct_detail-{metric}-{y}-{k}.joblib'
                note=save_fit(model,tr,pre['detail_features'],'next_'+metric,path,'regressor');heads.append(dict(arm='direct_detail',head=metric,**note))
                pred=model.predict(te.select(pre['detail_features']).to_numpy())
                if metric=='pa':pred=np.clip(pred,0,800)
                pred[te['hard_unavailable'].to_numpy()]=0
                q=q.with_columns(pl.Series('direct_detail_'+metric,pred))
            active=tr.filter(pl.col('next_pa')>0)
            for family in ['ridge','hist']:
                for weight in ['equal','pa']:
                    arm=f'rate_{family}_{weight}';model=make_pipeline(StandardScaler(),Ridge(alpha=100)) if family=='ridge' else tree()
                    path=r.OUT/f'{arm}-{y}-{k}.joblib';note=save_fit(model,active,pre['detail_features'],'next_batting_rate',path,'ridge' if family=='ridge' else 'regressor',weight=='pa')
                    heads.append(dict(arm=arm,head='batting_rate',**note));pred=model.predict(te.select(pre['detail_features']).to_numpy())
                    assert np.isfinite(pred).all();q=q.with_columns(pl.Series(arm+'_rate',pred))
            floor=sum(w*q[f'quality_{lag}'].to_numpy()*(q[f'pa_{lag}'].to_numpy()+1200) for lag,w in enumerate([5,4,3]))/(
                sum(w*q[f'pa_{lag}'].to_numpy() for lag,w in enumerate([5,4,3]))+4800)
            q=q.with_columns(pl.Series('floor_rate',floor));assert q.select('next_pa','next_value').equals(te.select('next_pa','next_value'))
            for n in heads:
                replay=joblib.load(n['path']).predict_proba(te.select(n['features']).to_numpy()) if n['kind']=='classifier' else joblib.load(n['path']).predict(te.select(n['features']).to_numpy())
                assert np.isfinite(replay).all()
            q.write_parquet(cellpath);r.write(fitpath.name,dict(models=heads,prediction_hash=sha256_file(cellpath)))
            fits.extend(heads);print(f'Completed origin {y}, held-player group {k}: {len(te)} forecasts / {len(heads)} fitted heads',flush=True)
    allpred=pl.concat([pl.read_parquet(r.OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('origin_year','player_id')
    assert allpred.height==sum(c['test_rows'] for c in pre['cells']) and allpred['row_id'].n_unique()==len(allpred)
    allpred.write_parquet(r.OUT/'predictions.parquet');r.write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    r.write('fit-report.json',dict(new_fits=len(fits),rows=len(allpred),player_walkthrough_status='pending',protected_2026_used=False,frozen_forecast_changed=False,
        input_hashes=pre['input_hashes'],output_hashes={str(r.OUT/n):sha256_file(r.OUT/n) for n in ['predictions.parquet','fits.json','fit-contract.json']}))
    print(f'Finished {len(fits)} fixed heads and {len(allpred)} whole-population forecasts.')

if __name__=='__main__':main()
