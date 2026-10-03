import numpy as np
import pytest
from universal_baseball.hitter_workload_anchor import reference,forecast


def test_reference_preserves_prior_regular_and_short_schedule():
    r,a=reference([[0,471,381],[200,180,100],[0,0,0]],[[162,162,162],[60,162,162],[162,162,162]])
    np.testing.assert_allclose(r,[471,540,100])
    assert a[1,0]==540


def test_reference_does_not_guarantee_playing_time():
    r,_=reference([[0,600,500]],[[162,162,162]])
    assert forecast(r+np.array([-700]),[False])[0]==0
    assert forecast(r,[True])[0]==0


def test_unknown_history_is_not_zero():
    with pytest.raises(ValueError):reference([[np.nan,0,0]],[[162,162,162]])
    with pytest.raises(ValueError):reference([[0,0,0]],[[0,162,162]])
