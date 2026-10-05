"""Unlabeled production preflight, preserving the actually tested route and folds."""
from pathlib import Path
import json
import hashlib
import numpy as np
import polars as pl
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_talent_bridge import PROFILE_FEATURES,SCOUT_FEATURES
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'model_artifacts/hitter-selected-2026-production'
CONTRACT=ROOT/'docs/hitter-2026-production-fit-contract.md'


def read(p):return json.loads(p.read_text(encoding='utf8'))


def write(p,o):
    assert not p.exists(),f'Preserve {p}'
    p.write_text(json.dumps(o,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8',newline='\n')


def profile(f):
    return f.with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_band'),
        pl.when(pl.col('elapsed')<0).then(-1).when(pl.col('elapsed')<=2).then(0).when(pl.col('elapsed')<=5).then(1).otherwise(2).alias('career_band'),
        pl.when(pl.col('quality_0')<-.5).then(0).when(pl.col('quality_0')<.5).then(1).otherwise(2).alias('quality_band'),
        pl.when(pl.col('source_position')=='2').then(pl.lit('C')).when(pl.col('source_position').is_in(['4','6','8'])).then(pl.lit('middle'))
            .when(pl.col('source_position')=='UNKNOWN').then(pl.lit('unknown')).otherwise(pl.lit('other')).alias('position_band'))


def checks(train,test,names,head,fold):
    assert len(train)>100 and train['player_id'].n_unique()>100 and len(test)>0
    assert train['target_year'].max()<=2025 and not (train['target_year']==2020).any()
    assert (train['target_year']==train['origin_year']+1).all()
    assert not set(train['player_id'])&set(test['player_id'])
    assert (train['outer_fold']!=fold).all() and (test['outer_fold']==fold).all()
    assert train['window_complete'].all()
    assert train.unique('row_id').height==len(train) and test.unique('row_id').height==len(test)
    assert not any(c.startswith('next_') for c in names)
    assert not any(c.startswith('next_') for c in test.columns)
    assert set(test['origin_year'])=={2025} and set(test['target_year'])=={2026}
    assert np.isfinite(train.select(names).to_numpy().astype(float)).all() and np.isfinite(test.select(names).to_numpy().astype(float)).all()
    assert np.isfinite(train['next_pa'].to_numpy()).all() and train['next_pa'].min()>=0
    if head=='participation':assert set(train['next_active'])=={0,1}
    else:assert train['next_pa'].min()>0
    if head.startswith('rate'):assert np.isfinite(train['next_batting_rate'].to_numpy()).all()
    groups=[['stage','prior_debut','career_band'],['stage','prior_debut','age_band','current_state','quality_band'],
            ['stage','prior_debut','age_band','current_state','regular_window','position_band']]
    tagged_train,tagged_test=profile(train),profile(test);supports=[]
    for i,keys in enumerate(groups):
        n=tagged_train.group_by(keys).agg(pl.col('player_id').n_unique().alias('training_people'))
        supports.append(tagged_test.select('row_id',*keys).join(n,on=keys,how='left',validate='m:1')
            .with_columns(pl.col('training_people').fill_null(0),pl.lit(head).alias('head'),pl.lit(fold).alias('fold'),pl.lit(i).alias('profile_kind')))
    out=pl.concat(supports,how='diagonal_relaxed');ranges=[]
    for c in ['age','elapsed','quality_0','career_mlb_observed_pa','pa_0','minor_pa_0','regular_window']:
        lo,hi=train[c].min(),train[c].max();outside=test.filter((pl.col(c)<lo)|(pl.col(c)>hi))
        ranges.append(dict(feature=c,minimum=lo,maximum=hi,forecast_row_ids=outside['row_id'].to_list()))
    w=weights(train)
    if head.startswith('rate'):w*=train['next_pa'].to_numpy();w*=len(w)/w.sum()
    assert np.isfinite(w).all() and (w>0).all() and np.isclose(w.mean(),1.)
    return out,dict(head=head,fold=fold,training_rows=len(train),training_people=train['player_id'].n_unique(),
        active_training=head!='participation',max_target_year=int(train['target_year'].max()),
        repaired_origin2020_rows=int((train['origin_year']==2020).sum()),forecast_rows=len(test),
        feature_count=len(names),sparse_profile_rows=out.filter(pl.col('training_people')<20)['row_id'].n_unique(),
        unseen_profile_rows=out.filter(pl.col('training_people')==0)['row_id'].n_unique(),
        unknown_age_rows=int(test['age_unknown'].sum()),ranges=ranges,
        weight_sha256=hashlib.sha256(w.astype('<f8').tobytes()).hexdigest(),
        training_row_ids=train['row_id'].to_list(),feature_names=names,integrity_pass=True,
        support_claim='Profile warnings retained; integrity does not certify all forecasts.')


def main():
    OUT.mkdir(parents=True,exist_ok=True);assert not (OUT/'preflight.json').exists()
    gate_dirs=['hitter-base-inputs-2025-reviewed','hitter-translation-inputs-2025','hitter-tested-training-membership',
               'hitter-availability-2025-source','hitter-forecast-population-2025-review']
    paths=[CONTRACT,Path(__file__),ROOT/'scripts/prepare_practical_hitter_v33.py',ROOT/'scripts/fit_practical_hitter_v31.py'];gates={}
    for name in gate_dirs:
        path=ROOT/f'reports/generated/{name}/review.json';r=read(path);gates[name]=r;paths.append(path)
        for kind in ['input_hashes','output_hashes']:
            for p,h in r[kind].items():assert sha256_file(Path(p))==h,(name,p)
        assert not r['protected_outcomes_used'] and not r['candidate_frozen']
    assert gates['hitter-tested-training-membership']['all_modern_rows_now_source_checked']
    assert gates['hitter-availability-2025-source']['historical_overrides_unchanged']
    pa_pre_path=ROOT/'reports/generated/hitter-preseason-readiness-v68/preflight.json';pa_pre=read(pa_pre_path)
    numeric_pre_path=ROOT/'reports/generated/practical-hitter-numeric-repair-v53/preflight.json';numeric_pre=read(numeric_pre_path)
    sc_pre_path=ROOT/'reports/generated/hitter-statcast-next-year/preflight.json';sc_pre=read(sc_pre_path)
    names=dict(participation=pa_pre['pa_features'],conditional_pa=pa_pre['pa_features'],rate_numeric=numeric_pre['rate_features'],
        rate_tracking=sc_pre['arms']['ridge_measurements'],rate_prospect=numeric_pre['rate_features']+SCOUT_FEATURES+PROFILE_FEATURES)
    assert [len(names[n]) for n in names]==[251,251,199,262,220]
    paths.extend([pa_pre_path,numeric_pre_path,sc_pre_path])
    modern_path=ROOT/'reports/generated/hitter-preseason-readiness-v68/features.parquet';modern=pl.read_parquet(modern_path);paths.append(modern_path)
    tracking_path=ROOT/'reports/generated/hitter-statcast-next-year/features.parquet';tracking=pl.read_parquet(tracking_path);paths.append(tracking_path)
    for c in ['row_id','player_id','origin_year','next_pa','next_batting_rate','next_active']:
        assert modern.sort('row_id')[c].equals(tracking.sort('row_id')[c]),c
    availability_path=ROOT/'reports/generated/hitter-availability-2025-source/availability.parquet';status=pl.read_parquet(availability_path);paths.append(availability_path)
    supports=[];cells=[];forecast_count=0
    for fold in range(5):
        q_path=ROOT/f'reports/generated/hitter-translation-inputs-2025/forecast-inputs-{fold}.parquet'
        t_path=ROOT/f'reports/generated/hitter-talent-bridge-v74/features-{fold}.parquet';paths.extend([q_path,t_path])
        q=pl.read_parquet(q_path).filter(pl.col('outer_fold')==fold).join(status.drop('player_id'),on='row_id',validate='1:1').sort('row_id')
        assert all(player_fold(pid)==fold for pid in q['player_id'])
        transit=pl.read_parquet(t_path)
        train_ids=modern.filter((pl.col('target_year')<=2025)&(pl.col('target_year')!=2020)&(pl.col('outer_fold')!=fold)&pl.col('window_complete'))['row_id'].to_list()
        tr=modern.filter(pl.col('row_id').is_in(train_ids)).sort('row_id');active=tr.filter(pl.col('next_pa')>0)
        active_ids=active['row_id'].to_list()
        head_frames=dict(participation=tr,conditional_pa=active,rate_numeric=active,
            rate_tracking=tracking.filter(pl.col('row_id').is_in(active_ids)).sort('row_id'),
            rate_prospect=transit.filter(pl.col('row_id').is_in(active_ids)).sort('row_id'))
        head_checks=[]
        for head,train in head_frames.items():
            sup,note=checks(train,q,names[head],head,fold);supports.append(sup);head_checks.append(note)
            if head.startswith('rate'):assert np.isfinite(safe_matrix(train,names[head])).all() and np.isfinite(safe_matrix(q,names[head])).all()
        q.write_parquet(OUT/f'inputs-{fold}.parquet');forecast_count+=len(q)
        cells.append(dict(fold=fold,training_row_ids=train_ids,active_training_row_ids=active_ids,forecast_row_ids=q['row_id'].to_list(),heads=head_checks))
        print(f'Fold {fold}: five actual-head preflights complete, {len(q)} unlabeled forecasts; no fits.',flush=True)
    assert forecast_count==4030
    pl.concat(supports,how='diagonal_relaxed').write_parquet(OUT/'profile-support.parquet')
    write(OUT/'preflight.json',dict(before_fitting=True,contract_sha256=sha256_file(CONTRACT),cells=cells,features=names,
        histogram_settings=pa_pre['settings'],ridge_alpha=100,forecast_population=4030,model_heads_to_fit=25,
        actual_tested_training_rule=gates['hitter-tested-training-membership']['actual_retained_rule'],
        origin_year=2025,target_year=2026,origin_replacement_reference=570/182926,
        coverage=gates['hitter-forecast-population-2025-review']['qualification'],
        unmodeled_rostered_nonpitchers=3,universal_coverage_claim_allowed=False,source_integrity_pass=True,
        support_warnings_are_not_removed=True,candidate_fitted=False,candidate_frozen=False,protected_outcomes_used=False,
        next_steps=['Fit fixed heads once','Replay and player reasonability review','Immutable qualified candidate freeze','Authorized final 2026 evaluation'],
        input_hashes={str(p):sha256_file(p) for p in paths},
        output_hashes={str(p):sha256_file(p) for p in OUT.iterdir() if p.suffix in ['.json','.parquet']}))


if __name__=='__main__':main()
