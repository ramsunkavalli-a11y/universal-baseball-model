"""Fixed chronological stacking test: talent and draft pedigree -> workload."""
import argparse
import json
import warnings
from pathlib import Path
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_arrival_value_transfer import FOLDS
from universal_baseball.hitter_conditional_workload import fit_head
from universal_baseball.hitter_talent_workload import (
    TALENT,PEDIGREE,pedigree_features,fit_talent,fit_workload,talent_training)
from universal_baseball.storage import sha256_file

OUT=Path('reports/generated/hitter-talent-workload-v1')
PACKAGE=Path('model_artifacts/hitter-talent-workload-v1-2026-09-23')
PANEL=Path('reports/generated/hitter-arrival-source-repair-v1/repaired-panel.parquet')
PREVIOUS=Path('model_artifacts/hitter-conditional-workload-v1-2026-09-23')
DRAFT=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated/draft-history/draft-history.parquet')
CODE=[Path('docs/hitter-talent-workload-v1-plan.md'),Path(__file__),
      Path('scripts/score_hitter_talent_workload_v1.py'),Path('tests/test_hitter_talent_workload.py'),
      *[Path('src/universal_baseball')/(s+'.py') for s in ('hitter_talent_workload',
       'hitter_conditional_workload','hitter_arrival_value_transfer','hitter_canceled_season','hitter_model_tournament')]]


