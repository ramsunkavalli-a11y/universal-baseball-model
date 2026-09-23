import numpy as np
import polars as pl
from universal_baseball.player_path_population import identity_split, identity_ess, sample_weights, exact_summary, iid_summary


def test_identity_split_keeps_all_snapshots_together():
    ids = np.repeat(np.arange(100),3)
    half = identity_split(ids)
    assert all(len(np.unique(half[ids==i]))==1 for i in range(100))
    assert half.sum()==150
    assert np.array_equal(half[::3],identity_split(np.arange(100)))


def test_ess_is_identity_not_rows():
    assert identity_ess([1,1,2],[.5,.5,1]) == 2
    assert identity_ess([1,1,2],[.25,.25,1]) < 2


def test_sampling_reproducible_and_no_zero_mass_donors():
    w = np.array([[0,.2,.8],[1,0,0]])
    a = sample_weights(w,1600,417)
    assert np.array_equal(a,sample_weights(w,1600,417))
    assert (a[0]>0).all() and (a[1]==0).all()
    assert abs((a[0]==1).mean()-.2)<.04


def test_exact_crps_and_mean_from_two_point_distribution():
    w = np.array([[.5,.5]])
    war = np.array([[0.,0.,0.],[4.,4.,4.]])
    pa = np.array([[0.,0.,0.],[500.,500.,500.]])
    out = exact_summary(w,war,pa,np.array([[2.,2.,2.]]),np.array([[500.,500.,500.]]))
    assert out['mean_batting'][0] == 6
    assert out['crps'][0] == 3
    assert out['p_regular_workload'][0] == .5
    assert out['brier_regular_workload'][0] == .25


def test_finite_draw_crps_and_brier_correction():
    war = np.array([[[0.],[2.]]]); pa = np.array([[[0.],[500.]]])
    out = iid_summary(war,pa,np.array([[1.]]),np.array([[0.]]))
    assert out['crps'][0] == 0
    assert out['brier_no_mlb'][0] == 0


def test_eligible_weights_maturity_and_pandemic():
    import sys
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    from audit_player_path_population_v1 import eligible
    p = pl.DataFrame({'player_id':[1,1,1,2], 'origin_year':[2015,2016,2019,2015],
        'war_h1':[0.,1.,2.,None],'pa_h1':[0.,20.,30.,None]})
    f = eligible(p,2021,1)
    assert f.height==2
    assert f['identity_weight'].to_list()==[.5,.5]
    assert f['origin_year'].max()==2016


def test_forest_identity_balance_and_self_exclusion():
    from universal_baseball.player_path_population import fitted_weights
    ids=np.repeat(np.arange(100),2)
    train=pl.DataFrame({'player_id':ids,'identity_weight':np.full(200,.5),
        'feature':np.tile([0.,1.],100),'war_h1':np.tile([0.,1.],100),
        'stage':['Lower minors']*200})
    test=pl.DataFrame({'player_id':[0,101],'feature':[0.,1.],'stage':['Lower minors']*2})
    weights,notes=fitted_weights(train,test,['feature'],1,'A1')
    np.testing.assert_allclose(weights.sum(axis=1),1,atol=1e-6)
    assert not weights[0,ids==0].any()
    assert all(n['overlap']==0 for n in notes['splits'])
    assert notes['node_identity_count']['0']>=21
