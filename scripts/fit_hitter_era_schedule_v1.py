"""Fixed single-field era ablations and matched-training schedule test."""
import argparse
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_hitter_arrival_coherence_v1 import save
from fit_hitter_detail_arrival_v1 import OUT as SOURCE
from audit_hitter_schedule_opportunity_v1 import OUT
from universal_baseball.hitter_detail_arrival import eligible
from universal_baseball.hitter_canceled_season import fit_model,predict
from universal_baseball.hitter_structural_missingness import fit_augmented
from universal_baseball.hitter_schedule_opportunity import attach_schedule,restrict_training,FEATURES
from universal_baseball.storage import sha256_file

PACKAGE=Path('model_artifacts/hitter-era-schedule-v1-2026-09-23')
A_SOURCE=Path('reports/generated/hitter-structural-missingness-v1/predictions.parquet')
CODE=[Path('docs/hitter-era-schedule-v1-plan.md'),Path(__file__),
      Path('scripts/audit_hitter_schedule_opportunity_v1.py'),Path('scripts/score_hitter_era_schedule_v1.py'),
      Path('src/universal_baseball/hitter_schedule_opportunity.py'),Path('tests/test_hitter_schedule_opportunity.py'),
      *[Path('src/universal_baseball')/(s+'.py') for s in ('hitter_structural_missingness','hitter_canceled_season',
           'hitter_detail_arrival','hitter_model_tournament')]]


def hashes():
    return {str(p):sha256_file(p) for p in [*CODE,SOURCE/'input-panel.parquet',SOURCE/'prefit-manifest.json',
         SOURCE/'predictions.parquet',A_SOURCE,OUT/'schedule-features.parquet',OUT/'schedule-audit.json',OUT/'team-schedules.parquet']}


def fit(train,query,columns,arm):
    if arm=='AE': return fit_augmented(train,query,columns,'next_year',True)
    if arm in ('S0','S1'): train=restrict_training(train)
    cols=columns+FEATURES if arm=='S1' else columns
    model,used,note=fit_model(train,cols,'next_year')
    return predict(model,used,query),note


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    (OUT/'fits').mkdir(parents=True,exist_ok=True)
    columns=json.loads((SOURCE/'prefit-manifest.json').read_text())['arms']['R']
    assert columns.count('reorganization_era')==1
    columns=[c for c in columns if c!='reorganization_era']
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Already frozen')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'columns_without_era':columns,'schedule_features':FEATURES,
             'protected_outcomes_used':False});print('Frozen');return
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    panel=attach_schedule(pl.read_parquet(SOURCE/'input-panel.parquet'),pl.read_parquet(OUT/'schedule-features.parquet'))
    base=pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold')&~pl.col('pandemic')&
          (pl.col('engine')=='lightgbm')&(pl.col('arm')=='R')&(pl.col('target')=='next_year'))
    a=pl.read_parquet(A_SOURCE).filter((pl.col('target')=='next_year')&(pl.col('arm')=='A'))
    frames=[base,a];notes=[]
    for (year,),b in base.partition_by('origin_year',as_dict=True).items():
        query=panel.filter(pl.col('origin_year')==year); train=eligible(panel,year,'next_year')
        np.testing.assert_array_equal(query['player_id'],b['player_id'])
        for arm in (['E','AE']+(['S0','S1'] if year>=2021 else [])):
            path=OUT/'fits'/f'next_year-{year}-{arm}.parquet'
            if path.exists() and path.with_suffix('.json').exists():
                note=json.loads(path.with_suffix('.json').read_text());assert sha256_file(path)==note['sha256']
                frame=pl.read_parquet(path)
            else:
                print(f'{year} {arm}',flush=True);p,note=fit(train,query,columns,arm)
                frame=b.with_columns(pl.Series('probability',p),pl.lit(arm).alias('arm'));frame.write_parquet(path)
                note.update(year=year,arm=arm,sha256=sha256_file(path));save(path.with_suffix('.json'),note)
            frames.append(frame);notes.append(note)
    result=pl.concat(frames,how='vertical_relaxed');result.write_parquet(OUT/'predictions.parquet')
    mutations=[]
    for arm,year in [('AE',2022),('S1',2021)]:
        changed=panel.with_columns(pl.when(pl.col('origin_year')+1>year).then(9999.).otherwise(pl.col('pa_h1')).alias('pa_h1'))
        changed=changed.with_columns(*[pl.when(pl.col('origin_year')>year).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c)
                                     for c in columns+FEATURES])
        print(f'Future mutation {arm} {year}',flush=True)
        p,_=fit(eligible(changed,year,'next_year'),changed.filter(pl.col('origin_year')==year),columns,arm)
        expected=result.filter((pl.col('origin_year')==year)&(pl.col('arm')==arm))
        np.testing.assert_array_equal(p,expected['probability']);mutations.append({'arm':arm,'origin':year,'max_difference':0.})
    assert hashes()==pre['hashes']
    save(OUT/'fit-manifest.json',{'fits':notes,'mutations':mutations,
        'prediction_sha256':sha256_file(OUT/'predictions.parquet'),'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),
        'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(json.dumps({'fits':len(notes),'mutations':mutations}))


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
