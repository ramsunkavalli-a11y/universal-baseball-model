"""Origin-known level/age representation and horizon-aware shared rate design."""
import numpy as np
import polars as pl

LEVELS=['MLB','AAA','AA','Aplus','A','Aminus','RK120','RK121','RK124','RK128','RK134','RKother','DSL','MEX','absent']
LEVEL_FEATURES=[f'development_level_{b}' for b in LEVELS]
AGE_FEATURES=[f'development_age_{b}' for b in LEVELS]
HORIZON_FEATURES=[n for h in range(2,7) for n in [f'development_horizon_{h}',f'development_horizon_age_{h}',
    *[f'development_horizon_{h}_{b}' for b in LEVELS]]]


def representation(frame):
    if not set(frame['dominant_level']).issubset(LEVELS): raise ValueError('Unknown level')
    if not frame['horizon'].is_between(1,6).all(): raise ValueError('Unknown horizon')
    result=frame.with_columns(*[(pl.col('dominant_level')==b).cast(pl.Float64).alias(f'development_level_{b}') for b in LEVELS])
    result=result.with_columns(*[(pl.col(f'development_level_{b}')*pl.col('age_centered')).alias(f'development_age_{b}') for b in LEVELS])
    for h in range(2,7):
        result=result.with_columns((pl.col('horizon')==h).cast(pl.Float64).alias(f'development_horizon_{h}'))
        result=result.with_columns((pl.col(f'development_horizon_{h}')*pl.col('age_centered')).alias(f'development_horizon_age_{h}'),
            *[(pl.col(f'development_horizon_{h}')*pl.col(f'development_level_{b}')).alias(f'development_horizon_{h}_{b}') for b in LEVELS])
    return result


def preflight_shared(train,test,cutoff,held_fold,features,expected_ids):
    for frame in [train,test]:
        if not len(frame) or frame.unique(['player_id','origin_year','horizon']).height!=len(frame): raise ValueError('Empty/duplicate observations')
        if not np.isfinite(frame.select(features).to_numpy()).all(): raise ValueError('Invalid predictor matrix')
        if frame['origin_year'].max()>2024 or frame['target_year'].max()>2025: raise ValueError('Protected season')
        if not (frame['target_year']==frame['origin_year']+frame['horizon']).all(): raise ValueError('Horizon mismatch')
    if not (train['next_pa']>0).all() or not np.isfinite(train['next_batting_rate'].to_numpy()).all(): raise ValueError('Unobserved training talent')
    if train['target_year'].max()>cutoff or (train['target_year']==2020).any(): raise ValueError('Unmatured/excluded outcomes')
    if set(train['player_id'])&set(test['player_id']) or (train['outer_fold']==held_fold).any(): raise ValueError('Held player contamination')
    if not (test['origin_year']==cutoff).all() or not (test['outer_fold']==held_fold).all() or not (test['horizon']==1).all(): raise ValueError('Wrong test context')
    if test['row_id'].to_list()!=expected_ids: raise ValueError('Evaluation changed')
    if any(n.startswith(('next_','target_')) for n in features): raise ValueError('Outcome predictor')
    return dict(integrity_pass=True,training_observations=len(train),training_people=train['player_id'].n_unique(),
        training_origins=train['origin_year'].n_unique(),maximum_training_target=int(train['target_year'].max()),
        training_horizons=sorted(train['horizon'].unique().to_list()),test_rows=len(test),
        claim='execution_only_not_profile_or_predictive_certification')
