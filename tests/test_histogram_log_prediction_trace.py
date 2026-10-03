import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from universal_baseball.histogram_log_prediction_trace import log_trace
from threadpoolctl import threadpool_limits


def test_log_path_reconstructs_mean_instead_of_confusing_raw_log_with_pa():
    x=np.arange(80,dtype=float).reshape(-1,1);y=np.where(x[:,0]<40,0,400)
    with threadpool_limits(limits=2):
        model=HistGradientBoostingRegressor(loss='poisson',max_iter=15,max_depth=2,min_samples_leaf=10,early_stopping=False).fit(x,y)
        for row in [x[0],x[-1]]:
            t=log_trace(model,row,['work']);assert np.isclose(t['unbounded_mean_pa'],model.predict(row[None,:])[0])
            assert np.isclose(t['reference']+sum(p['path_effect'] for p in t['feature_effects']),t['raw_log_prediction'])
