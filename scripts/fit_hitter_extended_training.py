"""Two fixed training-history arms; preserve anchors and actual saved heads."""
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
from prepare_hitter_extended_training import ROOT,OUT,CURRENT,read,write,verify


def fit():
    pre = read(OUT/'preflight.json')
    verify(pre['input_hashes'])
    assert pre['checks_before_fits']==210
    f = pl.read_parquet(OUT/'features.parquet')
    anchor = pl.read_parquet(CURRENT/'scored-predictions.parquet').sort('row_id')
    assert len(anchor)==30506
    fits = []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k = c['year'],c['fold']
            pp = OUT/f'forecast-{y}-{k}.parquet'
            if pp.exists():
                note = read(OUT/f'fit-{y}-{k}.json')
                verify({str(pp):note['prediction_sha256'],**{h['path']:h['sha256'] for h in note['heads']}})
                fits.append(note)
                continue
            te = f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert te['row_id'].equals(q['row_id'])
            assert te['next_pa'].equals(q['next_pa'])
            heads = []
            for arm in ['restricted','extended']:
                tr = f.filter(pl.col('row_id').is_in(c['training_row_ids'][arm])).sort('row_id')
                active = tr.filter(pl.col('next_pa')>0)
                pred = {}
                for head,sub,names in [('participation',tr,pre['pa_features']),('conditional_pa',active,pre['pa_features']),('rate',active,pre['rate_features'])]:
                    mp = OUT/f'{arm}-{head}-{y}-{k}.joblib'
                    hp = OUT/f'{arm}-{head}-{y}-{k}.json'
                    target = 'next_active' if head=='participation' else 'next_pa' if head=='conditional_pa' else 'next_batting_rate'
                    if hp.exists():
                        note = read(hp)
                        verify({str(mp):note['sha256']})
                        model = joblib.load(mp)
                    else:
                        assert not mp.exists(), 'Unsealed saved head needs explicit recovery, not silent refit'
                        model = Ridge(alpha=100) if head=='rate' else (HistGradientBoostingClassifier if head=='participation' else HistGradientBoostingRegressor)(**pre['settings'])
                        w = weights(sub)
                        if head=='rate':
                            w *= sub['next_pa'].to_numpy()
                            w *= len(w)/w.sum()
                        x = safe_matrix(sub,names) if head=='rate' else sub.select(names).to_numpy()
                        model.fit(x,sub[target].to_numpy(),sample_weight=w)
                        joblib.dump(model,mp,compress=3)
                        note = dict(arm=arm,head=head,path=str(mp),sha256=sha256_file(mp),features=names,
                            training_rows=len(sub),training_people=sub['player_id'].n_unique(),
                            min_target_year=int(sub['target_year'].min()),max_target_year=int(sub['target_year'].max()))
                        write(hp.name,note)
                    x = safe_matrix(te,names) if head=='rate' else te.select(names).to_numpy()
                    pred[head] = model.predict_proba(x)[:,1] if head=='participation' else model.predict(x)
                    assert np.isfinite(pred[head]).all()
                    heads.append(note)
                p = pred['participation'].copy()
                p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()] = 0
                cond = np.clip(pred['conditional_pa'],1,800)
                q = q.with_columns(pl.Series(arm+'_raw_p',pred['participation']),pl.Series(arm+'_p',p),
                    pl.Series(arm+'_raw_conditional_pa',pred['conditional_pa']),pl.Series(arm+'_conditional_pa',cond),
                    pl.Series(arm+'_pa',p*cond),pl.Series(arm+'_rate',pred['rate']))
                q = q.with_columns((pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'),
                    (pl.col(arm+'_pa')*(pl.col('baseline_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_pa_only_value'),
                    pl.col(arm+'_pa').alias(arm+'_pa_only_pa'),
                    (pl.col('preseason_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_rate_only_value'),
                    pl.col('preseason_pa').alias(arm+'_rate_only_pa'))
            assert q.select(anchor.columns).equals(anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id'))
            q.write_parquet(pp)
            note = dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(pp))
            write(f'fit-{y}-{k}.json',note)
            fits.append(note)
            print(f'Matched training histories {y}/{k}: six heads saved; anchors exact.',flush=True)
    q = pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert q.select(anchor.columns).equals(anchor)
    q.write_parquet(OUT/'predictions.parquet')
    write('fits.json',fits)
    write('fit-report.json',dict(heads=210,old_columns_exact=True,player_walkthrough_status='pending',
        protected_outcomes_used=False,frozen_forecast_changed=False,deployment_approved=False))


if __name__=='__main__':
    fit()
