"""One fixed alternative to reweighting conditional participation survivors."""
import numpy as np
import polars as pl
from universal_baseball.hitter_arrival_value_transfer import training
from universal_baseball.hitter_canceled_season import matrix
from universal_baseball.hitter_model_tournament import make_engine_models


def active_common_measure(panel,year,h):
    return training(panel,year,h).filter(pl.col(f'pa_h{h}')>0)


def fit_common_weight(panel,columns,year,h):
    if any(c in ('origin_year','player_id') or c.startswith(('pa_h','war_h','target_')) for c in columns):
        raise ValueError('Outcome/identity input')
    train=active_common_measure(panel,year,h)
    query=panel.filter(pl.col('origin_year')==year)
    x=matrix(train,columns)
    keep=np.array([len(np.unique(x[np.isfinite(x[:,j]),j]))>1 for j in range(x.shape[1])])
    used=[c for c,k in zip(columns,keep) if k]
    if not used: raise ValueError('No varying features')
    w=train['identity_weight'].to_numpy();w=w/w.mean()
    model=make_engine_models('lightgbm',417,'balanced').regressor.set_params(n_jobs=4)
    model.fit(x[:,keep],train[f'pa_h{h}'].to_numpy(),sample_weight=w)
    prediction=np.clip(model.predict(matrix(query,used)),1,750)
    return prediction, {'year':year,'horizon':h,'training_rows':train.height,
        'training_players':train['player_id'].n_unique(),'used_features':used,
        'latest_label':int(train['origin_year'].max())+h,
        'weight_mean':float(w.mean()),'weight_min':float(w.min()),'weight_max':float(w.max()),
        'clipped_predictions':int(((prediction==1)|(prediction==750)).sum())}


def paired_mse(frame,candidate,reference,target,draws=4000,seed=1729):
    """Equal-origin paired player-history bootstrap; not season-shock uncertainty."""
    ids,inv=np.unique(frame['player_id'].to_numpy(),return_inverse=True)
    years=sorted(frame['origin_year'].unique())
    a=(frame[candidate].to_numpy()-frame[target].to_numpy())**2
    b=(frame[reference].to_numpy()-frame[target].to_numpy())**2
    d=np.zeros((len(ids),len(years)));n=np.zeros_like(d);folds=[]
    for j,year in enumerate(years):
        mask=frame['origin_year'].to_numpy()==year
        np.add.at(d[:,j],inv[mask],a[mask]-b[mask]);np.add.at(n[:,j],inv[mask],1)
        folds.append({'origin':int(year),'rows':int(mask.sum()),'candidate_mse':float(a[mask].mean()),
            'reference_mse':float(b[mask].mean()),'delta':float((a[mask]-b[mask]).mean())})
    rng=np.random.default_rng(seed);values=[]
    for _ in range(draws):
        ix=rng.integers(0,len(ids),len(ids));counts=n[ix].sum(axis=0)
        if (counts>0).all():values.append(float(np.mean(d[ix].sum(axis=0)/counts)))
    return {'delta':float(np.mean([f['delta'] for f in folds])),
        'interval95':np.quantile(values,[.025,.975]).tolist(),'draws':len(values),'seed':seed,'folds':folds}
