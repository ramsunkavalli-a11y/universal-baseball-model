"""Chronological talent stacking and immutable historical draft evidence."""
import numpy as np
import polars as pl
from universal_baseball.hitter_conditional_workload import active_training, fit_head
from universal_baseball.hitter_canceled_season import matrix
from universal_baseball.hitter_model_tournament import make_engine_models

TALENT = ['talent_rate_h1', 'talent_supported_h1', 'talent_rate_h3', 'talent_supported_h3']
PEDIGREE = ['pedigree_matched', 'pedigree_pick_quality', 'pedigree_high_school',
            'pedigree_school_known', 'pedigree_years_since']


def pedigree_features(panel, draft):
    """Only immutable selection facts; no bonuses or later evaluator opinions."""
    pieces = []
    for (year,), q in panel.partition_by('origin_year', as_dict=True).items():
        d = draft.filter((pl.col('draft_year') <= year) & (pl.col('pick_number') > 0))
        if d.height:
            d = d.with_columns(pl.col('pick_number').max().over('draft_year').alias('_max'))
            d = d.with_columns((1-pl.col('pick_number').log()/pl.col('_max').clip(lower_bound=2).log())
                .clip(0,1).alias('pedigree_pick_quality'))
            d = d.sort('player_id','draft_year','pick_number').unique('player_id',keep='last')
            d = d.select('player_id',pl.lit(1).alias('pedigree_matched'),'pedigree_pick_quality',
                pl.col('school_class').fill_null('').str.contains('HS').cast(pl.Int8).alias('pedigree_high_school'),
                (pl.col('school_class').fill_null('')!='').cast(pl.Int8).alias('pedigree_school_known'),
                (year-pl.col('draft_year')).alias('pedigree_years_since'))
            q = q.join(d,on='player_id',how='left',validate='m:1',maintain_order='left')
            q = q.with_columns(pl.col('pedigree_matched').fill_null(0))
        else:
            q = q.with_columns(pl.lit(0).alias('pedigree_matched'),
                              *[pl.lit(None,dtype=pl.Float64).alias(c) for c in PEDIGREE[1:]])
        pieces.append(q)
    return pl.concat(pieces,how='vertical_relaxed').sort('origin_year','player_id')


def talent_training(panel, year, horizon):
    t = active_training(panel,year,horizon).filter(pl.col(f'war_h{horizon}').is_finite().fill_null(False))
    return t.with_columns((1/pl.len().over('player_id')).alias('identity_weight'))


def fit_talent(panel, columns, year, horizon):
    if horizon not in (1,3): raise ValueError('Only fixed talent horizons 1 and 3')
    if any(c.startswith(('pa_h','war_h','talent_','pedigree_')) or c in ('player_id','origin_year') for c in columns):
        raise ValueError('Leaking or recursive talent feature')
    t = talent_training(panel,year,horizon)
    q = panel.filter(pl.col('origin_year')==year).sort('player_id')
    origins = sorted(t['origin_year'].unique().to_list())
    supported = t.height>=200 and len(origins)>=2
    note = {'year':year,'horizon':horizon,'training_rows':t.height,
            'training_players':t['player_id'].n_unique(),'training_origins':origins,
            'latest_label':max(origins)+horizon if origins else None,'supported':supported}
    if not supported: return np.full(q.height,np.nan),note
    x=matrix(t,columns)
    keep=[c for j,c in enumerate(columns) if len(np.unique(x[np.isfinite(x[:,j]),j]))>1]
    y=600*t[f'war_h{horizon}'].to_numpy()/t[f'pa_h{horizon}'].to_numpy()
    w=t['identity_weight'].to_numpy()*t[f'pa_h{horizon}'].to_numpy();w=w/w.mean()
    assert np.isfinite(y).all() and keep
    model=make_engine_models('lightgbm',427,'balanced').regressor.set_params(n_jobs=4)
    model.fit(matrix(t,keep),y,sample_weight=w)
    pred=np.clip(model.predict(matrix(q,keep)),-5,10)
    return pred,{**note,'used_features':keep,'clipped_predictions':int(((pred==-5)|(pred==10)).sum())}


def fit_workload(panel, columns, year, horizon, arm):
    extra={'T':TALENT,'P':PEDIGREE,'TP':TALENT+PEDIGREE}[arm]
    prediction,_,note=fit_head(panel,columns+extra,year,horizon,'D')
    return prediction,{**note,'arm':arm}
