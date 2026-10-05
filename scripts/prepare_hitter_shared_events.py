"""Prepare the fixed shared-profile comparison without fitting new hitter heads."""
from collections import defaultdict
from pathlib import Path
import json

import numpy as np
import polars as pl

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_shared_events import PROFILE, profile
from universal_baseball.hitter_talent_bridge import SCOUT_FEATURES
from universal_baseball.hitter_evidence_representation import FOREIGN_CONTROL_FEATURES
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from prepare_hitter_evidence_representation import tags

ROOT=Path(__file__).resolve().parents[1]
GEN=ROOT/'reports/generated'
OUT=GEN/'hitter-shared-events'
PREVIOUS=GEN/'hitter-evidence-representation'
BRIDGE=GEN/'hitter-talent-bridge-v74'
BORROWED=GEN/'foreign-borrowed-stability'
CONTRACT=ROOT/'docs/hitter-shared-event-contract.md'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(name,value):
    path=OUT/name
    assert not path.exists(),f'Preserve existing receipt {path}'
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def verify(mapping):
    for p,h in mapping.items():
        assert sha256_file(Path(p))==h,p


def main():
    assert not OUT.exists() or not any(OUT.iterdir()),'Do not restart saved source preparation'
    assert read(PREVIOUS/'final-review.json')['player_walkthrough_status']=='complete'
    old=read(PREVIOUS/'preflight.json')
    verify(old['source_hashes'])
    source={r['candidate_key']:r for r in read(GEN/'foreign-origin-inputs/origin-inputs.json')['rows']}
    profiles={(r['candidate_key'],r['outer_fold']):r for r in read(BORROWED/'profiles.json')['profiles']}
    fits={(r['cutoff'],tuple(r['excluded_folds'])):r for r in read(BORROWED/'fits.json')['fits']}
    for cal in fits.values():
        assert all(player_fold(pid) not in cal['excluded_folds'] for pid,_ in cal['domestic_keys'])
    history=defaultdict(list)
    raw=pl.read_parquet(GEN/'practical-hitter-v31/counts.parquet').filter(pl.col('season')<=2024)
    for r in raw.to_dicts():history[r['player_id']].append(r)
    selected={c['origin']['row_id'] for c in read(PREVIOUS/'reviewed-cases.json')['cases']}
    assert len(selected)==41
    base=read(GEN/'practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    names=[n for n in base if n not in old['removed_redundant_minor_rates']]+SCOUT_FEATURES+PROFILE+FOREIGN_CONTROL_FEATURES+['position_outfield_unspecified']
    assert len(names)==len(set(names))==134 and not any(n.startswith('next_') for n in names)
    OUT.mkdir(exist_ok=True)
    cases=[];checks=[];supports=[];counts=[];ranges=[]
    paths=[CONTRACT,Path(__file__),ROOT/'src/universal_baseball/hitter_shared_events.py',ROOT/'tests/test_hitter_shared_events.py',
           ROOT/'scripts/fit_hitter_shared_events.py',ROOT/'scripts/review_hitter_shared_events.py',
           GEN/'practical-hitter-v31/counts.parquet',BORROWED/'profiles.json',BORROWED/'fits.json',
           GEN/'foreign-origin-inputs/origin-inputs.json',PREVIOUS/'final-review.json',PREVIOUS/'reviewed-cases.json',
           PREVIOUS/'preflight.json',PREVIOUS/'predictions.parquet']
    for k in range(5):
        f=pl.read_parquet(PREVIOUS/f'features-{k}.parquet').sort('row_id')
        assert f.height==63314 and f['origin_year'].max()==2024 and f['target_year'].max()==2025
        graphs={g['cutoff']:g for g in read(BRIDGE/f'translation-{k}.json')['graphs']}
        for g in graphs.values():assert all(player_fold(p)!=k for p in g['people'])
        overlays={'domestic':[],'foreign':[]}
        for row in f.iter_rows(named=True):
            y=row['origin_year'];key=f'{y}:{row["player_id"]}';s=source.get(key);fp=profiles.get((key,k))
            cal=fits[y,tuple(sorted({k,row['outer_fold']}))]
            arms,note=profile(history[row['player_id']],graphs[y],cal,s,fp,origin=y,outer_fold=k,own_fold=row['outer_fold'])
            for a,p in arms.items():overlays[a].append(dict(row_id=row['row_id'],**p))
            if row['row_id'] in selected and row['outer_fold']==k:
                h=history[row['player_id']]
                used=[r for r in h if 0<=y-r['season']<3 and r['bucket'] in graphs[y]['offsets'] and r['plate_appearances']>0]
                smallest=min(used,key=lambda r:r['plate_appearances']) if used else None
                removal=None
                if smallest:
                    _,probe=profile([r for r in h if r is not smallest],graphs[y],cal,s,fp,origin=y,outer_fold=k,own_fold=row['outer_fold'])
                    removal=dict(removed=dict(season=smallest['season'],bucket=smallest['bucket'],PA=smallest['plate_appearances']),
                        future_shared_probability=probe['future_shared_probability'],
                        max_absolute_probability_change=float(np.max(np.abs(np.array(probe['future_shared_probability'])-note['future_shared_probability']))),
                        interpretation='Consistent source removal, not a replacement fit or causal estimate')
                cases.append(dict(row_id=row['row_id'],player_id=row['player_id'],player_name=row['player_name'],origin_year=y,
                    prior_debut=row['prior_debut'],age=row['age'],source_history=used,
                    profile=note,inputs=arms,smallest_source_removal=removal,
                    raw_profile_deployed=row['prior_debut']==0,
                    foreign_source=bool(s),calibration_key=cal['fit_key']))
        keys=['prior_debut','stage','age_group','mlb_exposure','foreign_source','first_team_history','restriction_profile']
        for arm in overlays:
            g=f.join(pl.DataFrame(overlays[arm]),on='row_id',validate='1:1')
            path=OUT/f'{arm}-features-{k}.parquet';g.write_parquet(path);paths.append(path)
            assert np.isfinite(safe_matrix(g,names)).all()
            for c in [c for c in old['cells'] if c['fold']==k]:
                tr=g.filter(pl.col('row_id').is_in(c['training_row_ids'])&(pl.col('next_pa')>0)).sort('row_id')
                te=g.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
                sup,note=preflight(tr,te,cutoff=c['year'],fold=k,features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                assert tr['target_year'].max()<=c['year'] and not set(tr['player_id'])&set(te['player_id'])
                supports.append(sup.with_columns(pl.lit(arm).alias('arm'),pl.lit(k).alias('test_fold')))
                cnt=tags(tr).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
                counts.append(tags(te).select('row_id',*keys).join(cnt,on=keys,how='left',validate='m:1').with_columns(
                    pl.col('profile_people').fill_null(0),pl.lit(arm).alias('arm'),pl.lit(k).alias('test_fold'),pl.lit(c['year']).alias('origin_year')))
                x,tx=safe_matrix(tr,names),safe_matrix(te,names)
                for i,n in enumerate(names):
                    lo,hi=float(x[:,i].min()),float(x[:,i].max())
                    ids=te.filter(pl.Series((tx[:,i]<lo)|(tx[:,i]>hi)))['row_id'].to_list()
                    if ids:ranges.append(dict(arm=arm,origin=c['year'],fold=k,feature=n,min=lo,max=hi,row_ids=ids))
                checks.append(dict(origin=c['year'],fold=k,arm=arm,**note))
        paths += [PREVIOUS/f'features-{k}.parquet',BRIDGE/f'translation-{k}.json']
        print(f'Fold {k}: both source matrices and all actual active preflights saved.',flush=True)
    assert len(checks)==70 and len(cases)==41
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(counts).write_parquet(OUT/'profile-support.parquet')
    save('source-cases.json',dict(cases=cases));save('ranges.json',dict(warnings=ranges))
    paths += [OUT/n for n in ['support.parquet','profile-support.parquet','source-cases.json','ranges.json']]
    save('preflight.json',dict(cells=old['cells'],checks=checks,names=names,arms=['domestic','foreign'],
        input_hashes={str(p):sha256_file(p) for p in paths},ridge_alpha=100,new_hitter_fits=0,
        source_walkthrough_status='pending',protected_outcomes_used=False,deployment_approved=False))


if __name__=='__main__':main()
