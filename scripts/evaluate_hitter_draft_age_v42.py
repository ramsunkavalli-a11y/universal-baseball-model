"""One representation change, same PA/rate estimands and fixed learners."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
import prepare_hitter_draft_age_v42 as e
from fit_practical_hitter_v31 import tree,weights
from universal_baseball.storage import sha256_file


def main():
    pre=e.r.read(e.OUT/'preflight.json');review=e.r.read(e.OUT/'source-review.json')
    assert review['source_walkthrough_status']=='complete'
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(e.OUT/'features.parquet');base=pl.read_parquet(e.base.OUT/'predictions.parquet');cols=pre['features'];frames=[];fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=e.OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=e.r.read(e.OUT/f'fit-{y}-{k}.json');assert sha256_file(path)==note['prediction_sha256']
                for n in note['models']:assert sha256_file(Path(n['path']))==n['sha256']
                frames.append(pl.read_parquet(path));fits.extend(note['models']);continue
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id');te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert te['row_id'].equals(q['row_id']);notes=[]
            for metric in ['pa','rate']:
                sub=tr if metric=='pa' else tr.filter(pl.col('next_pa')>0)
                w=weights(sub)
                if metric=='rate':w=w*sub['next_pa'].to_numpy();w*=len(w)/w.sum()
                x=sub.select(cols).to_numpy() if metric=='pa' else e.scale.safe_matrix(sub,cols)
                z=te.select(cols).to_numpy() if metric=='pa' else e.scale.safe_matrix(te,cols)
                model=tree() if metric=='pa' else Ridge(alpha=100)
                model.fit(x,sub['next_'+('pa' if metric=='pa' else 'batting_rate')].to_numpy(),sample_weight=w)
                artifact=e.OUT/f'draft-age-{metric}-{y}-{k}.joblib';joblib.dump(model,artifact,compress=3)
                raw=model.predict(z);assert np.isfinite(raw).all();pred=raw.copy()
                if metric=='pa':pred=np.clip(pred,0,800);pred[te['hard_unavailable'].to_numpy()]=0
                q=q.with_columns(pl.Series('draft_age_'+metric,pred));notes.append(dict(metric=metric,path=str(artifact),
                    sha256=sha256_file(artifact),training_rows=len(sub),training_players=sub['player_id'].n_unique(),
                    maximum_target_year=int(sub['target_year'].max()),clipped_rows=int(((raw<0)|(raw>800)).sum()) if metric=='pa' else 0))
            q=q.with_columns((pl.col('draft_age_pa')*(pl.col('draft_age_rate')/600+pl.col('origin_replacement_rate'))).alias('draft_age_value'),
                pl.col('draft_age_pa').alias('age_pa_only_pa'),pl.col('cohort_rate').alias('age_pa_only_rate'),
                pl.col('cohort_pa').alias('age_rate_only_pa'),pl.col('draft_age_rate').alias('age_rate_only_rate'))
            q=q.with_columns((pl.col('age_pa_only_pa')*(pl.col('age_pa_only_rate')/600+pl.col('origin_replacement_rate'))).alias('age_pa_only_value'),
                (pl.col('age_rate_only_pa')*(pl.col('age_rate_only_rate')/600+pl.col('origin_replacement_rate'))).alias('age_rate_only_value'))
            q.write_parquet(path);e.write(f'fit-{y}-{k}.json',dict(models=notes,prediction_sha256=sha256_file(path)));fits.extend(notes);frames.append(q)
            print(f'{y}/{k}: {len(q)} paired forecasts',flush=True)
    q=pl.concat(frames).sort('row_id');assert q.select(base.columns).equals(base.sort('row_id'))
    q.write_parquet(e.OUT/'predictions.parquet');e.write('fits.json',fits)
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    e.write('fit-report.json',dict(heads=len(fits),rows=len(q),player_walkthrough_status='pending',protected_outcomes_used=False))


if __name__=='__main__':main()
