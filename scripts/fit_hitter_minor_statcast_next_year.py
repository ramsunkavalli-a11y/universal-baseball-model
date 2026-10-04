"""Two fixed regularized heads, with qualified context routing and exact fallback."""
from pathlib import Path
import hashlib
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_minor_statcast_forecast import route
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
import prepare_hitter_minor_statcast_next_year as prep


def main():
    out = prep.OUT; pre = prep.read(out/'preflight.json')
    assert not (out/'fit-report.json').exists(), 'Do not restart a completed comparison'
    prep.verify_hashes(pre['input_hashes'])
    anchor = pl.read_parquet(out/'anchor.parquet').sort('row_id')
    records, predictions = [], []
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y, k = c['year'], c['fold']; receipt = out/f'fit-{y}-{k}.json'
            if receipt.exists():
                n = prep.read(receipt)
                assert n['runner_sha256'] == sha256_file(Path(__file__))
                assert n['preflight_sha256'] == sha256_file(out/'preflight.json')
                prep.verify_hashes(n['output_hashes'])
                records.append(n); predictions.append(pl.read_parquet(n['predictions_path'])); continue
            f = pl.read_parquet(out/f'features-{k}.parquet')
            tr, te, context, disabled = route(f,c['training_row_ids'],c['test_row_ids'],pre['minimum_context_people'])
            assert context == c['league_context'] and disabled == c['disabled_features']
            q = anchor.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
            assert q['row_id'].equals(te['row_id'])
            eligible = te['msc_eligible'].to_numpy()
            q = q.with_columns(te['msc_eligible'],te['msc_own_ev_n'])
            w = weights(tr)*tr['next_pa'].to_numpy(); w *= len(w)/w.sum()
            heads, hashes = [], {}
            for arm, names in pre['arms'].items():
                # No effect is available in early cells; do not manufacture a
                # pointless model or extrapolate from absent source contexts.
                raw = q['combined_rate'].to_numpy().copy()
                if eligible.any():
                    model = Ridge(alpha=pre['ridge_alpha'])
                    model.fit(safe_matrix(tr,names),tr['next_batting_rate'].to_numpy(),sample_weight=w)
                    raw = model.predict(safe_matrix(te,names))
                    path = out/f'{arm}-{y}-{k}.joblib'; assert not path.exists()
                    joblib.dump(model,path,compress=3); hashes[str(path)] = sha256_file(path)
                    assert np.allclose(joblib.load(path).predict(safe_matrix(te,names)),raw,atol=1e-12,rtol=0)
                    heads.append(dict(arm=arm,path=str(path),sha256=hashes[str(path)],features=names,
                        training_rows=len(tr),training_people=tr['player_id'].n_unique(),max_target_year=int(tr['target_year'].max())))
                rate = np.where(eligible,raw,q['combined_rate'].to_numpy())
                assert np.isfinite(rate).all() and np.array_equal(rate[~eligible],q['combined_rate'].to_numpy()[~eligible])
                value = q['preseason_pa'].to_numpy()*(rate/600+q['origin_replacement_rate'].to_numpy())
                # Keep the identical stored fallback, avoiding roundoff changes.
                value[~eligible] = q['combined_value'].to_numpy()[~eligible]
                q = q.with_columns(pl.Series(arm+'_raw_rate',raw),pl.Series(arm+'_rate',rate),pl.Series(arm+'_value',value))
            path = out/f'forecast-{y}-{k}.parquet'; assert not path.exists(); q.write_parquet(path)
            hashes[str(path)] = sha256_file(path)
            n = dict(year=y,fold=k,heads=heads,predictions_path=str(path),output_hashes=hashes,
                preflight_sha256=sha256_file(out/'preflight.json'),runner_sha256=sha256_file(Path(__file__)),
                weight_sha256=hashlib.sha256(w.tobytes()).hexdigest(),eligible_rows=int(eligible.sum()),
                no_fit_exact_fallback=not eligible.any())
            prep.write(receipt.name,n); records.append(n); predictions.append(q)
            print(f'{y}/{k}: {len(heads)} heads; {int(eligible.sum())} eligible, others exact combined fallback.',flush=True)
    q = pl.concat(predictions).sort('row_id'); assert q.select(anchor.columns).equals(anchor)
    q.write_parquet(out/'predictions.parquet')
    prep.write('fit-report.json',dict(cells=records,heads=sum(len(r['heads']) for r in records),forecasts=len(q),
        playing_time_unchanged=True,all_fallbacks_exact=True,player_walkthrough_status='pending',
        predictive_validation=False,deployment_approved=False,protected_outcomes_used=False,
        predictions_sha256=sha256_file(out/'predictions.parquet')))


if __name__ == '__main__':
    main()
