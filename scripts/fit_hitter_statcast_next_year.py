"""Fixed direct MLB rate comparison, with exact untracked-current fallback."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
import prepare_hitter_statcast_next_year as prep


def main():
    out=prep.OUT; pre=prep.read(out/'preflight.json')
    assert not (out/'fit-report.json').exists(),'Do not restart completed comparison'
    for p,h in pre['input_hashes'].items(): assert sha256_file(Path(p))==h,p
    f=pl.read_parquet(out/'features.parquet'); current=pl.read_parquet(pre['current_anchor']); records=[]
    base_names=pre['arms']['ridge_coverage'][:199]; predictions=[]
    with threadpool_limits(limits=2):
        for cell in pre['cells']:
            y,k=cell['year'],cell['fold']; receipt=out/f'fit-{y}-{k}.json'
            if receipt.exists():
                note=prep.read(receipt)
                assert note['runner_sha256']==sha256_file(Path(__file__)) and note['preflight_sha256']==sha256_file(out/'preflight.json')
                for head in note['heads']: assert sha256_file(Path(head['path']))==head['sha256']
                assert sha256_file(Path(note['predictions_path']))==note['predictions_sha256']
                records.append(note);predictions.append(pl.read_parquet(note['predictions_path']));continue
            train=f.filter(pl.col('row_id').is_in(cell['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
            test=f.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
            q=current.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
            assert test['row_id'].equals(q['row_id'])
            old=prep.read(prep.ROOT/f'reports/generated/practical-hitter-numeric-repair-v53/fit-{y}-{k}.json')
            saved=next(h for h in old['heads'] if h['head']=='rate')
            assert sha256_file(Path(saved['path']))==saved['sha256']
            replay=joblib.load(saved['path']).predict(safe_matrix(test,base_names))
            assert np.allclose(replay,q['preseason_rate'].to_numpy(),atol=1e-10,rtol=0),'Anchor replay failed'
            w=weights(train)*train['next_pa'].to_numpy(); w*=len(w)/w.sum()
            assert train['target_year'].max()<=y and not set(train['player_id'])&set(test['player_id'])
            tracked=test['sc_tracked'].to_numpy(); heads=[]
            q=q.with_columns(test['sc_tracked'],test['sc_own_ev_n'],test['sc_own_pair_n'])
            for arm,names in pre['arms'].items():
                model=Ridge(alpha=pre['ridge_alpha']) if arm.startswith('ridge') else HistGradientBoostingRegressor(**pre['hist_settings'])
                x=safe_matrix(train,names); tx=safe_matrix(test,names)
                model.fit(x,train['next_batting_rate'].to_numpy(),sample_weight=w)
                raw=model.predict(tx); rate=np.where(tracked,raw,q['preseason_rate'].to_numpy())
                assert np.isfinite(rate).all() and np.array_equal(rate[~tracked],q['preseason_rate'].to_numpy()[~tracked])
                path=out/f'{arm}-{y}-{k}.joblib'; assert not path.exists(); joblib.dump(model,path,compress=3)
                assert np.allclose(joblib.load(path).predict(tx),raw,atol=1e-12,rtol=0)
                q=q.with_columns(pl.Series(arm+'_raw_rate',raw),pl.Series(arm+'_rate',rate))
                q=q.with_columns((pl.col('preseason_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
                assert np.allclose(q.filter(~pl.col('sc_tracked'))[arm+'_value'],q.filter(~pl.col('sc_tracked'))['preseason_value'],atol=1e-12,rtol=0)
                heads.append(dict(arm=arm,path=str(path),sha256=sha256_file(path),training_rows=len(train),
                    training_players=train['player_id'].n_unique(),max_target_year=int(train['target_year'].max()),features=names))
            path=out/f'forecast-{y}-{k}.parquet'; q.write_parquet(path)
            note=dict(year=y,fold=k,heads=heads,predictions_path=str(path),predictions_sha256=sha256_file(path),
                preflight_sha256=sha256_file(out/'preflight.json'),runner_sha256=sha256_file(Path(__file__)),
                saved_anchor_sha256=saved['sha256'],weight_sha256=__import__('hashlib').sha256(w.tobytes()).hexdigest())
            prep.write(f'fit-{y}-{k}.json',note);records.append(note);predictions.append(q)
            print(f'{y}/{k}: four fixed rate heads; current anchor replayed; exact untracked fallback.',flush=True)
    combined=pl.concat(predictions).sort('row_id'); assert combined['row_id'].equals(current.sort('row_id')['row_id'])
    combined.write_parquet(out/'predictions.parquet')
    prep.write('fit-report.json',dict(cells=records,heads=140,forecasts=30506,playing_time_unchanged=True,
        untracked_forecasts_unchanged=True,protected_outcomes_used=False,player_walkthrough_status='pending',
        predictive_validation=False,deployment_approved=False,predictions_sha256=sha256_file(out/'predictions.parquet')))


if __name__=='__main__':main()
