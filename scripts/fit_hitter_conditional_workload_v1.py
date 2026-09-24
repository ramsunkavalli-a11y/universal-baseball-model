"""Freeze and fit conditional workload only; no component/value replacement."""
import argparse
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_arrival_source_repair import FEATURES
from universal_baseball.hitter_arrival_value_transfer import FOLDS
from universal_baseball.hitter_conditional_workload import fit_head
from universal_baseball.storage import sha256_file

OUT=Path('reports/generated/hitter-conditional-workload-v1')
PANEL=Path('reports/generated/hitter-arrival-source-repair-v1/repaired-panel.parquet')
PREVIOUS=Path('model_artifacts/hitter-arrival-value-transfer-v1-2026-09-23')
BASE=Path('reports/generated/multiyear-hitter-v1/manifest.json')
DETAIL=Path('reports/generated/hitter-detail-arrival-v1/prefit-manifest.json')
CODE=[Path('docs/hitter-conditional-workload-v1-plan.md'),Path(__file__),Path('scripts/score_hitter_conditional_workload_v1.py'),
    Path('tests/test_hitter_conditional_workload.py'),*[Path('src/universal_baseball')/(n+'.py') for n in
        ('hitter_conditional_workload','hitter_arrival_value_transfer','hitter_canceled_season','hitter_model_tournament')]]


def hashes():
    return {str(p):sha256_file(p) for p in [*CODE,PANEL,BASE,DETAIL,PREVIOUS/'predictions.parquet',PREVIOUS/'fit-manifest.json']}


def references(panel):
    f=pl.read_parquet(PREVIOUS/'predictions.parquet').select('origin_year','player_id','player_name','horizon','age','level','stage',
        'prospect','prior_debut','minor_returner','recent_debut','mlb_pa_lag0','actual_pa','B_pa','E_pa',
        pl.col('F_pa').alias('I_pa'),pl.col('U_p').alias('fixed_p'),(pl.col('B_pa')/pl.col('B_p')).alias('I_conditional'))
    assert set(f.select('origin_year','horizon').unique().iter_rows())==set(FOLDS)
    for y,h in FOLDS:
        q=panel.filter(pl.col('origin_year')==y);b=f.filter((pl.col('origin_year')==y)&(pl.col('horizon')==h))
        np.testing.assert_array_equal(q['player_id'],b['player_id']);np.testing.assert_array_equal(q[f'pa_h{h}'],b['actual_pa'])
    return f.sort('horizon','origin_year','player_id')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    (OUT/'fits').mkdir(parents=True,exist_ok=True)
    panel=pl.read_parquet(PANEL)
    basic=json.loads(BASE.read_text())['full_features']+['prior_debut']+FEATURES
    detailed=json.loads(DETAIL.read_text())['arms']['R']+FEATURES
    columns={'A':basic,'D':detailed,'M':detailed}
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Already frozen')
        ref=references(panel);ref.write_parquet(OUT/'references.parquet')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'columns':columns,'folds':FOLDS,
            'reference_sha256':sha256_file(OUT/'references.parquet'),'protected_outcomes_used':False,'production_forecasts_changed':False})
        print('Fixed workload contract frozen');return
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    assert sha256_file(OUT/'references.parquet')==pre['reference_sha256']
    refs=pl.read_parquet(OUT/'references.parquet');frames=[];notes=[]
    for year,h in FOLDS:
        b=refs.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))
        for head in ('A','D','M'):
            path=OUT/'fits'/f'{year}-h{h}-{head}.parquet'
            if path.exists() and path.with_suffix('.json').exists():
                note=json.loads(path.with_suffix('.json').read_text());assert sha256_file(path)==note['sha256']
                result=pl.read_parquet(path)
            else:
                print(f'Workload {year} H{h} {head}',flush=True)
                q,p,note=fit_head(panel,columns[head],year,h,head)
                result=b.select('origin_year','player_id','horizon').with_columns(pl.Series(head+'_conditional',q))
                if p is not None:
                    result=result.with_columns(*[pl.Series('role_'+str(k),p[:,k]) for k in range(3)])
                result.write_parquet(path);note['sha256']=sha256_file(path);save(path.with_suffix('.json'),note)
            b=b.join(result,on=['origin_year','player_id','horizon'],how='left',validate='1:1',maintain_order='left')
            b=b.with_columns((pl.col('fixed_p')*pl.col(head+'_conditional')).alias(head+'_universal_pa'))
            b=b.with_columns(pl.when(pl.col('prospect')).then(pl.col(head+'_universal_pa')).otherwise(pl.col('B_pa')).alias(head+'_pa'))
            notes.append(note)
        b=b.with_columns((pl.col('fixed_p')*pl.col('role_2')).alias('M_regular_probability'))
        frames.append(b)
    f=pl.concat(frames).sort('horizon','origin_year','player_id');f.write_parquet(OUT/'predictions.parquet')
    checks=[]
    for year,h in [(2022,2),(2021,3)]:
        changed=panel.with_columns(pl.when(pl.col('origin_year')+h>year).then(9999.).otherwise(pl.col(f'pa_h{h}')).alias(f'pa_h{h}'))
        changed=changed.with_columns(*[pl.when(pl.col('origin_year')>year).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c) for c in detailed])
        for head in ('D','M'):
            print(f'Future mutation {year} H{h} {head}',flush=True)
            q,p,_=fit_head(changed,columns[head],year,h,head)
            b=f.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))
            np.testing.assert_array_equal(q,b[head+'_conditional'])
            if p is not None:np.testing.assert_array_equal(p,b.select('role_0','role_1','role_2').to_numpy())
            checks.append({'year':year,'horizon':h,'head':head,'maximum_difference':0.})
    assert hashes()==pre['hashes']
    save(OUT/'fit-manifest.json',{'fits':notes,'mutations':checks,'prediction_sha256':sha256_file(OUT/'predictions.parquet'),
        'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),'protected_outcomes_used':False,'production_forecasts_changed':False})
    print('36 heads and four mutation checks complete',flush=True)


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
