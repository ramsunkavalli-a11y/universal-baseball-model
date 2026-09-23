"""Fixed source-outage augmentation; preserve all statistical training weights."""
import numpy as np
import polars as pl
from universal_baseball.hitter_canceled_season import matrix,hide_annual_block
from universal_baseball.hitter_detail_arrival import target_values
from universal_baseball.hitter_model_tournament import make_engine_models

FLAGS = ['structural_outage_lag1','structural_outage_lag2']


def attach_outages(frame):
    return frame.with_columns(*[
        (pl.col('prospect') & (pl.col('origin_year')-lag == 2020) &
         (pl.col(f'missing_lag{lag}') == 1)).fill_null(False).cast(pl.Int8).alias(FLAGS[lag-1])
        for lag in (1,2)])


def augmented_rows(train, masked):
    train = attach_outages(train)
    original = train.with_columns((pl.col('identity_weight')*
                 pl.when(pl.col('prospect')).then(.5).otherwise(1.)).alias('fit_weight'))
    copies = [original]
    for lag in (1,2):
        more = train.filter(pl.col('prospect'))
        if masked:
            more = hide_annual_block(more,lag).with_columns(pl.lit(1,dtype=pl.Int8).alias(FLAGS[lag-1]))
        copies.append(more.with_columns((pl.col('identity_weight')*.25).alias('fit_weight')))
    return pl.concat(copies,how='vertical_relaxed')


def fit_augmented(train, query, columns, target, masked):
    if any(c.startswith(('pa_h','war_h','target_')) or c in ('player_id','origin_year') for c in columns):
        raise ValueError('Forbidden input')
    augmented = augmented_rows(train,masked)
    query = attach_outages(query)
    cols = columns+FLAGS
    x = matrix(augmented,cols); tx = matrix(query,cols)
    keep = np.array([len(np.unique(x[np.isfinite(x[:,j]),j]))>1 for j in range(x.shape[1])])
    y = target_values(augmented,target)
    if not keep.any() or len(np.unique(y)) != 2: raise ValueError('Insufficient support')
    weight = augmented['fit_weight'].to_numpy()/float(train['identity_weight'].mean())
    model = make_engine_models('lightgbm',417,'balanced').classifier.set_params(n_jobs=4)
    model.fit(x[:,keep],y,sample_weight=weight)
    p = np.clip(model.predict_proba(tx[:,keep])[:,1],1e-6,1-1e-6)
    return p, {'training_rows':train.height,'augmented_rows':augmented.height,
        'training_origins':sorted(train['origin_year'].unique().to_list()),
        'original_weight_sum':float(train['identity_weight'].sum()),
        'augmented_weight_sum':float(augmented['fit_weight'].sum()),'normalized_weight_sum':float(weight.sum()),
        'used_features':[c for c,k in zip(cols,keep) if k],
        'dropped_constant_or_unobserved':[c for c,k in zip(cols,keep) if not k]}
