"""Two locked rate heads; exact workload and unsupported forecast fallbacks."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
import prepare_hitter_contact_v41 as e
import prepare_practical_hitter_v33 as scale
from fit_practical_hitter_v31 import tree,weights
from universal_baseball.hitter_contact_transfer import scaled
from universal_baseball.storage import sha256_file

OUT=e.OUT


def matrix(f,pre,arm):
    return scaled(f,pre['old_features'],pre['added_features'],scale.safe_matrix) if arm=='contact_ridge' else f.select(pre['old_features']+pre['added_features']).to_numpy()


def main():
    pre=e.r.read(OUT/'preflight.json');review=e.r.read(OUT/'source-review.json');assert review['source_walkthrough_status']=='complete'
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(e.base.OUT/'predictions.parquet');frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=e.r.read(OUT/f'fit-{y}-{k}.json');assert sha256_file(path)==note['prediction_sha256']
                for n in note['models']:assert sha256_file(Path(n['path']))==n['sha256']
                frames.append(pl.read_parquet(path));fits.extend(note['models']);continue
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert te['row_id'].equals(q['row_id']);usable=te['row_id'].is_in(c['supported_test_row_ids']).to_numpy();notes=[]
            w=weights(tr)*tr['next_pa'].to_numpy();w*=len(w)/w.sum()
            for arm in ['contact_ridge','contact_hist']:
                pred=q['cohort_rate'].to_numpy().copy()
                if usable.any():
                    model=Ridge(alpha=100) if arm=='contact_ridge' else tree();model.fit(matrix(tr,pre,arm),tr['next_batting_rate'].to_numpy(),sample_weight=w)
                    artifact=OUT/f'{arm}-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
                    raw=model.predict(matrix(te,pre,arm));assert np.isfinite(raw).all();pred[usable]=raw[usable]
                    notes.append(dict(arm=arm,path=str(artifact),sha256=sha256_file(artifact),training_rows=len(tr),training_players=tr['player_id'].n_unique(),
                        maximum_target_year=int(tr['target_year'].max()),supported_test_rows=int(usable.sum())))
                q=q.with_columns(pl.Series(arm+'_rate',pred),pl.col('cohort_pa').alias(arm+'_pa')).with_columns(
                    (pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
            q=q.with_columns(pl.Series('contact_supported',usable));q.write_parquet(path)
            e.write(f'fit-{y}-{k}.json',dict(models=notes,prediction_sha256=sha256_file(path)));fits.extend(notes);frames.append(q)
            print(f'{y}/{k}: {int(usable.sum())} supported, {len(q)-int(usable.sum())} exact fallbacks',flush=True)
    q=pl.concat(frames).sort('row_id');assert q.select(base.columns).equals(base.sort('row_id'))
    q.write_parquet(OUT/'predictions.parquet');e.write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    e.write('fit-report.json',dict(heads=len(fits),rows=len(q),supported_rows=int(q['contact_supported'].sum()),workload_bit_exact=True,
        player_walkthrough_status='pending',protected_outcomes_used=False))


if __name__=='__main__':main()
