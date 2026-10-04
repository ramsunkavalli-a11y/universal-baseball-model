"""Locked mean-workload capacity comparison; no changed arrival or batting."""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from lightgbm import LGBMRegressor

SETTINGS={
    'deep_hist':dict(max_iter=250,max_depth=6,max_leaf_nodes=31,min_samples_leaf=30,
        learning_rate=.05,l2_regularization=10,early_stopping=False,random_state=31),
    'lightgbm':dict(objective='regression',n_estimators=250,max_depth=6,num_leaves=31,
        min_child_samples=30,min_child_weight=.001,learning_rate=.05,reg_lambda=10,reg_alpha=0,
        colsample_bytree=1.,subsample=1.,subsample_freq=0,random_state=31,n_jobs=2,
        deterministic=True,force_col_wise=True,verbosity=-1)}


def learner(arm):
    return (HistGradientBoostingRegressor if arm=='deep_hist' else LGBMRegressor)(**SETTINGS[arm])


def forecast(raw,p,rate,replacement):
    raw,p,rate,replacement=[np.asarray(x,dtype=float) for x in [raw,p,rate,replacement]]
    assert raw.shape==p.shape==rate.shape==replacement.shape
    assert np.isfinite(raw).all() and np.isfinite(rate).all() and np.isfinite(replacement).all()
    assert ((p>=0)&(p<=1)).all()
    conditional=np.clip(raw,1,800);pa=p*conditional
    return dict(raw_conditional_pa=raw,conditional_pa=conditional,pa=pa,
        value=pa*(rate/600+replacement))
