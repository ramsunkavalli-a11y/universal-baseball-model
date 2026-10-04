import numpy as np
from universal_baseball.hitter_positive_workload import forecast,learner,SETTINGS


def test_fixed_probability_rate_and_clipping_keep_nonarrivals():
    z=forecast([-10,200,900],[.1,0,.8],[-2,2,0],[.003]*3)
    assert np.array_equal(z['conditional_pa'],[1,200,800])
    assert np.allclose(z['pa'],[.1,0,640]) and z['value'][1]==0
    assert z['raw_conditional_pa'][0]==-10


def test_matching_depth_leaf_scale_and_no_early_stopping():
    assert SETTINGS['deep_hist']['max_depth']==SETTINGS['lightgbm']['max_depth']==6
    assert SETTINGS['deep_hist']['max_leaf_nodes']==SETTINGS['lightgbm']['num_leaves']==31
    assert learner('deep_hist').get_params()['early_stopping'] is False
    assert learner('lightgbm').get_params()['objective']=='regression'


def test_setting_probability_to_zero_never_invents_zero_rate():
    z=forecast([500],[0],[4],[.003])
    assert z['conditional_pa'][0]==500 and z['pa'][0]==0 and z['value'][0]==0
