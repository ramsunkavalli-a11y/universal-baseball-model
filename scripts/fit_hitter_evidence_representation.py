"""Two fixed talent representations with one common pair of job heads per cell."""
from pathlib import Path

import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
from prepare_hitter_evidence_representation import ROOT,GEN,OUT,OLD,read,save


def verify(mapping):
    for p,h in mapping.items():
        assert sha256_file(Path(p))==h,p


def main():
    pre=read(OUT/'preflight.json'); verify(pre['source_hashes'])
    review=read(OUT/'source-review.json')
    assert review['source_player_walkthrough_status']=='complete'
    assert review['approved_for_fixed_development_fit'] and not review['deployment_approved']
    verify(review['hashes'])
    assert pre['before_fitting'] and pre['checks_before_fits']==140
    assert not (OUT/'fit-report.json').exists(),'Preserve a completed experiment'
    seal=dict(runner_sha256=sha256_file(Path(__file__)),preflight_sha256=sha256_file(OUT/'preflight.json'),
              source_review_sha256=sha256_file(OUT/'source-review.json'))
    if (OUT/'fit-seal.json').exists():assert read(OUT/'fit-seal.json')==seal
    else:save('fit-seal.json',seal)
    previous=pl.read_parquet(OLD/'predictions.parquet')
    forecasts=[]; receipts=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold']; path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=read(OUT/f'fit-{y}-{k}.json');verify(note['hashes'])
                forecasts.append(pl.read_parquet(path));receipts.append(note);continue
            f=pl.read_parquet(OUT/f'features-{k}.parquet')
            tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            active=tr.filter(pl.col('next_pa')>0)
            q=previous.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert te['row_id'].equals(q['row_id'])
            heads=[]; hashes={}; job={}
            for head,sub,cls,target in [('participation',tr,HistGradientBoostingClassifier,'next_active'),
                                       ('conditional_pa',active,HistGradientBoostingRegressor,'next_pa')]:
                names=pre['job_features'];m=cls(**pre['settings'])
                m.fit(sub.select(names).to_numpy(),sub[target].to_numpy(),sample_weight=weights(sub))
                x=te.select(names).to_numpy()
                job[head]=m.predict_proba(x)[:,1] if head=='participation' else m.predict(x)
                p=OUT/f'common-{head}-{y}-{k}.joblib';assert not p.exists();joblib.dump(m,p,compress=3)
                hashes[str(p)]=sha256_file(p)
                heads.append(dict(head=head,arm='common',path=str(p),sha256=hashes[str(p)],features=names,
                                  training_rows=sub.height,training_people=sub['player_id'].n_unique(),target=target))
            prob=job['participation'].copy()
            prob[(te['status_hard_unavailable'].to_numpy()>0)|(te['status_retired'].to_numpy()>0)]=0
            conditional=np.clip(job['conditional_pa'],1,800);pa=prob*conditional
            w=weights(active)*active['next_pa'].to_numpy();w*=len(w)/w.sum()
            for arm,names in pre['arms'].items():
                m=Ridge(alpha=pre['ridge_alpha'])
                m.fit(safe_matrix(active,names),active['actual_relative_rate'].to_numpy(),sample_weight=w)
                rate=m.predict(safe_matrix(te,names));assert np.isfinite(rate).all()
                p=OUT/f'repaired-{arm}-rate-{y}-{k}.joblib';assert not p.exists();joblib.dump(m,p,compress=3)
                hashes[str(p)]=sha256_file(p)
                heads.append(dict(head='rate',arm=arm,path=str(p),sha256=hashes[str(p)],features=names,
                                  training_rows=active.height,training_people=active['player_id'].n_unique(),target='actual_relative_rate'))
                name='repaired_'+arm
                q=q.with_columns(pl.Series(name+'_raw_p',job['participation']),pl.Series(name+'_p',prob),
                    pl.Series(name+'_raw_conditional_pa',job['conditional_pa']),pl.Series(name+'_conditional_pa',conditional),
                    pl.Series(name+'_pa',pa),pl.Series(name+'_rate',rate),
                    pl.Series(name+'_value',pa*(rate/600+te['integration_replacement_rate'].to_numpy())))
                q=q.with_columns((pl.col(name+'_pa')*(pl.col('current_rate')/600+pl.col('origin_replacement_rate'))).alias(name+'_workload_only_value'),
                    (pl.col('current_pa')*(pl.col(name+'_rate')/600+pl.col('origin_replacement_rate'))).alias(name+'_talent_only_value'))
            assert q['repaired_domestic_pa'].equals(q['repaired_overseas_pa'])
            assert np.isfinite(q.select([n for n in q.columns if n.startswith('repaired_')]).to_numpy()).all()
            q.write_parquet(path);hashes[str(path)]=sha256_file(path)
            note=dict(origin=y,fold=k,heads=heads,hashes=hashes,
                      preflight_sha256=seal['preflight_sha256'],maximum_training_target_year=int(tr['target_year'].max()))
            save(f'fit-{y}-{k}.json',note);receipts.append(note);forecasts.append(q)
            print(f'{y}/{k}: common jobs and two fixed talent heads saved; no subgroup selection.',flush=True)
    q=pl.concat(forecasts).sort('row_id')
    assert q.height==30519 and q['row_id'].equals(previous.sort('row_id')['row_id'])
    assert q.select(previous.columns).equals(previous.sort('row_id'))
    q.write_parquet(OUT/'predictions.parquet')
    save('fit-report.json',dict(cells=receipts,new_heads=140,rows=30519,
        predictions_sha256=sha256_file(OUT/'predictions.parquet'),player_walkthrough_status='pending',
        protected_outcomes_used=False,deployment_approved=False,broad_goal_achieved=False))


if __name__=='__main__':main()
