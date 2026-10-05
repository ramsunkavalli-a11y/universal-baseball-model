"""Fit the 25 predeclared production heads, preserving every intermediate."""
from pathlib import Path
import json
import hashlib
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
from prepare_hitter_production_2026 import ROOT,OUT,read,write


def main():
    pre=read(OUT/'preflight.json');assert pre['before_fitting'] and pre['source_integrity_pass'] and not pre['protected_outcomes_used']
    assert not (OUT/'fit-report.json').exists(),'Preserve completed production fits'
    for kind in ['input_hashes','output_hashes']:
        for p,h in pre[kind].items():assert sha256_file(Path(p))==h,p
    seal_path=OUT/'fit-execution-seal.json';seal=dict(preflight_sha256=sha256_file(OUT/'preflight.json'),
        runner_sha256=sha256_file(Path(__file__)),before_fitting=True,protected_outcomes_used=False)
    if seal_path.exists():assert read(seal_path)==seal
    else:write(seal_path,seal)
    modern=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet')
    tracking=pl.read_parquet(ROOT/'reports/generated/hitter-statcast-next-year/features.parquet')
    receipts=[]
    with threadpool_limits(limits=2):
        for cell in pre['cells']:
            fold=cell['fold'];receipt=OUT/f'fit-{fold}.json';output=OUT/f'forecast-{fold}.parquet'
            if receipt.exists():
                r=read(receipt);assert r['execution_seal']==seal and sha256_file(output)==r['forecast_sha256']
                for h in r['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                receipts.append(r);continue
            assert not output.exists(),'Unreceipted forecast file'
            q=pl.read_parquet(OUT/f'inputs-{fold}.parquet').sort('row_id')
            transit=pl.read_parquet(ROOT/f'reports/generated/hitter-talent-bridge-v74/features-{fold}.parquet')
            tr=modern.filter(pl.col('row_id').is_in(cell['training_row_ids'])).sort('row_id')
            active=tr.filter(pl.col('row_id').is_in(cell['active_training_row_ids'])).sort('row_id')
            frame=dict(participation=tr,conditional_pa=active,rate_numeric=active,
                rate_tracking=tracking.filter(pl.col('row_id').is_in(cell['active_training_row_ids'])).sort('row_id'),
                rate_prospect=transit.filter(pl.col('row_id').is_in(cell['active_training_row_ids'])).sort('row_id'))
            predictions={};heads=[]
            for head in pre['features']:
                train=frame[head];names=pre['features'][head];is_rate=head.startswith('rate');w=weights(train)
                if is_rate:w*=train['next_pa'].to_numpy();w*=len(w)/w.sum()
                note=next(h for h in cell['heads'] if h['head']==head)
                assert hashlib.sha256(w.astype('<f8').tobytes()).hexdigest()==note['weight_sha256']
                assert train['row_id'].to_list()==note['training_row_ids']
                assert not set(train['player_id'])&set(q['player_id'])
                model=Ridge(alpha=100) if is_rate else (HistGradientBoostingClassifier if head=='participation'
                    else HistGradientBoostingRegressor)(**pre['histogram_settings'])
                x=safe_matrix(train,names) if is_rate else train.select(names).to_numpy()
                tx=safe_matrix(q,names) if is_rate else q.select(names).to_numpy()
                target='next_batting_rate' if is_rate else 'next_active' if head=='participation' else 'next_pa'
                model.fit(x,train[target].to_numpy(),sample_weight=w)
                pred=model.predict_proba(tx)[:,1] if head=='participation' else model.predict(tx)
                assert np.isfinite(pred).all();predictions[head]=pred
                mp=OUT/f'{head}-{fold}.joblib';assert not mp.exists(),'Unreceipted model'
                joblib.dump(model,mp,compress=3)
                replay=joblib.load(mp).predict_proba(tx)[:,1] if head=='participation' else joblib.load(mp).predict(tx)
                assert np.allclose(pred,replay,rtol=0,atol=1e-12)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),target=target,features=names,
                    training_rows=len(train),training_people=train['player_id'].n_unique(),weight_sha256=note['weight_sha256']))
                print(f'Fold {fold}: {head} fitted and saved-head replay matches.',flush=True)
            raw_p=predictions['participation'];assert (raw_p>=0).all() and (raw_p<=1).all()
            override=q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()
            p=np.where(override,0.,raw_p);cond=np.clip(predictions['conditional_pa'],1,800);pa=p*cond
            prospect=q['prior_debut'].to_numpy()==0;tracked=q['sc_tracked'].to_numpy()
            rate=np.where(prospect,predictions['rate_prospect'],np.where(tracked,predictions['rate_tracking'],predictions['rate_numeric']))
            route=np.where(prospect,'translated_prospect',np.where(tracked,'measured_MLB','numeric_MLB'))
            value=pa*(rate/600+pre['origin_replacement_reference'])
            q=q.with_columns(*[pl.Series('raw_'+h,v) for h,v in predictions.items()],pl.Series('participation_probability',p),
                pl.Series('conditional_pa',cond),pl.Series('expected_pa',pa),pl.Series('hitting_wins_per_600',rate),
                pl.Series('batting_contribution',value),pl.Series('talent_route',route),pl.Series('participation_override',override))
            assert not any(c.startswith('next_') for c in q.columns)
            q.write_parquet(output)
            r=dict(fold=fold,execution_seal=seal,heads=heads,forecast_path=str(output),forecast_sha256=sha256_file(output),
                forecast_rows=len(q),protected_outcomes_used=False,candidate_frozen=False)
            write(receipt,r);receipts.append(r)
    forecast=pl.concat([pl.read_parquet(OUT/f'forecast-{c["fold"]}.parquet') for c in pre['cells']]).sort('row_id')
    assert len(forecast)==4030 and forecast['row_id'].n_unique()==4030
    forecast.write_parquet(OUT/'forecast.parquet')
    write(OUT/'fit-report.json',dict(heads_fitted=25,folds=receipts,forecast_population=4030,
        model_replays_pass=True,independent_replay_pending=True,player_walkthrough_status='pending',
        candidate_frozen=False,protected_outcomes_used=False,forecast_sha256=sha256_file(OUT/'forecast.parquet'),
        qualification=pre['coverage'],universal_coverage_claim_allowed=False,
        expected_pa_total=float(forecast['expected_pa'].sum()),batting_contribution_total=float(forecast['batting_contribution'].sum())))


if __name__=='__main__':main()
