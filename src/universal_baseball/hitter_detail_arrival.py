"""Fixed richer-input arrival experiment; no production forecast changes."""
import numpy as np
import polars as pl
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from universal_baseball.hitter_model_tournament import make_engine_models

TARGETS={'next_year':1,'arrival_three':3,'regular_three':3}


def join_lags(panel,annual,columns,prefix,lags=(0,1,2)):
    if annual.select('season','player_id').is_duplicated().any():raise ValueError('Duplicate annual feature key')
    out=panel
    added=[]
    for lag in lags:
        names={c:f'{prefix}{lag}__{c}' for c in columns}
        flag=f'{prefix}{lag}__available'
        source=annual.select('season','player_id',*columns).rename(names).with_columns(
            (pl.col('season')+lag).alias('origin_year'),pl.lit(1).alias(flag)).drop('season')
        out=out.join(source,on=['origin_year','player_id'],how='left',validate='m:1',maintain_order='left').with_columns(pl.col(flag).fill_null(0))
        added.extend([*names.values(),flag])
    assert out.height==panel.height
    return out,added


def eligible(panel,cutoff,target,excluded=()):
    h=TARGETS[target]
    if cutoff+h>2025:raise ValueError('Protected development target')
    mask=(pl.col('origin_year')+h<=cutoff)&~((pl.col('origin_year')<2020)&(pl.col('origin_year')+h>=2020))
    for k in range(1,h+1):mask &= pl.col(f'pa_h{k}').is_finite().fill_null(False)
    f=panel.filter(mask&~pl.col('player_id').is_in(list(excluded))).sort('origin_year','player_id')
    return f.with_columns((1/pl.len().over('player_id')).alias('identity_weight'))


def target_values(f,target):
    a=f.select([f'pa_h{h}' for h in range(1,TARGETS[target]+1)]).to_numpy()
    if not np.isfinite(a).all() or (a<0).any():raise ValueError('Incomplete or invalid outcomes')
    return ((a>=450).sum(axis=1)>=2 if target=='regular_three' else (a>0).any(axis=1)).astype(int)


def fit_probability(train,test,columns,target,engine='lightgbm'):
    if any(c.startswith(('pa_h','war_h','target_')) or c in ('player_id','origin_year') for c in columns):
        raise ValueError('Outcome or identity selected')
    x=train.select(columns).cast(pl.Float64).to_numpy().copy();tx=test.select(columns).cast(pl.Float64).to_numpy().copy()
    x[~np.isfinite(x)]=np.nan;tx[~np.isfinite(tx)]=np.nan
    keep=np.array([len(np.unique(x[np.isfinite(x[:,j]),j]))>1 for j in range(x.shape[1])])
    if not keep.any():raise ValueError('No variable training features')
    y=target_values(train,target)
    if len(np.unique(y))!=2:raise ValueError('Insufficient class support')
    w=train['identity_weight'].to_numpy();w=w/w.mean()
    if engine=='lightgbm':
        model=make_engine_models('lightgbm',417,'balanced').classifier.set_params(n_jobs=4)
        model.fit(x[:,keep],y,sample_weight=w)
    else:
        model=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
            LogisticRegression(C=.1,max_iter=4000,random_state=417))
        model.fit(x[:,keep],y,logisticregression__sample_weight=w)
    return np.clip(model.predict_proba(tx[:,keep])[:,1],1e-6,1-1e-6),{
        'used_features':[c for c,k in zip(columns,keep) if k],
        'dropped_constant_or_unobserved':[c for c,k in zip(columns,keep) if not k],
        'training_rows':train.height,'training_players':train['player_id'].n_unique(),
        'positive_rows':int(y.sum()),'training_origins':sorted(train['origin_year'].unique().to_list()),
        'latest_label':int(train['origin_year'].max())+TARGETS[target]}


def losses(y,p):
    y,p=np.asarray(y),np.clip(np.asarray(p),1e-6,1-1e-6)
    return (p-y)**2,-y*np.log(p)-(1-y)*np.log1p(-p)
