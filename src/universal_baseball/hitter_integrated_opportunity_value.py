"""Fixed historical integration; assembly never uses future player outcomes."""
from __future__ import annotations

import numpy as np
import polars as pl

from universal_baseball.multiyear_hitter_components import COMPONENTS

KEY = ['origin_year', 'player_id', 'horizon']
ARMS = ('L', 'B', 'D', 'E', 'N', 'H')
META = ['age', 'stage', 'prospect', 'prior_debut', 'minor_returner',
        'recent_debut', 'mlb_pa_lag0', 'mlb_pa_lag1', 'mlb_pa_lag2', 'pa_lag0']
INPUTS = [*KEY, *META, 'player_name', 'old_pa', 'old_value', 'B_pa', 'B_p',
          'B_value', 'E_pa', 'E_p', 'E_value', 'D_pa', 'fixed_p', 'rate']


def finite(frame, columns):
    if any(frame[c].null_count() or not frame[c].is_finite().all() for c in columns):
        raise ValueError('Missing/nonfinite model inputs')


def assemble(inputs, component):
    """Direct totals remain totals; only explicit benchmark rates change exposure."""
    f = inputs.select(INPUTS).sort(KEY)
    if f.select(KEY).is_duplicated().any():
        raise ValueError('Duplicate player-horizon key')
    if not f['horizon'].is_in([1, 2, 3]).all() or (f['origin_year'] + f['horizon']).max() > 2025:
        raise ValueError('Unsupported/protected evaluation horizon')
    if f.filter(pl.col('prospect') & pl.col('prior_debut')).height:
        raise ValueError('Overlapping routing scopes')
    finite(f, ['old_pa','old_value','B_pa','B_p','B_value','E_pa','E_p',
               'E_value','D_pa','fixed_p','rate'])
    for c in ['old_pa', 'B_pa', 'E_pa', 'D_pa']:
        if not f[c].is_between(0, 750).all():
            raise ValueError('PA outside annual model bounds')
    for c in ['B_p','E_p','fixed_p']:
        if not f[c].is_between(0, 1).all():
            raise ValueError('Invalid probability')
    f = f.with_columns(
        pl.when(pl.col('prospect')).then(pl.col('D_pa'))
          .when(pl.col('prior_debut')).then(pl.col('E_pa')).otherwise(pl.col('B_pa')).alias('H_pa'),
        pl.when(pl.col('prospect')).then(pl.col('fixed_p')).otherwise(pl.col('B_p')).alias('D_p'),
        pl.when(pl.col('prospect')).then(pl.col('fixed_p'))
          .when(pl.col('prior_debut')).then(pl.col('E_p')).otherwise(pl.col('B_p')).alias('H_p'),
        pl.col('E_pa').alias('N_pa'), pl.col('E_p').alias('N_p'),
        pl.col('E_value').alias('N_value'), pl.col('old_pa').alias('L_pa'),
        pl.col('old_value').alias('L_value'),
        pl.when(pl.col('prospect')).then(pl.lit('prospect_F_D'))
          .when(pl.col('prior_debut')).then(pl.lit('prior_MLB_E'))
          .otherwise(pl.lit('remaining_B')).alias('route'))
    f = f.with_columns(*[(pl.col('B_value') + (pl.col(a+'_pa')-pl.col('B_pa'))*pl.col('rate')/600)
                          .alias(a+'_value') for a in ('D','E','H')])
    # Require exactly the original seven component records for every scoring key.
    c = component.join(f.select(KEY), on=KEY, how='inner', validate='m:1')
    if c.height != 7*f.height or c.select(*KEY,'component').is_duplicated().any():
        raise ValueError('Missing/duplicate components')
    if set(c['component']) != set(COMPONENTS):
        raise ValueError('Unexpected component inventory')
    if not c['selected_model'].is_in(['neutral','benchmark','direct']).all():
        raise ValueError('Unknown component model semantics')
    finite(c, ['benchmark_rate','benchmark','direct','selected','expected_pa','batting'])
    np.testing.assert_allclose(c['benchmark'], c['benchmark_rate']*c['expected_pa']/600, atol=1e-12)
    c = c.with_columns(pl.when(pl.col('selected_model')=='benchmark').then(pl.col('benchmark'))
        .when(pl.col('selected_model')=='direct').then(pl.col('direct')).otherwise(0.).alias('_replay'))
    np.testing.assert_allclose(c['selected'], c['_replay'], atol=1e-12)
    c = c.join(f.select(*KEY,*[a+'_pa' for a in ARMS], 'old_value'), on=KEY, validate='m:1')
    np.testing.assert_allclose(c['expected_pa'],c['L_pa'],atol=1e-10)
    np.testing.assert_allclose(c['batting'],c['old_value'],atol=1e-10)
    c = c.with_columns(pl.col('selected').alias('L_runs'), *[
        pl.when(pl.col('selected_model')=='benchmark').then(pl.col('benchmark_rate')*pl.col(a+'_pa')/600)
        .when(pl.col('selected_model')=='direct').then(pl.col('direct')).otherwise(0.).alias(a+'_runs')
        for a in ARMS if a!='L'])
    totals = c.group_by(KEY).agg(*[pl.col(a+'_runs').sum().alias(a+'_other_runs') for a in ARMS])
    f = f.join(totals, on=KEY, validate='1:1', maintain_order='left').with_columns(*[
        (pl.col(a+'_value')+pl.col(a+'_other_runs')/10).alias(a+'_expanded') for a in ARMS])
    return f, c.select(*KEY,'component','selected_model','benchmark_rate','direct',
                       *[a+'_pa' for a in ARMS],*[a+'_runs' for a in ARMS])


