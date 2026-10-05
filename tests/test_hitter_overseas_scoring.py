import sys
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from fit_hitter_overseas_integration import rate_weights
from review_hitter_overseas_integration import origin_weights, errors, interval


def test_rate_precision_weights_preserve_equal_origin_totals():
    f=pl.DataFrame({'origin_year':[2011,2011,2012],'next_pa':[1,600,30]})
    w=rate_weights(f)
    assert np.isclose(w[:2].sum(),w[2])
    assert np.isclose(w[1]/w[0],300)
    assert np.isclose(w.sum(),3)


def cohort():
    f=pl.DataFrame({'origin_year':[2016,2016,2017], 'player_id':[1,2,1],
        'next_pa':[0,100,200], 'actual_relative_value':[0.,1.,2.],
        'a_pa':[0.,110.,190.], 'a_p':[.01,.9,.8], 'a_value':[0.,1.1,1.9],
        'b_pa':[0.,120.,180.], 'b_p':[.01,.8,.8], 'b_value':[0.,1.2,1.8]})
    return f


def test_no_arrival_is_retained_in_proper_probability_scores():
    f=cohort();e=errors(f,'a')
    assert e.shape==(3,8) and np.isclose(e[0,6],.01**2)
    assert np.isclose(e[0,7],-np.log(.99))
    assert np.isclose(origin_weights(f)[:2].sum(),origin_weights(f)[2])


def test_cluster_interval_keeps_original_row_weights():
    f=cohort();point=origin_weights(f)@(errors(f,'a')-errors(f,'b'))
    result=interval(f,'a','b')
    assert all(r['fixed_original_origin_weights'] for r in result)
    assert np.allclose([r['change'] for r in result],point)
