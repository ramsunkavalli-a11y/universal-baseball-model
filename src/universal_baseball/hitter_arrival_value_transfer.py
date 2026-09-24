"""Annual activity and explicit probability-only opportunity/value intervention."""
import numpy as np
import polars as pl
from universal_baseball.hitter_canceled_season import matrix
from universal_baseball.hitter_model_tournament import make_engine_models

FOLDS=[(y,1) for y in (2016,2017,2018,2021,2022)]+[(y,2) for y in (2016,2017,2021,2022)]+[(y,3) for y in (2016,2021,2022)]


def training(panel, cutoff, horizon):
    if horizon not in (1,2,3) or cutoff+horizon>2025:raise ValueError('Protected or unsupported fold')
    f=panel.filter((pl.col('origin_year')+horizon<=cutoff)&
        ~((pl.col('origin_year')<2020)&(pl.col('origin_year')+horizon>=2020))&
        pl.col(f'pa_h{horizon}').is_finite().fill_null(False)).sort('origin_year','player_id')
    return f.with_columns((1/pl.len().over('player_id')).alias('identity_weight'))


def annual_labels(frame,horizon):
    pa=frame[f'pa_h{horizon}'].to_numpy()
    if not np.isfinite(pa).all() or (pa<0).any():raise ValueError('Invalid annual targets')
    return (pa>0).astype(int)


def fit_activity(panel,columns,year,horizon):
    if any(c in ('player_id','origin_year') or c.startswith(('pa_h','war_h','target_')) for c in columns):
        raise ValueError('Outcome or identity feature')
    train=training(panel,year,horizon);query=panel.filter(pl.col('origin_year')==year)
    x=matrix(train,columns)
    keep=np.array([len(np.unique(x[np.isfinite(x[:,j]),j]))>1 for j in range(x.shape[1])])
    used=[c for c,k in zip(columns,keep) if k]
    y=annual_labels(train,horizon);assert len(np.unique(y))==2 and used
    w=train['identity_weight'].to_numpy();w=w/w.mean()
    model=make_engine_models('lightgbm',417,'balanced').classifier.set_params(n_jobs=4)
    model.fit(x[:,keep],y,sample_weight=w)
    p=np.clip(model.predict_proba(matrix(query,used))[:,1],1e-6,1-1e-6)
    return p,{'training_rows':train.height,'training_players':train['player_id'].n_unique(),
        'training_origins':sorted(train['origin_year'].unique().to_list()),'latest_label':int(train['origin_year'].max())+horizon,
        'used_features':used,'dropped_features':[c for c in columns if c not in used]}


def propagate(frame, probability, scope):
    """Leave baseline direct value intact except an explicit marginal PA change."""
    p=np.asarray(probability,float);mask=np.asarray(scope,bool)
    if len(p)!=frame.height or len(mask)!=frame.height or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError('Invalid probability or scope')
    base_p,base_pa,base_v,rate=[frame[c].to_numpy() for c in ('B_p','B_pa','B_value','rate')]
    if any(not np.isfinite(a).all() for a in (base_p,base_pa,base_v,rate)) or (base_p<=0).any() or (base_pa<=0).any():
        raise ValueError('Nonpositive or invalid baseline hurdle denominator')
    cp=base_pa/base_p
    if (cp<1-1e-8).any() or (cp>750+1e-8).any():raise ValueError('Invalid conditional PA')
    new_p=np.where(mask,p,base_p);pa=np.where(mask,new_p*cp,base_pa)
    value=np.where(mask,base_v+(pa-base_pa)*rate/600,base_v)
    return new_p,pa,value
