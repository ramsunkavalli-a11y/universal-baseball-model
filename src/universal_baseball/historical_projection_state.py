"""Validated dated forecast states and mature realized-error vectors."""
import numpy as np
import polars as pl

KEYS=['origin_year','player_id','horizon']


def conditional_workload(probability, expected_pa):
    p,pa=np.asarray(probability,float),np.asarray(expected_pa,float)
    if not np.isfinite(p).all() or not np.isfinite(pa).all() or ((p<0)|(p>1)|(pa<0)).any():
        raise ValueError('Invalid opportunity')
    if ((p==0)&(pa>0)).any():raise ValueError('Positive PA with zero participation')
    return np.divide(pa,p,out=np.full_like(pa,np.nan),where=p>0)


def validate_states(frame):
    if frame.select(KEYS).null_count().row(0)!= (0,0,0):raise ValueError('Missing forecast key')
    if frame.select(KEYS).is_duplicated().any():raise ValueError('Duplicate forecast key')
    if frame['source_cutoff'].null_count() or frame.filter(pl.col('source_cutoff')!=pl.col('origin_year')).height:
        raise ValueError('Source cutoff differs from origin')
    if frame.filter((pl.col('origin_year')>2025)|(pl.col('horizon')<1)|(pl.col('horizon')>3)).height:
        raise ValueError('Protected or unsupported vintage')
    for c in ('opportunity_latest_label','rate_latest_label','anchor_latest_label','value_latest_label'):
        if frame[c].null_count() or frame.filter(pl.col(c)>pl.col('origin_year')).height:
            raise ValueError('Future or undocumented fitted vintage: '+c)
    for c in ('h1_rate_anchor','research_conditional_rate','delivered_value','delivered_p','delivered_pa'):
        if not np.isfinite(frame[c].to_numpy()).all():raise ValueError('Missing forecast: '+c)
    p,pa=frame['delivered_p'].to_numpy(),frame['delivered_pa'].to_numpy()
    expected=conditional_workload(p,pa)
    np.testing.assert_allclose(frame['delivered_conditional_pa'],expected,equal_nan=True,rtol=1e-10,atol=1e-10)
    counts=frame.group_by('origin_year','player_id').agg(pl.col('horizon').n_unique())
    if (counts['horizon']!=3).any():raise ValueError('Incomplete forecast vector')


def residual_ledger(states,panel):
    """Outcome observations are separate from predictors and never zero-fill missing years."""
    rows=[]
    for h in (1,2,3):
        f=states.filter(pl.col('horizon')==h).join(panel.select('origin_year','player_id',
            pl.col(f'war_h{h}').alias('actual_value'),pl.col(f'pa_h{h}').alias('actual_pa')),
            on=['origin_year','player_id'],how='left',validate='1:1',maintain_order='left')
        rows.append(f.with_columns((pl.col('origin_year')+h).alias('outcome_year'),
            (pl.col('actual_value')-pl.col('delivered_value')).alias('value_residual'),
            (pl.col('actual_pa')-pl.col('delivered_pa')).alias('pa_residual'),
            pl.when(pl.col('actual_pa')>0).then(600*pl.col('actual_value')/pl.col('actual_pa')).otherwise(None).alias('observed_active_rate')))
    return pl.concat(rows).sort(KEYS)


def mature_vectors(ledger,cutoff,excluded_ids=()):
    if cutoff>2025:raise ValueError('Protected cutoff')
    if ledger.select(KEYS).is_duplicated().any():raise ValueError('Duplicate residual key')
    f=ledger.filter((pl.col('origin_year')+3<=cutoff)&~((pl.col('origin_year')<2020)&(pl.col('origin_year')+3>=2020))
        &~pl.col('player_id').is_in(list(excluded_ids)))
    complete=f.group_by('origin_year','player_id').agg(pl.col('horizon').n_unique().alias('n'),
        (pl.col('actual_value').is_finite()&pl.col('actual_pa').is_finite()).fill_null(False).all().alias('complete'))
    keys=complete.filter((pl.col('n')==3)&pl.col('complete')).select('origin_year','player_id')
    return f.join(keys,on=['origin_year','player_id'],how='inner',validate='m:1').sort(KEYS)
