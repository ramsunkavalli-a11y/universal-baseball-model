"""Separate execution integrity, training support and predictive certification."""
import numpy as np
import polars as pl


def _profiles(frame):
    return frame.with_columns(
        pl.when(pl.col('elapsed') == 0).then(0).when(pl.col('elapsed') <= 2).then(1).otherwise(2).alias('elapsed_band'),
        pl.when(pl.col('age') <= 22).then(0).when(pl.col('age') <= 25).then(1).when(pl.col('age') <= 28).then(2).otherwise(3).alias('age_band'),
        pl.when(pl.col('quality_0') <= -1).then(0).when(pl.col('quality_0') <= 1).then(1).otherwise(2).alias('quality_band'))


def preflight(train, test, *, cutoff, fold, features, expected_keys):
    """Integrity errors raise; inadequate support tags forecasts, never drops them."""
    for f in [train, test]:
        if f.is_empty() or f.unique(['player_id', 'origin_year', 'horizon']).height != f.height:
            raise ValueError('Empty or duplicate forecast population')
        if not np.isfinite(f.select(features).to_numpy()).all() or not f['window_complete'].all():
            raise ValueError('Uncertified or missing feature history')
        if f['target_year'].max() > 2025 or f['origin_year'].max() > 2024:
            raise ValueError('Protected season')
        if (f['target_year'] != f['origin_year']+f['horizon']).any():
            raise ValueError('Target horizon mismatch')
        pa, value = f['next_pa'].to_numpy(), f['next_value'].to_numpy()
        if not np.isfinite(pa).all() or not np.isfinite(value).all() or (pa < 0).any() or (value[pa == 0] != 0).any():
            raise ValueError('Invalid delivered-value labels')
    if set(train['player_id']) & set(test['player_id']) or (train['outer_fold'] == fold).any():
        raise ValueError('Held-player contamination')
    if (train['target_year'] > cutoff).any() or (train['target_year'] == 2020).any():
        raise ValueError('Unmatured or excluded training outcomes')
    if not (test['origin_year'] == cutoff).all() or not (test['outer_fold'] == fold).all():
        raise ValueError('Incorrect test cutoff or fold')
    if set(test.select('row_id', 'horizon').iter_rows()) != set(expected_keys):
        raise ValueError('Evaluation population changed')
    if train['horizon'].n_unique() != 1 or train['horizon'][0] != test['horizon'][0] or test['horizon'].n_unique() != 1:
        raise ValueError('Mixed or mismatched horizons')
    a, b = _profiles(train), _profiles(test)
    columns = ['row_id', 'horizon', 'player_id', 'origin_year', 'elapsed', 'current_state', 'regular_window', 'age',
        'quality_0', 'elapsed_band', 'age_band', 'quality_band']
    b = b.select(columns)
    groups = {'elapsed': ['elapsed'], 'current': ['current_state'], 'regular': ['regular_window'],
        'joint': ['elapsed_band', 'current_state', 'age_band'], 'quality_joint': ['elapsed_band', 'current_state', 'quality_band']}
    for name, keys in groups.items():
        counts = a.group_by(keys).agg(pl.col('player_id').n_unique().alias(f'{name}_players'))
        b = b.join(counts, on=keys, how='left', validate='m:1').with_columns(pl.col(f'{name}_players').fill_null(0))
    b = b.with_columns(
        ((pl.col('elapsed') < a['elapsed'].min()) | (pl.col('elapsed') > a['elapsed'].max())).alias('elapsed_outside'),
        ((pl.col('age') < a['age'].min()) | (pl.col('age') > a['age'].max())).alias('age_outside'),
        ((pl.col('quality_0') < a['quality_0'].min()) | (pl.col('quality_0') > a['quality_0'].max())).alias('quality_outside'),
        pl.any_horizontal([pl.col(f'{g}_players') == 0 for g in groups]).alias('unseen_profile'),
        pl.any_horizontal([pl.col(f'{g}_players') < 20 for g in groups]).alias('sparse_profile'))
    b = b.with_columns(pl.any_horizontal('elapsed_outside', 'age_outside', 'quality_outside', 'unseen_profile').alias('extrapolation'))
    b = b.with_columns((~pl.col('extrapolation') & ~pl.col('sparse_profile')).alias('profile_check_pass'))
    note = {'integrity_pass': True, 'training_rows': a.height, 'training_players': a['player_id'].n_unique(),
        'test_rows': b.height, 'min_training_elapsed': a['elapsed'].min(), 'max_training_elapsed': a['elapsed'].max(),
        'three_regular_training_players': a.filter(pl.col('regular_window') == 3)['player_id'].n_unique(),
        **{c: int(b[c].sum()) for c in ['elapsed_outside', 'age_outside', 'quality_outside', 'unseen_profile', 'sparse_profile', 'extrapolation', 'profile_check_pass']},
        'full_cohort_profile_check_pass': bool(b['profile_check_pass'].all()),
        'claim': 'profile_checks_only_not_predictive_validation'}
    return b, note


def claim_status(*, integrity, full_profile_support, predictive_gates, coherent):
    if not integrity:
        return 'invalid_execution'
    if not full_profile_support:
        return 'unsupported_for_full_cohort_certification'
    if not coherent:
        return 'incoherent_forecast_not_promotable'
    if not predictive_gates:
        return 'predictive_gates_failed'
    return 'development_evidence_only_requires_separate_deployment_review'
