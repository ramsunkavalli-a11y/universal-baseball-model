"""Two fixed additive rate adjustments; never refit the base talent forecast."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
import prepare_hitter_minor_precision as prep


def main():
    out=prep.OUT;pre=prep.read(out/'preflight.json')
    assert not (out/'fit-report.json').exists(),'Preserve finished fit'
    prep.old.verify_hashes(pre['input_hashes'])
    anchor=pl.read_parquet(out/'anchor.parquet').sort('row_id');forecasts=[];records=[]
    with threadpool_limits(limits=2):
        for k in range(5):
            f=pl.read_parquet(out/f'features-{k}.parquet')
            for c in [c for c in pre['cells'] if c['fold']==k]:
                y=c['year'];tr,te,off=prep.routed(f,c)
                assert off==c['precision_disabled_features']
                bases=pl.read_parquet(c['baseline_path'])
                trainbase=tr.select('row_id').join(bases.filter(pl.col('split')=='train'),on='row_id',validate='1:1')['base_rate'].to_numpy()
                residual=tr['next_batting_rate'].to_numpy()-trainbase
                w=weights(tr)*tr['next_pa'].to_numpy();w*=len(w)/w.sum()
                q=anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                eligible=te['msc_eligible'].to_numpy();heads=[]
                for arm,cols in pre['arms'].items():
                    update=np.zeros(len(te));path=out/f'{arm}-{y}-{k}.joblib'
                    if eligible.any():
                        assert not path.exists()
                        model=Ridge(alpha=pre['ridge_alpha'],fit_intercept=False)
                        model.fit(safe_matrix(tr,cols),residual,sample_weight=w)
                        update=model.predict(safe_matrix(te,cols));joblib.dump(model,path,compress=3)
                        heads.append(dict(arm=arm,path=str(path),sha256=sha256_file(path),features=cols))
                    rate=q['combined_rate'].to_numpy().copy();rate[eligible]+=update[eligible]
                    value=q['preseason_pa'].to_numpy()*(rate/600+q['origin_replacement_rate'].to_numpy())
                    value[~eligible]=q['combined_value'].to_numpy()[~eligible]
                    q=q.with_columns(pl.Series(arm+'_rate',rate),pl.Series(arm+'_value',value),pl.Series(arm+'_raw_update',update))
                path=out/f'forecast-{y}-{k}.parquet';assert not path.exists();q.write_parquet(path)
                receipt=dict(year=y,fold=k,heads=heads,predictions_path=str(path),predictions_sha256=sha256_file(path),
                    runner_sha256=sha256_file(Path(__file__)),eligible_rows=int(eligible.sum()),training_rows=len(tr))
                prep.write(f'fit-{y}-{k}.json',receipt);records.append(receipt);forecasts.append(q)
                print(y,k,'fixed adjustments',len(heads),'eligible',int(eligible.sum()),flush=True)
    q=pl.concat(forecasts).sort('row_id');assert q.select(anchor.columns).equals(anchor)
    q.write_parquet(out/'predictions.parquet')
    prep.write('fit-report.json',dict(cells=records,heads=sum(len(c['heads']) for c in records),
        forecasts=len(q),playing_time_unchanged=True,base_model_unchanged=True,
        predictions_sha256=sha256_file(out/'predictions.parquet'),player_walkthrough_status='pending',deployment_approved=False))


if __name__=='__main__':main()
