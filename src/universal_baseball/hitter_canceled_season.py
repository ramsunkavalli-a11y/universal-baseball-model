"""Research routing for an exogenous missing annual input block, not inactivity."""
import numpy as np
import polars as pl
from universal_baseball.hitter_detail_arrival import target_values
from universal_baseball.hitter_model_tournament import make_engine_models


def annual_block(column, lag):
    return column.endswith(f'_lag{lag}') or column.startswith(
        tuple(f'{source}{lag}__' for source in ('raw','park','pitch','context')))


def available_columns(columns, omitted):
    if not set(omitted) <= {1,2} or not omitted:
        raise ValueError('Only prior annual blocks may be omitted')
    return [c for c in columns if not any(annual_block(c,k) for k in omitted)
            and not (1 in omitted and c.startswith('change__'))]


def outage_mask(frame, year):
    lag = year-2020
    if lag not in (1,2): return np.zeros(frame.height, dtype=bool)
    return (frame['prospect'] & (frame[f'missing_lag{lag}'] == 1)).fill_null(False).to_numpy()


def hide_annual_block(frame, lag):
    """Stress only the query's annual block, keeping cumulative career knowledge."""
    if lag not in (1,2): raise ValueError('Invalid hidden block')
    expressions = []
    for c in frame.columns:
        if annual_block(c,lag):
            if c == f'missing_lag{lag}': value = 1
            elif c == f'mlb_value_history_available_lag{lag}': continue  # global label availability
            elif c.startswith(('log_pa_', 'log_mlb_pa_', 'share_', 'observed_mlb_value_')) or c.endswith('__available'):
                value = 0
            else: value = None
            expressions.append(pl.when(pl.col('prospect')).then(pl.lit(value,dtype=frame.schema[c]))
                               .otherwise(pl.col(c)).alias(c))
        elif lag == 1 and c.startswith('change__'):
            expressions.append(pl.when(pl.col('prospect')).then(None).otherwise(pl.col(c)).alias(c))
    return frame.with_columns(expressions)


def matrix(frame, columns):
    x = frame.select(columns).cast(pl.Float64).to_numpy().copy()
    x[~np.isfinite(x)] = np.nan
    return x


def fit_model(train, columns, target):
    if any(c.startswith(('pa_h','war_h','target_')) or c in ('player_id','origin_year') for c in columns):
        raise ValueError('Outcome or identity feature')
    x = matrix(train,columns)
    keep = np.array([len(np.unique(x[np.isfinite(x[:,j]),j])) > 1 for j in range(x.shape[1])])
    used = [c for c,k in zip(columns,keep) if k]
    y = target_values(train,target)
    if len(np.unique(y)) != 2 or not used: raise ValueError('Insufficient training support')
    w = train['identity_weight'].to_numpy(); w = w/w.mean()
    model = make_engine_models('lightgbm',417,'balanced').classifier.set_params(n_jobs=4)
    model.fit(x[:,keep],y,sample_weight=w)
    return model, used, {'used_features':used,'dropped_constant_or_unobserved':[c for c,k in zip(columns,keep) if not k],
                         'training_rows':train.height,'training_players':train['player_id'].n_unique(),
                         'positive_rows':int(y.sum()),'training_origins':sorted(train['origin_year'].unique().to_list())}


def predict(model, columns, query):
    return np.clip(model.predict_proba(matrix(query,columns))[:,1],1e-6,1-1e-6)
