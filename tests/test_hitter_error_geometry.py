import numpy as np
import pytest
from universal_baseball.hitter_error_geometry import decompose,change


def test_active_and_nonarrival_are_distinct():
    pa=np.array([100,400,50]);n=np.array([300,400,0]);a=np.array([2.,-1.,np.nan]);rep=np.full(3,.003)
    d=decompose(pa,n,np.array([1.,1.,2.]),a,rep)
    assert np.isnan(d['hitting'][2]) and np.isnan(d['opportunity'][2])
    assert np.isclose(d['error'][2],50*(2/600+.003))
    z=change(pa,n,np.array([1.,1.,2.]),np.array([2.,-1.,3.]),a,rep)
    assert np.allclose(z['delta'],z['active_hitting_squared']+z['active_interaction']+z['nonarrival'])
    assert z['nonarrival'][2]!=0 and z['active_interaction'][1]==0


def test_perfect_rate_can_reveal_workload_error():
    d=decompose([100],[400],[3],[3],[.003])
    assert d['hitting'][0]==0 and np.isclose(d['error'][0],-300*(3/600+.003))
    with pytest.raises(ValueError):decompose([1],[2],[1],[np.nan],[.003])