def hashes():
    return {str(p):sha256_file(p) for p in [*CODE,PANEL,DRAFT,PREVIOUS/'predictions.parquet',PREVIOUS/'prefit-manifest.json']}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    (OUT/'fits').mkdir(parents=True,exist_ok=True)
    panel=pl.read_parquet(PANEL).filter(pl.col('origin_year')<=2022).sort('origin_year','player_id')
    cols=json.loads((PREVIOUS/'prefit-manifest.json').read_text())['columns']['D']
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Already frozen')
        d=pl.read_parquet(DRAFT).filter(pl.col('draft_year')<=2022).select('draft_year','player_id','pick_number','school_class')
        raw_rows=d.height
        d=d.unique(maintain_order=True)
        assert not d.select('draft_year','player_id','pick_number').is_duplicated().any()
        d.write_parquet(OUT/'draft-evidence.parquet')
        p=pedigree_features(panel,d)
        coverage=p.group_by('origin_year','prospect').agg(pl.len().alias('rows'),
             pl.col('pedigree_matched').sum().alias('draft_matches')).sort('origin_year','prospect')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'columns':cols,'folds':FOLDS,
             'draft_sha256':sha256_file(OUT/'draft-evidence.parquet'),'draft_coverage':coverage.to_dicts(),
             'exact_duplicate_draft_rows_removed':raw_rows-d.height,
             'talent_features':TALENT,'pedigree_features':PEDIGREE,'primary':'TP',
             'protected_outcomes_used':False,'production_forecasts_changed':False})
        print('Plan, sources and code frozen');return
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert hashes()==pre['hashes']
    assert pre['draft_sha256']==sha256_file(OUT/'draft-evidence.parquet')
    draft=pl.read_parquet(OUT/'draft-evidence.parquet');panel=pedigree_features(panel,draft)
    parts=[];inner_notes=[]
    for year in sorted(panel['origin_year'].unique()):
        q=panel.filter(pl.col('origin_year')==year).select('origin_year','player_id')
        for h in (1,3):
            path=OUT/'fits'/f'talent-{year}-h{h}.parquet'
            if path.exists() and path.with_suffix('.json').exists():
                n=json.loads(path.with_suffix('.json').read_text());assert sha256_file(path)==n['sha256'];v=pl.read_parquet(path)
            else:
                print(f'Nested talent {year} H{h}',flush=True)
                pred,n=fit_talent(panel,cols,year,h)
                v=q.select('origin_year','player_id').with_columns(pl.Series(f'talent_rate_h{h}',pred),
                    pl.lit(int(n['supported'])).alias(f'talent_supported_h{h}'))
                v.write_parquet(path);n['sha256']=sha256_file(path);save(path.with_suffix('.json'),n)
            q=q.join(v,on=['origin_year','player_id'],validate='1:1',maintain_order='left')
            inner_notes.append(n)
        parts.append(q)
    nested=pl.concat(parts).sort('origin_year','player_id');nested.write_parquet(OUT/'nested-talent.parquet')
    panel=panel.join(nested,on=['origin_year','player_id'],validate='1:1',maintain_order='left')
    refs=pl.read_parquet(PREVIOUS/'predictions.parquet')
    frames=[];notes=[]
    for year,h in FOLDS:
        q=panel.filter(pl.col('origin_year')==year)
        b=refs.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))
        np.testing.assert_array_equal(q['player_id'],b['player_id'])
        np.testing.assert_array_equal(q[f'pa_h{h}'],b['actual_pa'])
        b=b.join(q.select('origin_year','player_id',*TALENT,*PEDIGREE),on=['origin_year','player_id'],validate='1:1',maintain_order='left')
        for arm in ('T','P','TP'):
            path=OUT/'fits'/f'workload-{year}-h{h}-{arm}.parquet'
            if path.exists() and path.with_suffix('.json').exists():
                n=json.loads(path.with_suffix('.json').read_text());assert sha256_file(path)==n['sha256'];v=pl.read_parquet(path)
            else:
                print(f'Workload {year} H{h} {arm}',flush=True)
                pred,n=fit_workload(panel,cols,year,h,arm)
                v=q.select('origin_year','player_id').with_columns(pl.Series(arm+'_conditional',pred))
                v.write_parquet(path);n['sha256']=sha256_file(path);save(path.with_suffix('.json'),n)
            b=b.join(v,on=['origin_year','player_id'],validate='1:1',maintain_order='left')
            b=b.with_columns(pl.when(pl.col('prospect')).then(pl.col('fixed_p')*pl.col(arm+'_conditional'))
                .otherwise(pl.col('B_pa')).alias(arm+'_pa'))
            notes.append(n)
        frames.append(b)
    f=pl.concat(frames).sort('horizon','origin_year','player_id');f.write_parquet(OUT/'predictions.parquet')
    print('Replay prior D: 2021 H1',flush=True)
    d,_,_=fit_head(panel,cols,2021,1,'D')
    np.testing.assert_array_equal(d,f.filter((pl.col('origin_year')==2021)&(pl.col('horizon')==1))['D_conditional'])
    checks=[]
    for year,h in ((2016,1),(2021,3)):
        changed=panel.with_columns(pl.when(pl.col('origin_year')+h>year).then(9999.).otherwise(pl.col(f'war_h{h}')).alias(f'war_h{h}'),
            pl.when(pl.col('origin_year')+h>year).then(777.).otherwise(pl.col(f'pa_h{h}')).alias(f'pa_h{h}'))
        assert talent_training(panel,year,h).equals(talent_training(changed,year,h))
        print(f'Nested future mutation {year} H{h}',flush=True)
        r,_=fit_talent(changed,cols,year,h)
        np.testing.assert_array_equal(r,nested.filter(pl.col('origin_year')==year)[f'talent_rate_h{h}'])
        checks.append({'type':'inner','year':year,'horizon':h,'maximum_difference':0.})
    for year,h in ((2021,3),(2022,2)):
        changed=panel
        for k in (1,2,3):
            changed=changed.with_columns(*[pl.when(pl.col('origin_year')+k>year).then(9999.)
                .otherwise(pl.col(f'{target}_h{k}')).alias(f'{target}_h{k}') for target in ('pa','war')])
        # Every cached nested forecast available to this outer fit has identical
        # eligible raw records. No future label can enter via the stacking layer.
        nested_checked=0
        for s in sorted(panel.filter(pl.col('origin_year')<=year)['origin_year'].unique()):
            for k in (1,3):
                a=talent_training(panel,s,k);b=talent_training(changed,s,k)
                used=['origin_year','player_id','identity_weight',f'pa_h{k}',f'war_h{k}',*cols]
                assert a.select(used).equals(b.select(used))
                nested_checked+=1
        print(f'Outer future mutation {year} H{h}',flush=True)
        r,_=fit_workload(changed,cols,year,h,'TP')
        np.testing.assert_array_equal(r,f.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))['TP_conditional'])
        checks.append({'type':'outer','year':year,'horizon':h,'nested_training_sets_checked':nested_checked,'maximum_difference':0.})
    assert hashes()==pre['hashes']
    save(OUT/'fit-manifest.json',{'inner_fits':inner_notes,'workload_fits':notes,'mutations':checks,
        'prior_D_replay':{'year':2021,'horizon':1,'maximum_difference':0.},
        'prediction_sha256':sha256_file(OUT/'predictions.parquet'),'nested_sha256':sha256_file(OUT/'nested-talent.parquet'),
        'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),'protected_outcomes_used':False,'production_forecasts_changed':False})
    print('Talent/workload fits and replays complete',flush=True)


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
