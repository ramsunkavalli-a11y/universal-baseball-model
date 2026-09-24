"""Fixed source-repair factorial; never edits the original panel or forecast."""
import argparse
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from materialize_hitter_arrival_source_repair_v1 import OUT, SOURCE
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_arrival_source_repair import COHORTS, FEATURES
from universal_baseball.hitter_detail_arrival import eligible, target_values, TARGETS
from universal_baseball.hitter_canceled_season import fit_model, predict
from universal_baseball.storage import sha256_file

CODE = [Path('docs/hitter-arrival-source-repair-v1-plan.md'), Path(__file__),
    Path('scripts/materialize_hitter_arrival_source_repair_v1.py'),
    Path('scripts/score_hitter_arrival_source_repair_v1.py'),
    Path('tests/test_hitter_arrival_source_repair.py'),
    *[Path('src/universal_baseball')/(n+'.py') for n in
      ('hitter_arrival_source_repair','hitter_detail_arrival','hitter_canceled_season','hitter_model_tournament')]]
FOLDS = [(y,'next_year') for y in (2017,2018,2021,2022,2023,2024)]+[
    (y,t) for t in ('arrival_three','regular_three') for y in (2021,2022)]


def hashes():
    files = [*CODE, *[OUT/n for n in ('repaired-panel.parquet','source-audit.json','source-changes.parquet',
        'debut-dates.parquet','year-end-rosters.parquet','league-context.parquet')],
        *[SOURCE/n for n in ('input-panel.parquet','predictions.parquet','prefit-manifest.json','reference-predictions.parquet')],
        Path('model_artifacts/hitter-era-schedule-v1-2026-09-23/predictions.parquet')]
    return {str(p):sha256_file(p) for p in files}


def arm_panel(original, repaired, arm):
    if arm=='R': return original
    if arm=='F': return repaired
    if arm=='C': return repaired.with_columns(original['on_40man'])
    if arm=='T': return original.with_columns(repaired['on_40man'])
    raise ValueError(arm)


def fit(panel, columns, arm, year, target):
    cols=columns+FEATURES if arm in ('C','F') else columns
    train=eligible(panel,year,target)
    query=panel.filter(pl.col('origin_year')==year)
    model,used,note=fit_model(train,cols,target)
    note['latest_label']=int(train['origin_year'].max())+TARGETS[target]
    assert note['latest_label']<=year
    return predict(model,used,query),note


def corrected_scoring(frame,repaired):
    metadata=repaired.select('origin_year','player_id',*COHORTS)
    return frame.drop([c for c in COHORTS if c in frame.columns]).join(metadata,
        on=['origin_year','player_id'],how='left',validate='m:1',maintain_order='left')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    (OUT/'fits').mkdir(parents=True,exist_ok=True)
    columns=json.loads((SOURCE/'prefit-manifest.json').read_text())['arms']['R']
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Already frozen')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'base_columns':columns,'league_columns':FEATURES,
            'folds':FOLDS,'arms':['R','C','T','F'],'primary':'F','protected_outcomes_used':False})
        print('Frozen before fitting');return
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    original=pl.read_parquet(SOURCE/'input-panel.parquet');repaired=pl.read_parquet(OUT/'repaired-panel.parquet')
    base=pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold')&~pl.col('pandemic')&
             (pl.col('engine')=='lightgbm')&(pl.col('arm')=='R'))
    frames=[];notes=[]
    for year,target in FOLDS:
        b=base.filter((pl.col('origin_year')==year)&(pl.col('target')==target))
        q=original.filter(pl.col('origin_year')==year)
        np.testing.assert_array_equal(q['player_id'],b['player_id'])
        np.testing.assert_array_equal(target_values(q,target),b['actual'])
        frames.append(corrected_scoring(b,repaired))
        for arm in ('C','T','F'):
            path=OUT/'fits'/f'{target}-{year}-{arm}.parquet'
            if path.exists() and path.with_suffix('.json').exists():
                note=json.loads(path.with_suffix('.json').read_text());assert sha256_file(path)==note['sha256']
                frame=pl.read_parquet(path)
            else:
                print(f'{target} {year} {arm}',flush=True)
                p,note=fit(arm_panel(original,repaired,arm),columns,arm,year,target)
                frame=corrected_scoring(b.with_columns(pl.Series('probability',p),pl.lit(arm).alias('arm')),repaired)
                frame.write_parquet(path);note.update(arm=arm,year=year,target=target,sha256=sha256_file(path))
                save(path.with_suffix('.json'),note)
            frames.append(frame);notes.append(note)
    result=pl.concat(frames,how='vertical_relaxed');result.write_parquet(OUT/'predictions.parquet')
    checks=[]
    for year,target in [(2022,'next_year'),(2021,'regular_three')]:
        h=TARGETS[target]
        changed=repaired.with_columns(*[pl.when(pl.col('origin_year')+h>year).then(9999.).otherwise(pl.col(f'pa_h{k}')).alias(f'pa_h{k}') for k in range(1,h+1)])
        changed=changed.with_columns(*[pl.when(pl.col('origin_year')>year).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c) for c in columns+FEATURES])
        print(f'Future mutation F {year} {target}',flush=True)
        p,_=fit(changed,columns,'F',year,target)
        b=result.filter((pl.col('arm')=='F')&(pl.col('origin_year')==year)&(pl.col('target')==target))
        np.testing.assert_array_equal(p,b['probability']);checks.append({'arm':'F','year':year,'target':target,'max_difference':0.})
    print('Unmodified R replay 2021 next_year',flush=True)
    p,_=fit(original,columns,'R',2021,'next_year')
    np.testing.assert_array_equal(p,base.filter((pl.col('origin_year')==2021)&(pl.col('target')=='next_year'))['probability'])
    assert hashes()==pre['hashes']
    save(OUT/'fit-manifest.json',{'fits':notes,'mutations':checks,'original_replay_exact':True,
        'prediction_sha256':sha256_file(OUT/'predictions.parquet'),'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),
        'protected_outcomes_used':False,'production_forecasts_changed':False})
    print('Completed 30 fits, two mutation replays and one original replay',flush=True)


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
