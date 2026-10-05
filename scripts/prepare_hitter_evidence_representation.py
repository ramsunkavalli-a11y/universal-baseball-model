"""Assemble source-only repaired inputs and seal every actual check before fits."""
from collections import defaultdict
from pathlib import Path
import json

import numpy as np
import polars as pl

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_evidence_representation import (
    RECENCY, MINOR_FEATURES, FOREIGN_CONTROL_FEATURES, FOREIGN_TALENT_FEATURES,
    JOB_FEATURES, check_cutoff, minor_evidence, foreign_evidence, job_evidence,
)
from universal_baseball.hitter_talent_bridge import SCOUT_FEATURES
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from prepare_hitter_statcast_next_year import materialize as tracking_features

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'reports/generated'
OUT = GEN / 'hitter-evidence-representation'
OLD = GEN / 'hitter-overseas-integration'
BRIDGE = GEN / 'hitter-talent-bridge-v74'
CONTRACT = ROOT / 'docs/hitter-evidence-representation-contract.md'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def save(name, value):
    path = OUT / name
    assert not path.exists(), f'Preserve completed preparation: {path}'
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False,
                              default=str) + '\n', encoding='utf8', newline='\n')


def tags(f):
    return f.with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_group'),
        pl.when(pl.col('pa_0')==0).then(0).when(pl.col('pa_0')<200).then(1).otherwise(2).alias('mlb_exposure'),
        (pl.col('evidence_foreign_source_present')>0).alias('foreign_source'),
        (pl.col('last_first_team_known')>0).alias('first_team_history'),
        pl.when(pl.col('status_hard_unavailable')>0).then(3).when(pl.col('status_unresolved_nonmedical')>0).then(2)
          .when(pl.col('status_finite_nonmedical')>0).then(1).otherwise(0).alias('restriction_profile'))


