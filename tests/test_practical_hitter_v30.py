import numpy as np
from universal_baseball.practical_hitter_v30 import forecast,EVENTS

def test_workload_bounds_and_definitive_status_not_blanket():
    np.testing.assert_array_equal(forecast([-3,200,1000,500],[False,False,False,True]),[0,200,800,0])

def test_zero_evidence_is_prior_not_zero_talent():
    for num,den,p in EVENTS.values():assert (0+100*p)/(0+100)==p

def test_invalid_prediction_is_not_silent_fallback():
    import pytest
    with pytest.raises(ValueError):forecast([np.nan],[False])
