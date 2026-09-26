import numpy as np
import polars as pl
from universal_baseball.hitter_common_weight import active_common_measure, paired_mse
from universal_baseball.hitter_conditional_workload import active_training


def test_common_weights_preserve_inactive_history_and_mature_cutoff():
    p=pl.DataFrame({'origin_year':[2014,2015,2014,2015,2017],
        'player_id':[1,1,2,2,1],'pa_h1':[0.,100.,500.,500.,999.]})
    c=active_common_measure(p,2016,1);d=active_training(p,2016,1)
    assert c['identity_weight'].to_list()==[.5,.5,.5]
    assert d.filter(pl.col('player_id')==1)['identity_weight'].item()==1
    assert c['origin_year'].max()==2015


def test_paired_identical_is_zero_and_row_order_invariant():
    p=pl.DataFrame({'player_id':[1,2,1,2],'origin_year':[2016,2016,2021,2021],
        'a':[1.,2.,3.,4.],'b':[1.,2.,3.,4.],'y':[0.,2.,3.,9.]})
    assert paired_mse(p,'a','b','y',20)['interval95']==[0.,0.]
    assert paired_mse(p,'a','b','y',20)==paired_mse(p.reverse(),'a','b','y',20)