def main():
    # A stopped source-only preparation may have five frames but no seal.
    # Reconstruct and compare every cached frame; never trust mere existence.
    allowed={f'features-{k}.parquet' for k in range(5)}
    assert not OUT.exists() or {p.name for p in OUT.iterdir()} <= allowed, 'Inspect completed or unexpected work; never restart it'
    assert read(OLD/'final-review.json')['player_walkthrough_status']=='complete'
    inventory = read(GEN/'hitter-incumbent-representation-audit/inventory.json')
    assert inventory['heads_replayed']==175 and inventory['new_fits']==0
    for p,h in inventory['input_hashes'].items():
        assert sha256_file(Path(p))==h, p
    old_pre=read(OLD/'preflight.json')
    # Only retained immutable data artifacts need loading. No 2026 source is read.
    frame=pl.read_parquet(OLD/'features.parquet').sort('row_id')
    assert frame.height==63314 and frame['origin_year'].max()==2024 and frame['target_year'].max()==2025
    raw=pl.read_parquet(GEN/'practical-hitter-v31/counts.parquet').filter(pl.col('season')<=2024)
    history=defaultdict(list)
    for r in raw.to_dicts():
        history[r['player_id']].append(r)
    source={r['candidate_key']:r for r in read(GEN/'foreign-origin-inputs/origin-inputs.json')['rows']}
    profiles={(r['candidate_key'],r['outer_fold']):r for r in read(GEN/'foreign-borrowed-stability/profiles.json')['profiles']}
    annual=pl.read_parquet(GEN/'hitter-statcast-full-history/annual-launch-features.parquet')
    assert annual['season'].max()==2024
    frame, controls, measurements=tracking_features(frame,annual)
    base=read(GEN/'practical-hitter-numeric-repair-v53/preflight.json')['rate_features']
    events={'K','BB','HBP','HR','BABIP','2B','3B'}
    removed=[c for c in base if c.startswith('pooled_') and not c.startswith('pooled_MLB_') and c.rsplit('_',1)[-1] in events]
    assert len(removed)==91
    domestic=[c for c in base if c not in removed]+SCOUT_FEATURES+MINOR_FEATURES+controls+measurements+FOREIGN_CONTROL_FEATURES+['position_outfield_unspecified']
    arms={'domestic':domestic,'overseas':domestic+FOREIGN_TALENT_FEATURES}
    job_names=read(GEN/'hitter-preseason-readiness-v68/preflight.json')['pa_features']
    job_names=job_names+[c for c in old_pre['arms']['domestic'] if c not in job_names]+JOB_FEATURES
    assert (len(domestic),len(arms['overseas']),len(job_names))==(195,202,293)
    assert len(set(arms['overseas']))==202 and len(set(job_names))==293
    assert not any(c.startswith('next_') for c in arms['overseas']+job_names)
    selected={r['origin']['row_id'] for r in read(OLD/'reviewed-cases.json')['cases']}
    assert len(selected)==38
    paths=[CONTRACT,ROOT/'docs/hitter-evidence-representation-prefit-correction.md',Path(__file__),ROOT/'src/universal_baseball/hitter_evidence_representation.py',
           ROOT/'tests/test_hitter_evidence_representation.py',ROOT/'scripts/fit_hitter_evidence_representation.py',
           ROOT/'scripts/prepare_practical_hitter_v33.py',ROOT/'scripts/prepare_hitter_statcast_next_year.py',
           ROOT/'src/universal_baseball/forecast_validation.py',ROOT/'src/universal_baseball/hitter_talent_bridge.py',
           OLD/'preflight.json',OLD/'features.parquet',OLD/'final-review.json',OLD/'reviewed-cases.json',
           GEN/'practical-hitter-v31/counts.parquet',GEN/'hitter-statcast-full-history/annual-launch-features.parquet',
           GEN/'foreign-origin-inputs/origin-inputs.json',GEN/'foreign-borrowed-stability/profiles.json',
           GEN/'hitter-incumbent-representation-audit/inventory.json',ROOT/'docs/hitter-incumbent-representation-review.md']
    source_cases=[]
    OUT.mkdir(parents=True, exist_ok=True)
    for fold in range(5):
        translation=read(BRIDGE/f'translation-{fold}.json')
        assert translation['features_sha256']==sha256_file(BRIDGE/f'features-{fold}.parquet')
        graph={g['cutoff']:g for g in translation['graphs']}
        for g in graph.values():
            assert g['held_fold']==fold and all(player_fold(pid)!=fold for pid in g['people'])
        overlay=[]
        for row in frame.iter_rows(named=True):
            origin=row['origin_year']; key=f'{origin}:{row["player_id"]}'; s=source.get(key); p=profiles.get((key,fold))
            check_cutoff(row,s)
            g=graph[origin]
            nmlb=sum(RECENCY[k]*float(row[f'pa_{k}']) for k in range(3))
            _,foreign_note=foreign_evidence(s,p,origin=origin,outer_fold=fold,own_fold=row['outer_fold'],mlb_exposure=nmlb,minor_exposure=0.)
            minor,minor_note=minor_evidence(history[row['player_id']],g,origin=origin,mlb_exposure=nmlb,
                                            foreign_exposure=foreign_note['supported_precision_PA'])
            overseas,foreign_note=foreign_evidence(s,p,origin=origin,outer_fold=fold,own_fold=row['outer_fold'],
                mlb_exposure=nmlb,minor_exposure=minor_note['supported_precision_PA'])
            jobs=job_evidence(row,s)
            overlay.append(dict(row_id=row['row_id'],**minor,**overseas,**jobs))
            if row['row_id'] in selected and row['outer_fold']==fold:
                source_cases.append(dict(row_id=row['row_id'],player_id=row['player_id'],player_name=row['player_name'],
                    origin_year=origin,fold=fold,information_date=row['ctx_information_date'],
                    minor=minor_note,foreign=foreign_note,jobs=jobs,new_source_features={**minor,**overseas,**jobs}))
        f=frame.join(pl.DataFrame(overlay),on='row_id',validate='1:1')
        f=f.with_columns(pl.when(pl.col('position_outfield_unspecified')>0).then(0).otherwise(pl.col('position_UNKNOWN')).alias('position_UNKNOWN'))
        assert np.isfinite(safe_matrix(f,arms['overseas'])).all()
        cache=OUT/f'features-{fold}.parquet'
        if cache.exists():
            assert pl.read_parquet(cache).equals(f), 'Cached source representation changed'
        else:
            f.write_parquet(cache)
        paths += [OUT/f'features-{fold}.parquet',BRIDGE/f'translation-{fold}.json',BRIDGE/f'features-{fold}.parquet']
        print(f'Fold {fold}: {len(f)} source-only rows; tracking, coherent precision and jobs assembled.',flush=True)
    supports=[]; profiles_out=[]; ranges=[]; cells=[]
    keys=['prior_debut','stage','age_group','mlb_exposure','foreign_source','first_team_history','restriction_profile']
    for c in old_pre['cells']:
        y,k=c['year'],c['fold']; f=pl.read_parquet(OUT/f'features-{k}.parquet')
        tr=f.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        te=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('row_id')
        assert tr['ctx_information_date'].max()<te['ctx_information_date'].min()
        assert np.isfinite(tr['actual_relative_rate'].to_numpy()).all() and np.isfinite(te['actual_relative_rate'].to_numpy()).all()
        assert not set(tr['player_id']) & set(te['player_id'])
        checks={}
        for head,names,sub in [('participation',job_names,tr),('conditional_pa',job_names,tr.filter(pl.col('next_pa')>0)),
            ('domestic_rate',arms['domestic'],tr.filter(pl.col('next_pa')>0)),
            ('overseas_rate',arms['overseas'],tr.filter(pl.col('next_pa')>0))]:
            sup,note=preflight(sub,te,cutoff=y,fold=k,features=names,expected_keys=te.select('row_id','horizon').iter_rows())
            checks[head]=note; supports.append(sup.with_columns(pl.lit(head).alias('head'),pl.lit(k).alias('test_fold')))
            cnt=tags(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
            profiles_out.append(tags(te).select('row_id',*keys).join(cnt,on=keys,how='left',validate='m:1').with_columns(
                pl.col('profile_people').fill_null(0),pl.lit(y).alias('origin_year'),pl.lit(k).alias('test_fold'),pl.lit(head).alias('head')))
            x=safe_matrix(sub,names) if head.endswith('_rate') else sub.select(names).to_numpy()
            tx=safe_matrix(te,names) if head.endswith('_rate') else te.select(names).to_numpy()
            for i,n in enumerate(names):
                lo,hi=float(x[:,i].min()),float(x[:,i].max())
                ids=te.filter(pl.Series((tx[:,i]<lo)|(tx[:,i]>hi)))['row_id'].to_list()
                if ids:ranges.append(dict(origin=y,fold=k,head=head,feature=n,minimum=lo,maximum=hi,row_ids=ids))
        cells.append(dict(**{n:c[n] for n in ['year','fold','information_date','training_row_ids','test_row_ids']},checks=checks))
        print(f'{y}/{k}: all four actual fit checks completed, difficult rows retained.',flush=True)
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    pl.concat(profiles_out).write_parquet(OUT/'profile-support.parquet')
    save('source-cases.json',source_cases);save('feature-ranges.json',dict(warnings=ranges))
    paths += [OUT/n for n in ['support.parquet','profile-support.parquet','source-cases.json','feature-ranges.json']]
    eval_ids=[r for c in cells for r in c['test_row_ids']]
    assert len(eval_ids)==len(set(eval_ids))==30519
    save('preflight.json',dict(before_fitting=True,new_fits=0,checks_before_fits=140,
        cells=cells,arms=arms,job_features=job_names,removed_redundant_minor_rates=removed,
        settings=old_pre['settings'],ridge_alpha=100,source_rows=63314,original_evaluation_rows=30506,
        addition_evaluation_rows=13,source_hashes={str(p):sha256_file(p) for p in paths},
        source_player_walkthrough_status='pending',player_walkthrough_status='pending',
        protected_outcomes_used=False,deployment_approved=False))
    print('140 actual checks sealed before any fit; source walkthrough is still required.',flush=True)


if __name__=='__main__':main()
