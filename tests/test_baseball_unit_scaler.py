import numpy as np
from universal_baseball.baseball_unit_scaler import BaseballUnitScaler


def test_rare_rate_variance_and_future_labels_cannot_change_scaling():
    names=['pooled_RK124_K','pooled_AAA_HR','last_stat_gap','role_minor_0']
    nearly_constant=np.array([[.23,.03,0,4],[.230001,.030001,1,4.1]])
    diverse=np.array([[.10,.01,0,3],[.50,.10,5,5]])
    a=BaseballUnitScaler(names).fit(nearly_constant,np.array([0,0]))
    b=BaseballUnitScaler(names).fit(diverse,np.array([100,800]))
    probe=np.array([[.19,.06,2,4.5]])
    assert np.allclose(a.transform(probe),[[-.4,.3,.4,.5]])
    assert np.array_equal(a.transform(probe),b.transform(probe))
