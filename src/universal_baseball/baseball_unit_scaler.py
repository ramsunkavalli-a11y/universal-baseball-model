"""Affine feature scaling that cannot amplify scarce rate histories."""
import numpy as np
from sklearn.base import BaseEstimator,TransformerMixin
from universal_baseball.practical_hitter_v30 import EVENTS


class BaseballUnitScaler(TransformerMixin,BaseEstimator):
    def __init__(self,features):
        self.features=features

    def fit(self,x,y=None):
        if x.shape[1]!=len(self.features):
            raise ValueError('Feature dimension mismatch')
        self.mean_=np.zeros(len(self.features));self.scale_=np.ones(len(self.features))
        for i,n in enumerate(self.features):
            ev=n.rsplit('_',1)[-1]
            if n.startswith('pooled_') and ev in EVENTS:
                self.mean_[i]=EVENTS[ev][2];self.scale_[i]=.1
            elif n=='last_stat_gap':
                self.scale_[i]=5
            elif n.startswith('role_minor_'):
                self.mean_[i]=4
        self.n_features_in_=len(self.features)
        return self

    def transform(self,x):
        x=np.asarray(x,dtype=float)
        if x.ndim!=2 or x.shape[1]!=self.n_features_in_ or not np.isfinite(x).all():
            raise ValueError('Invalid feature matrix')
        return (x-self.mean_)/self.scale_
