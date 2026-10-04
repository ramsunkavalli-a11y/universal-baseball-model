"""Fit locked nested heads and one active dispersion; keep all current means."""
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_workload_risk import fit_concentration, mixture_pmf, distribution_terms
from fit_practical_hitter_v31 import weights
import prepare_hitter_workload_risk as setup

ROOT,OUT=setup.ROOT,setup.OUT


def read(path):return json.loads(path.read_text(encoding='utf8'))


def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf8')


def main():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    paths=[Path(__file__),ROOT/'src/universal_baseball/hitter_workload_risk.py',ROOT/'tests/test_hitter_workload_risk.py',OUT/'preflight.json']
    seal={str(p):sha256_file(p) for p in paths}
    if (OUT/'fit-seal.json').exists():assert read(OUT/'fit-seal.json')==seal
    else:write('fit-seal.json',seal)
    f=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet')
    q=pl.read_parquet(ROOT/'reports/generated/hitter-preseason-readiness-v68/scored-predictions.parquet')
    names=pre['features'];notes=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];final_path=OUT/f'forecast-{y}-{k}.parquet'
            if final_path.exists():
                note=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(final_path)==note['forecast_sha256'];notes.append(note);continue
            nested=[];heads=[]
            for i in c['nested']:
                origin=i['origin'];tag=f'inner-{k}-{origin}';mp=OUT/(tag+'.joblib');vp=OUT/(tag+'.parquet');npth=OUT/(tag+'.json')
                tr=f.filter(pl.col('row_id').is_in(i['training_row_ids'])).sort('row_id')
                val=f.filter(pl.col('row_id').is_in(i['validation_row_ids'])).sort('row_id')
                if mp.exists():
                    h=read(npth);assert h['training_row_ids']==i['training_row_ids'] and h['validation_row_ids']==i['validation_row_ids']
                    assert sha256_file(mp)==h['model_sha256'] and sha256_file(vp)==h['prediction_sha256']
                else:
                    m=HistGradientBoostingRegressor(**pre['conditional_settings'])
                    m.fit(tr.select(names).to_numpy(),tr['next_pa'].to_numpy(),sample_weight=weights(tr))
                    raw=m.predict(val.select(names).to_numpy());assert np.isfinite(raw).all()
                    joblib.dump(m,mp,compress=3)
                    val.select('row_id','player_id','origin_year','target_year','outer_fold','next_pa').with_columns(
                        pl.Series('raw_conditional_pa',raw),pl.Series('conditional_pa',np.clip(raw,1,800))).write_parquet(vp)
                    h=dict(origin=origin,outer_fold=k,inner_fold=i['inner_fold'],training_row_ids=i['training_row_ids'],
                        validation_row_ids=i['validation_row_ids'],model_path=str(mp),model_sha256=sha256_file(mp),
                        prediction_path=str(vp),prediction_sha256=sha256_file(vp))
                    write(tag+'.json',h)
                    print(f'Nested {k}/{origin}: {len(tr)} active training rows, {len(val)} held-player forecasts',flush=True)
                nested.append(pl.read_parquet(vp).filter(pl.col('next_pa')>0));heads.append(h)
            calibration=pl.concat(nested).sort('row_id')
            assert set(calibration['row_id'])==set(c['calibration_row_ids'])
            concentration=fit_concentration(calibration['next_pa'].to_numpy(),calibration['conditional_pa'].to_numpy(),weights(calibration))
            cp=OUT/f'calibration-{y}-{k}.parquet';calibration.write_parquet(cp)
            te=q.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id');actual=te['next_pa'].to_numpy()
            p,mean=te['preseason_p'].to_numpy(),te['preseason_conditional_pa'].to_numpy()
            result=te
            for arm,value in [('risk',concentration['concentration']),('binomial',None)]:
                pmf=mixture_pmf(p,mean,value);terms=distribution_terms(pmf,actual)
                result=result.with_columns([pl.Series(arm+'_'+name,v) for name,v in terms.items()])
                assert np.allclose(pmf@np.arange(801),te['preseason_pa'],atol=1e-6,rtol=0)
            assert result.select(q.columns).equals(te)
            result.write_parquet(final_path)
            note=dict(year=y,fold=k,concentration=concentration,nested_heads=heads,calibration_path=str(cp),
                calibration_sha256=sha256_file(cp),forecast_sha256=sha256_file(final_path),
                unchanged_means=True,player_walkthrough_status='pending')
            write(f'fit-{y}-{k}.json',note);notes.append(note)
            print(f'Risk {y}/{k}: concentration {concentration["concentration"]:.5f}, forecasts unchanged',flush=True)
    result=pl.concat([pl.read_parquet(OUT/f'forecast-{c["year"]}-{c["fold"]}.parquet') for c in pre['cells']]).sort('row_id')
    assert result.select(q.columns).equals(q.sort('row_id')) and len(result)==30506
    result.write_parquet(OUT/'predictions.parquet')
    write('fit-report.json',dict(forecasts=len(result),nested_contexts=sum(len(c['nested']) for c in pre['cells']),
        unique_nested_heads=len(list(OUT.glob('inner-*.joblib'))),cells=notes,all_current_forecasts_unchanged=True,
        player_walkthrough_status='pending',predictive_validation='not_scored',protected_outcomes_used=False,
        output_sha256=sha256_file(OUT/'predictions.parquet')))
    print('All fixed distributions saved; statistical and player reviews pending.',flush=True)


if __name__=='__main__':main()
