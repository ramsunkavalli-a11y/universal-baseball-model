"""Locked paired-outcome forest and exact empirical probabilities/PA quantiles."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import ExtraTreesRegressor
from threadpoolctl import threadpool_limits
import prepare_hitter_joint_forest_v43 as e
from fit_practical_hitter_v31 import weights
from universal_baseball.paired_leaf_distribution import predictions
from universal_baseball.storage import sha256_file


def empirical_reference(tr,te,w):
    pa=tr['next_pa'].to_numpy();v=tr['next_value'].to_numpy();events=np.column_stack([pa>0,pa>=400,v<0,v>=2])
    overall=np.average(events,axis=0,weights=w);lookup={}
    for key in set(tr.select('stage','prior_debut').iter_rows()):
        use=(tr['stage'].to_numpy()==key[0])&(tr['prior_debut'].to_numpy()==key[1])
        lookup[key]=((w[use,None]*events[use]).sum(axis=0)+20*overall)/(w[use].sum()+20)
    return np.asarray([lookup.get(k,overall) for k in te.select('stage','prior_debut').iter_rows()])


def main():
    pre=e.r.read(e.OUT/'preflight.json');assert pre['source_walkthrough_status']=='complete'
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(e.OUT/'features.parquet');base=pl.read_parquet(e.base.OUT/'predictions.parquet');cols=pre['features'];frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=e.OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=e.r.read(e.OUT/f'fit-{y}-{k}.json');assert sha256_file(path)==note['prediction_sha256'];assert sha256_file(Path(note['path']))==note['sha256']
                frames.append(pl.read_parquet(path));fits.append(note);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert te['row_id'].equals(q['row_id'])
            w=weights(tr);x=tr.select(cols).to_numpy();z=te.select(cols).to_numpy()
            pa=tr['next_pa'].to_numpy();value=tr['next_value'].to_numpy()
            settings={a:b for a,b in pre['settings'].items() if a not in ['output_scales','equal_origin_weights']}
            model=ExtraTreesRegressor(**settings);model.fit(x,np.column_stack([pa/600,value/2]),sample_weight=w)
            artifact=e.OUT/f'joint-forest-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
            means,prob,quantiles=predictions(model,x,z,pa,value,w);ref=empirical_reference(tr,te,w)
            hard=te['hard_unavailable'].to_numpy();means[hard]=0;prob[hard]=0;quantiles[hard]=0;ref[hard]=0
            q=q.with_columns(pl.Series('joint_pa',means[:,0]),pl.Series('joint_value',means[:,1]),
                *[pl.Series('joint_'+n,prob[:,j]) for j,n in enumerate(['p_active','p_400','p_negative','p_2wins'])],
                *[pl.Series('reference_'+n,ref[:,j]) for j,n in enumerate(['p_active','p_400','p_negative','p_2wins'])],
                *[pl.Series('joint_pa_q'+str(int(a*100)),quantiles[:,j]) for j,a in enumerate([.1,.5,.9])])
            q=q.with_columns(pl.when(pl.col('joint_pa')>0).then(600*(pl.col('joint_value')/pl.col('joint_pa')-pl.col('origin_replacement_rate'))).otherwise(0.).alias('joint_rate'),
                pl.col('joint_pa_q50').alias('joint_median_pa'))
            q.write_parquet(path);note=dict(path=str(artifact),sha256=sha256_file(artifact),prediction_sha256=sha256_file(path),
                training_rows=len(tr),training_players=tr['player_id'].n_unique(),maximum_target_year=int(tr['target_year'].max()),
                feature_count=len(cols),distribution_means_reconstruct_model=True,hard_unavailable_rows=int(hard.sum()))
            e.write(f'fit-{y}-{k}.json',note);fits.append(note);frames.append(q);print(f'{y}/{k}: {len(q)} complete mean/risk forecasts',flush=True)
    q=pl.concat(frames).sort('row_id');assert q.select(base.columns).equals(base.sort('row_id'))
    q.write_parquet(e.OUT/'predictions.parquet');e.write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    e.write('fit-report.json',dict(heads=len(fits),rows=len(q),player_walkthrough_status='pending',protected_outcomes_used=False,
        paired_distribution_preserved=True,calibration_established=False))


if __name__=='__main__':main()
