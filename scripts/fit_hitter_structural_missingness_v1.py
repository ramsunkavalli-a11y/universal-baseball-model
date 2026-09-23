"""Fit one locked source-outage augmentation and its duplicate-only control."""
import argparse
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_hitter_arrival_coherence_v1 import save
from fit_hitter_detail_arrival_v1 import OUT as SOURCE
from universal_baseball.hitter_detail_arrival import eligible,TARGETS
from universal_baseball.hitter_structural_missingness import fit_augmented
from universal_baseball.storage import sha256_file

OUT=Path('reports/generated/hitter-structural-missingness-v1')
PACKAGE=Path('model_artifacts/hitter-structural-missingness-v1-2026-09-23')
CODE=[Path('docs/hitter-structural-missingness-v1-plan.md'),Path(__file__),
      Path('src/universal_baseball/hitter_structural_missingness.py'),Path('tests/test_hitter_structural_missingness.py'),
      Path('src/universal_baseball/hitter_canceled_season.py'),Path('src/universal_baseball/hitter_detail_arrival.py'),
      Path('src/universal_baseball/hitter_model_tournament.py')]


def hashes():
    return {str(p):sha256_file(p) for p in [*CODE,SOURCE/'input-panel.parquet',SOURCE/'prefit-manifest.json',
            SOURCE/'predictions.parquet',SOURCE/'reference-predictions.parquet']}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'fits').mkdir(exist_ok=True)
    panel=pl.read_parquet(SOURCE/'input-panel.parquet')
    columns=json.loads((SOURCE/'prefit-manifest.json').read_text())['arms']['R']
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Already frozen')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'columns':columns,'weights':[.5,.25,.25],
            'protected_outcomes_used':False});print(json.dumps({'frozen':True}));return
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    old=pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold')&~pl.col('pandemic')&
         (pl.col('engine')=='lightgbm')&(pl.col('arm')=='R'))
    frames=[];notes=[]
    for (target,year),base in old.partition_by('target','origin_year',as_dict=True).items():
        query=panel.filter(pl.col('origin_year')==year);train=eligible(panel,year,target)
        np.testing.assert_array_equal(query['player_id'],base['player_id']);frames.append(base)
        for arm in ('T','A'):
            path=OUT/'fits'/f'{target}-{year}-{arm}.parquet'
            if path.exists() and path.with_suffix('.json').exists():
                note=json.loads(path.with_suffix('.json').read_text());assert sha256_file(path)==note['sha256']
                frame=pl.read_parquet(path)
            else:
                print(f'{target} {year} {arm}',flush=True)
                prob,note=fit_augmented(train,query,columns,target,masked=arm=='A')
                frame=base.with_columns(pl.Series('probability',prob),pl.lit(arm).alias('arm'))
                frame.write_parquet(path)
                note.update(target=target,year=year,arm=arm,latest_label=int(train['origin_year'].max())+TARGETS[target],sha256=sha256_file(path))
                save(path.with_suffix('.json'),note)
            frames.append(frame);notes.append(note)
    f=pl.concat(frames,how='vertical_relaxed');f.write_parquet(OUT/'predictions.parquet')
    changed=panel
    for h in (1,2,3):
        changed=changed.with_columns(pl.when(pl.col('origin_year')+h>2021).then(9999.)
                   .otherwise(pl.col(f'pa_h{h}')).alias(f'pa_h{h}'))
    changed=changed.with_columns(*[pl.when(pl.col('origin_year')>2021).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c) for c in columns])
    print('Future-mutation refit',flush=True)
    mp,_=fit_augmented(eligible(changed,2021,'regular_three'),changed.filter(pl.col('origin_year')==2021),columns,'regular_three',True)
    expected=f.filter((pl.col('target')=='regular_three')&(pl.col('origin_year')==2021)&(pl.col('arm')=='A'))
    np.testing.assert_array_equal(mp,expected['probability'])
    assert pre['hashes']==hashes()
    save(OUT/'fit-manifest.json',{'fits':notes,'future_mutation_max_difference':float(np.max(abs(mp-expected['probability'].to_numpy()))),
         'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),'prediction_sha256':sha256_file(OUT/'predictions.parquet'),
         'protected_outcomes_used':False,'production_forecasts_changed':False})
    print(json.dumps({'fits':len(notes),'mutation_refits':1,'rows':f.height,'future_mutation_passed':True}))


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
