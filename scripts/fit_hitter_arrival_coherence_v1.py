"""Fixed rare-event arrival/value challenger, through completed 2025 outcomes."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from universal_baseball.hitter_arrival_coherence import cell_probability, linked_value, scopes
from universal_baseball.hitter_three_year_opportunity import attach_cohorts
from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.six_year_hitter import extend_labels,mature_mask
from universal_baseball.storage import sha256_file

BASE=Path('reports/generated/multiyear-hitter-v1')
PREVIOUS=Path('model_artifacts/hitter-three-year-opportunity-v1-2026-09-22/predictions.parquet')
SIX=Path('model_artifacts/six-year-hitter-v1-2026-09-22')
OLD=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
DEBUT=OLD/'career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet'
OUT=Path('reports/generated/hitter-arrival-coherence-v1')
PLAN=Path('docs/hitter-arrival-coherence-v1-plan.md')


def save(path,data):
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def references():
    early=pl.read_parquet(PREVIOUS).select('origin_year','player_id','horizon',
        pl.col('accepted').alias('old_pa'),pl.col('accepted_p').alias('old_p'),pl.col('delivered').alias('old_value'),
        'ensemble','ensemble_p','ensemble_product')
    late=pl.read_parquet(SIX/'predictions.parquet').filter(pl.col('origin_year')<2025).select('origin_year','player_id','horizon',
        pl.col('expected_pa').alias('old_pa'),pl.col('activity').alias('old_p'),pl.col('direct').alias('old_value'))
    current=pl.read_parquet(SIX/'forecast-2026-2031.parquet')
    now=pl.concat([current.select('origin_year','player_id',pl.lit(h,dtype=pl.Int32).alias('horizon'),
        pl.col(f'expected_pa_h{h}').alias('old_pa'),pl.col(f'activity_h{h}').alias('old_p'),pl.col(f'value_{2025+h}').alias('old_value')) for h in range(1,7)])
    return pl.concat([early,late,now],how='diagonal_relaxed')


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    paths=[PLAN,Path(__file__),Path('src/universal_baseball/hitter_arrival_coherence.py'),BASE/'panel.parquet',BASE/'targets.parquet',BASE/'manifest.json',DEBUT,PREVIOUS,
        SIX/'predictions.parquet',SIX/'forecast-2026-2031.parquet',Path('src/universal_baseball/hitter_model_tournament.py')]
    hashes={str(p):sha256_file(p) for p in paths}
    fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:16]
    cache=OUT/'cache'/fingerprint;cache.mkdir(exist_ok=True,parents=True)
    targets=pl.read_parquet(BASE/'targets.parquet')
    panel=attach_cohorts(extend_labels(pl.read_parquet(BASE/'panel.parquet'),targets),pl.read_parquet(DEBUT),targets)
    features=json.loads((BASE/'manifest.json').read_text())['full_features']
    ref=references(); results=[]; notes=[]
    pairs=sorted(ref.select('origin_year','horizon').unique().iter_rows())
    for cold,folds in [(False,pairs),(True,[(2022,h) for h in (1,2,3)])]:
        for year,h in folds:
            dest=cache/f'{year}-h{h}-cold{int(cold)}.parquet';note_path=dest.with_suffix('.json')
            if dest.exists() and note_path.exists():
                result=pl.read_parquet(dest);note=json.loads(note_path.read_text())
            else:
                test=panel.filter(pl.col('origin_year')==year).sort('player_id')
                mask=mature_mask(panel,year,h,test['player_id'].to_numpy() if cold else ())
                train=panel.filter(pl.Series(mask)); active=train[f'pa_h{h}'].to_numpy()>0
                x=train.select(features).to_numpy(); tx=test.select(features).to_numpy()
                pa_model=make_engine_models('lightgbm',417,'balanced').regressor.set_params(n_jobs=4)
                rate_model=make_engine_models('lightgbm',427,'balanced').regressor.set_params(n_jobs=4)
                ypa=train[f'pa_h{h}'].to_numpy(); yvalue=train[f'war_h{h}'].to_numpy()
                positive=np.clip(pa_model.fit(x[active],ypa[active]).predict(tx),1,750)
                rate=np.clip(rate_model.fit(x[active],600*yvalue[active]/ypa[active],sample_weight=ypa[active]/ypa[active].mean()).predict(tx),-5,10)
                prob,supported,cells=cell_probability(train,test,h)
                # Unsupported rows are carried through exactly, not filled by zero.
                candidate_pa,candidate_value=linked_value(np.nan_to_num(prob),positive,rate)
                result=test.select('origin_year','player_id','age','level','stage','prospect','prior_debut',
                    pl.col(f'pa_h{h}').alias('actual_pa'),pl.col(f'war_h{h}').alias('actual_value')).with_columns(
                        pl.lit(h,dtype=pl.Int32).alias('horizon'),pl.lit(cold).alias('cold'),pl.lit(year<2020<=year+h).alias('pandemic'),
                        pl.Series('new_p',prob).fill_nan(None),pl.Series('new_pa',candidate_pa),pl.Series('new_value',candidate_value),
                        pl.Series('conditional_pa',positive),pl.Series('rate',rate),pl.Series('cell_supported',supported))
                for strength in (50,200):
                    pp,_,_=cell_probability(train,test,h,strength)
                    ppa,vv=linked_value(np.nan_to_num(pp),positive,rate)
                    result=result.with_columns(pl.Series(f'p{strength}',pp).fill_nan(None),pl.Series(f'pa{strength}',ppa),pl.Series(f'value{strength}',vv))
                result=result.join(ref.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h)),on=['origin_year','player_id','horizon'],how='left',validate='1:1',maintain_order='left')
                assert result['old_value'].null_count()==0
                for name,which in scopes(result).items():
                    result=result.with_columns(pl.Series(name+'_affected',which),*[pl.when(pl.Series(which)).then(pl.col('new_'+suffix)).otherwise(pl.col('old_'+suffix)).alias(name+'_'+suffix) for suffix in ('pa','p','value')])
                note={'origin':year,'horizon':h,'cold':cold,'training_rows':train.height,'training_origins':sorted(train['origin_year'].unique().to_list()),
                    'latest_label':int(train['origin_year'].max())+h,'shared_players':len(set(train['player_id'])&set(test['player_id'])),
                    'probability_cells':cells,'conditional_pa_clipped':int(((positive==1)|(positive==750)).sum()),'rate_clipped':int(((rate==-5)|(rate==10)).sum())}
                result.write_parquet(dest); save(note_path,note)
            results.append(result); notes.append(note)
            print(f'Ready {year} H{h} cold={cold}',flush=True)
    result=pl.concat(results,how='diagonal_relaxed')
    result.write_parquet(OUT/'predictions.parquet')
    assert all(sha256_file(Path(p))==s for p,s in hashes.items())
    save(OUT/'fit-manifest.json',{'source_hashes':hashes,'fingerprint':fingerprint,'fits':notes,'protected_outcomes_used':False,'forecasts_changed':False})
    print(json.dumps({'rows':result.height,'fits':len(notes)}))


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4): main()
