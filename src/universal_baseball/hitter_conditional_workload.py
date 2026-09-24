"""Fixed conditional PA heads; role labels never select forecast players."""
import numpy as np
import polars as pl
from universal_baseball.hitter_arrival_value_transfer import training
from universal_baseball.hitter_canceled_season import matrix
from universal_baseball.hitter_model_tournament import make_engine_models


def roles(pa):
    y=np.asarray(pa,float)
    if not np.isfinite(y).all() or (y<=0).any():raise ValueError('Roles require observed positive PA')
    return np.where(y<100,0,np.where(y<450,1,2))


def active_training(panel,year,h):
    f=training(panel,year,h).filter(pl.col(f'pa_h{h}')>0)
    return f.with_columns((1/pl.len().over('player_id')).alias('identity_weight'))


def role_means(y,w):
    r=roles(y);w=np.asarray(w,float)
    if w.shape!=r.shape or not np.isfinite(w).all() or (w<=0).any():raise ValueError('Invalid role weights')
    if set(r)!={0,1,2}:raise ValueError('Missing training role')
    return np.array([np.average(np.asarray(y)[r==k],weights=w[r==k]) for k in range(3)])


def mixture_mean(p,means):
    p=np.asarray(p,float);m=np.asarray(means,float)
    if p.ndim!=2 or p.shape[1]!=3 or m.shape!=(3,) or not np.isfinite(p).all() or not np.isfinite(m).all():
        raise ValueError('Invalid mixture shape or values')
    if ((p<0)|(p>1)).any() or not np.allclose(p.sum(axis=1),1.,rtol=1e-10,atol=1e-10):raise ValueError('Invalid probabilities')
    return np.clip(p@m,1,750)


def fit_head(panel,columns,year,h,head):
    if head not in ('A','D','M'):raise ValueError(head)
    if any(c in ('origin_year','player_id') or c.startswith(('pa_h','war_h','target_')) for c in columns):
        raise ValueError('Outcome/identity input')
    train=active_training(panel,year,h);query=panel.filter(pl.col('origin_year')==year)
    x=matrix(train,columns);keep=np.array([len(np.unique(x[np.isfinite(x[:,j]),j]))>1 for j in range(x.shape[1])])
    used=[c for c,k in zip(columns,keep) if k];assert used
    y=train[f'pa_h{h}'].to_numpy();w=train['identity_weight'].to_numpy();w=w/w.mean()
    tx=matrix(query,used);pair=make_engine_models('lightgbm',417,'balanced')
    if head=='M':
        means=role_means(y,w)
        model=pair.classifier.set_params(objective='multiclass',num_class=3,n_jobs=4)
        model.fit(x[:,keep],roles(y),sample_weight=w)
        np.testing.assert_array_equal(model.classes_,[0,1,2])
        p=model.predict_proba(tx);prediction=mixture_mean(p,means)
        extra={'role_means':means.tolist(),'role_training_counts':np.bincount(roles(y),minlength=3).tolist(),
            'role_training_weight':[float(w[roles(y)==k].sum()) for k in range(3)]}
    else:
        model=pair.regressor.set_params(n_jobs=4);model.fit(x[:,keep],y,sample_weight=w)
        prediction=np.clip(model.predict(tx),1,750);p=None;extra={}
    note={'year':year,'horizon':h,'head':head,'training_rows':train.height,'training_players':train['player_id'].n_unique(),
        'training_origins':sorted(train['origin_year'].unique().to_list()),'latest_label':int(train['origin_year'].max())+h,
        'used_features':used,'dropped_features':[c for c in columns if c not in used],
        'clipped_predictions':int(((prediction==1)|(prediction==750)).sum()),**extra}
    return prediction,p,note


def paired_interval(frame,candidate,reference,draws=2000):
    """Equal-origin MSE difference, 97.5% whole-player bootstrap interval."""
    ids,inv=np.unique(frame['player_id'].to_numpy(),return_inverse=True)
    years=sorted(frame['origin_year'].unique());d=np.zeros((len(ids),len(years)));n=np.zeros_like(d);folds=[]
    a=(frame[candidate].to_numpy()-frame['actual_pa'].to_numpy())**2
    b=(frame[reference].to_numpy()-frame['actual_pa'].to_numpy())**2
    for j,year in enumerate(years):
        use=frame['origin_year'].to_numpy()==year
        np.add.at(d[:,j],inv[use],a[use]-b[use]);np.add.at(n[:,j],inv[use],1)
        folds.append({'origin':int(year),'candidate_mse':float(a[use].mean()),'reference_mse':float(b[use].mean()),'delta':float((a[use]-b[use]).mean())})
    rng=np.random.default_rng(417);boot=[]
    for _ in range(draws):
        ix=rng.integers(0,len(ids),len(ids));counts=n[ix].sum(axis=0)
        if (counts>0).all():boot.append(float(np.mean(d[ix].sum(axis=0)/counts)))
    return {'delta':float(np.mean([f['delta'] for f in folds])),'interval975':np.quantile(boot,[.0125,.9875]).tolist(),
        'draws':len(boot),'improving_origins':sum(f['delta']<0 for f in folds),'folds':folds}