def profiles():
    mlb = pl.col('stage')=='Current MLB'
    return {'all':pl.lit(True), 'prospects':pl.col('prospect'),
        'upper_prospects':pl.col('prospect')&(pl.col('stage')=='Upper minors'),
        'lower_prospects':pl.col('prospect')&(pl.col('stage')=='Lower minors'),
        'prior_debut':pl.col('prior_debut'), 'current_MLB':mlb,
        'MLB_under100':mlb&(pl.col('mlb_pa_lag0')<100),
        'MLB_100_399':mlb&pl.col('mlb_pa_lag0').is_between(100,399),
        'MLB_400plus':mlb&(pl.col('mlb_pa_lag0')>=400),
        'young_brief_debut':mlb&(pl.col('age')<=25)&(pl.col('pa_lag0')>=400)&(pl.col('mlb_pa_lag0')<100),
        'minor_returner':pl.col('minor_returner'),
        'returner_recent400':pl.col('minor_returner')&(pl.max_horizontal('mlb_pa_lag1','mlb_pa_lag2')>=400),
        'age_under23':pl.col('age')<23, 'age_23_26':pl.col('age').is_between(23,27,closed='left'),
        'age_27_31':pl.col('age').is_between(27,32,closed='left'), 'age_32plus':pl.col('age')>=32}


def cumulative(f):
    if f.select(KEY).is_duplicated().any():
        raise ValueError('Duplicate horizon before cumulative sum')
    out = f.group_by('origin_year','player_id').agg(pl.len().alias('_n'),
        pl.col('horizon').n_unique().alias('_nh'),pl.col('complete_components').all(),
        *[pl.col(c).first() for c in [*META,'player_name','route']],
        *[pl.col(c).sum() for c in ['actual_pa','actual_value','actual_expanded',
                                   *[a+'_'+t for a in ARMS for t in ('pa','value','expanded')]]])
    # Null-skipping sums must never fabricate complete component labels.
    return out.filter((pl.col('_n')==3)&(pl.col('_nh')==3)).with_columns(
        pl.when(pl.col('complete_components')).then(pl.col('actual_expanded')).otherwise(None).alias('actual_expanded')
    ).sort('origin_year','player_id')
