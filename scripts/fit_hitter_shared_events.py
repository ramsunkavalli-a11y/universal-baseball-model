"""Two fixed shared event heads, preserving the incumbent's MLB route and PA."""
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
from prepare_hitter_shared_events import OUT,PREVIOUS,read,save,verify


def main():
    pre=read(OUT/'preflight.json');verify(pre['input_hashes'])
    review=read(OUT/'source-review.json');verify(review['hashes'])
    assert review['source_player_walkthrough_status']=='complete' and review['approved_for_fixed_fit']
    assert not (OUT/'fit-report.json').exists(),'Preserve completed fits'
    save('fit-seal.json',dict(preflight_sha256=sha256_file(OUT/'preflight.json'),source_review_sha256=sha256_file(OUT/'source-review.json')))
    previous=pl.read_parquet(PREVIOUS/'predictions.parquet').sort('row_id')
    frames={(a,k):pl.read_parquet(OUT/f'{a}-features-{k}.parquet') for a in pre['arms'] for k in range(5)}
    forecasts=[];receipts=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];q=previous.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            heads=[];hashes={}
            for a in pre['arms']:
                f=frames[a,k];tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
                te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                assert te['row_id'].equals(q['row_id'])
                w=weights(tr)*tr['next_pa'].to_numpy();w*=len(w)/w.sum()
                m=Ridge(alpha=pre['ridge_alpha']);m.fit(safe_matrix(tr,pre['names']),tr['actual_relative_rate'].to_numpy(),sample_weight=w)
                raw=m.predict(safe_matrix(te,pre['names']))
                addition=q['source_addition'].to_numpy()
                rate=np.where((te['prior_debut'].to_numpy()==0)|addition,raw,q['current_rate'].to_numpy())
                assert np.isfinite(rate).all()
                pa=np.where(addition,q['repaired_domestic_pa'].to_numpy(),q['current_pa'].to_numpy())
                prob=np.where(addition,q['repaired_domestic_p'].to_numpy(),q['current_p'].to_numpy())
                conditional=np.where(addition,q['repaired_domestic_conditional_pa'].to_numpy(),q['current_conditional_pa'].to_numpy())
                name='shared_'+a
                q=q.with_columns(pl.Series(name+'_raw_rate',raw),pl.Series(name+'_rate',rate),pl.Series(name+'_pa',pa),
                    pl.Series(name+'_p',prob),pl.Series(name+'_conditional_pa',conditional),
                    pl.Series(name+'_value',pa*(rate/600+te['origin_replacement_rate'].to_numpy())))
                path=OUT/f'{a}-rate-{y}-{k}.joblib';assert not path.exists();joblib.dump(m,path,compress=3)
                hashes[str(path)]=sha256_file(path)
                heads.append(dict(arm=a,path=str(path),sha256=hashes[str(path)],training_rows=tr.height,training_people=tr['player_id'].n_unique(),maximum_target_year=int(tr['target_year'].max())))
            pp=OUT/f'forecast-{y}-{k}.parquet';q.write_parquet(pp);hashes[str(pp)]=sha256_file(pp)
            note=dict(origin=y,fold=k,heads=heads,hashes=hashes);save(f'fit-{y}-{k}.json',note)
            forecasts.append(q);receipts.append(note)
            print(f'{y}/{k}: two talent heads; original playing time and MLB routing unchanged.',flush=True)
    q=pl.concat(forecasts).sort('row_id');assert q['row_id'].equals(previous['row_id']) and q.select(previous.columns).equals(previous)
    q.write_parquet(OUT/'predictions.parquet')
    save('fit-report.json',dict(cells=receipts,heads=70,rows=q.height,predictions_sha256=sha256_file(OUT/'predictions.parquet'),
        protected_outcomes_used=False,player_walkthrough_status='pending',deployment_approved=False))


if __name__=='__main__':main()
