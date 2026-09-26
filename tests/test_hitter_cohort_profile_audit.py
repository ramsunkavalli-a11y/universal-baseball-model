import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_cohort_profile_audit import decompose,cohort,describe


def test_exact_error_decomposition():
    f=pl.DataFrame({'probability':[.1,.9,.5],'conditional':[100.,500.,200.],'actual_pa':[0.,600.,10.]})
    q=decompose(f)
    np.testing.assert_allclose(q['pa_error'],[-10.,150.,-90.])
    np.testing.assert_allclose(q['pa_error'],q['participation_pa_error']+q['workload_pa_error'])
    with pytest.raises(ValueError):decompose(f.with_columns(pl.lit(2.).alias('probability')))


def test_partition():
    f=pl.DataFrame({'prospect':[True,True,False,False,False],'minor_returner':[False,False,True,False,False],
        'stage':['Upper minors','Lower minors','Upper minors','Current MLB','Inactive / unknown']})
    q=cohort(f)
    assert q['audit_cohort'].to_list()==['Prospect upper','Prospect lower','Former MLB in minors','Current MLB','Inactive / unknown']


def test_no_flag_from_one_year_or_tiny_cells():
    f=pl.DataFrame({'origin_year':[2021,2022,2018],'player_id':[1,2,3],'probability':[.1,.1,.1],
        'conditional':[100.,100.,100.],'actual_pa':[500.,400.,300.]})
    q=describe(decompose(f))
    assert q['descriptive_flag'] is None and q['non2021_supported_origins']==0
    assert q['non2021_equal_origin_bias']==340.
