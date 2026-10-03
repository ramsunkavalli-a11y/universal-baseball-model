import numpy as np


def test_pa_weighted_rate_can_recover_expected_value_without_independence():
    pa=np.array([100.,600.]);rate=np.array([4.,1.])
    actual=np.mean(pa*rate/600)
    assert np.isclose(pa.mean()*np.average(rate,weights=pa)/600,actual)
    assert not np.isclose(pa.mean()*rate.mean()/600,actual)
