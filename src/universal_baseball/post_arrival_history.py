"""Cutoff-local minor evidence; no claim of park-neutral MLB equivalence."""
import hashlib

import numpy as np
import polars as pl

EVENTS = ['ubb', 'k', 'single', 'double', 'triple', 'hr', 'hbp']
GROUPS = ['AAA', 'AA', 'lower']
ACTIVITY_FEATURES = [f'minor_log_pa_{g}_{lag}' for g in GROUPS for lag in range(3)] + [
    f'minor_canceled_{lag}' for lag in range(3)]
PERFORMANCE_FEATURES = [f'minor_{g}_{e}' for g in GROUPS for e in EVENTS]


def player_fold(player_id):
    return int.from_bytes(hashlib.sha256(f'ubm-prospect-v8:{player_id}'.encode()).digest()[:8], 'big') % 5


def prepare_source(source):
    if source['season'].max() > 2025:
        raise ValueError('Protected source')
    key = ['season', 'player_id', 'sport_id', 'team_id']
    if source.unique(key).height != source.height:
        raise ValueError('Duplicate source identities')
    f = source.filter((pl.col('sport_id') != 1) & (pl.col('plate_appearances') > 0))
    if f.filter(pl.col('season') == 2020).height:
        raise ValueError('Canceled MiLB season has counts')
    f = f.with_columns(
        (pl.col('base_on_balls')-pl.col('intentional_walks')).alias('ubb'),
        pl.col('strike_outs').alias('k'),
        (pl.col('hits')-pl.col('doubles')-pl.col('triples')-pl.col('home_runs')).alias('single'),
        pl.col('doubles').alias('double'), pl.col('triples').alias('triple'),
        pl.col('home_runs').alias('hr'), pl.col('hit_by_pitch').alias('hbp'))
    if any(f[c].null_count() for c in [*EVENTS, 'plate_appearances']):
        raise ValueError('Missing component counts')
    if f.filter(pl.any_horizontal(pl.col(EVENTS) < 0) | (pl.sum_horizontal(EVENTS) > pl.col('plate_appearances'))).height:
        raise ValueError('Invalid mutually exclusive counts')
    f = f.group_by('season', 'player_id', 'sport_id', 'level_group').agg(pl.col('plate_appearances', *EVENTS).sum())
    return f.with_columns(
        pl.when(pl.col('sport_id') == 11).then(pl.lit('AAA'))
        .when(pl.col('sport_id') == 12).then(pl.lit('AA')).otherwise(pl.lit('lower')).alias('minor_group'),
        pl.Series('source_fold', [player_fold(i) for i in f['player_id']]))


def add_history(panel, source, held_fold):
    """Peer means exclude held identities, are local to each observed season/level."""
    if panel['origin_year'].max() > 2024:
        raise ValueError('Unsupported forecast origin')
    keys = ['season', 'sport_id', 'level_group']
    peers = source.filter((pl.col('source_fold') != held_fold) & (pl.col('season') <= panel['origin_year'].max()))
    means = peers.group_by(keys).agg(*[(pl.col(e).sum()/pl.col('plate_appearances').sum()).alias(f'mean_{e}') for e in EVENTS])
    observed = source.filter(pl.col('season') <= panel['origin_year'].max()).join(means, on=keys, how='left', validate='m:1')
    if any(observed[f'mean_{e}'].null_count() for e in EVENTS):
        raise ValueError('No nonheld seasonal peers')
    observed = observed.with_columns(*[(pl.col(e)-pl.col('plate_appearances')*pl.col(f'mean_{e}')).alias(f'excess_{e}') for e in EVENTS])
    observed = observed.group_by('season', 'player_id', 'minor_group').agg(pl.col('plate_appearances', *[f'excess_{e}' for e in EVENTS]).sum())
    out = panel
    for g in GROUPS:
        for lag in range(3):
            sub = observed.filter(pl.col('minor_group') == g).select(
                (pl.col('season')+lag).alias('origin_year'), 'player_id',
                pl.col('plate_appearances').alias(f'minor_pa_{g}_{lag}'),
                *[pl.col(f'excess_{e}').alias(f'excess_{g}_{e}_{lag}') for e in EVENTS])
            out = out.join(sub, on=['origin_year', 'player_id'], how='left', validate='1:1')
            cols = [f'minor_pa_{g}_{lag}', *[f'excess_{g}_{e}_{lag}' for e in EVENTS]]
            out = out.with_columns(pl.col(cols).fill_null(0))
            out = out.with_columns((pl.col(f'minor_pa_{g}_{lag}')/600).log1p().alias(f'minor_log_pa_{g}_{lag}'))
        total = pl.sum_horizontal([f'minor_pa_{g}_{lag}' for lag in range(3)])
        out = out.with_columns(*[(pl.sum_horizontal([f'excess_{g}_{e}_{lag}' for lag in range(3)])/(total+1200)).alias(f'minor_{g}_{e}') for e in EVENTS])
    out = out.with_columns(*[((pl.col('origin_year')-lag) == 2020).cast(pl.Int8).alias(f'minor_canceled_{lag}') for lag in range(3)],
        pl.sum_horizontal([f'minor_pa_{g}_{lag}' for g in GROUPS for lag in range(3)]).alias('minor_history_pa'),
        pl.sum_horizontal([f'minor_pa_{g}_0' for g in GROUPS]).alias('minor_current_pa'))
    if not np.isfinite(out.select(ACTIVITY_FEATURES+PERFORMANCE_FEATURES).to_numpy()).all():
        raise ValueError('Nonfinite history')
    return out, means
