import numpy as np
from universal_baseball.probability_position_diagnostics import (
    pit_bin_mass, quantile_exceedance, paired_position)


def test_zero_atom_is_not_false_calibration_failure():
    pmf=np.array([[.9,.1]])
    p0,*_=pit_bin_mass(pmf,[0])
    p1,*_=pit_bin_mass(pmf,[1])
    np.testing.assert_allclose(.9*p0+.1*p1,.1)
    q,p,o=quantile_exceedance(pmf,[0],[.1,.5,.9])
    np.testing.assert_allclose(p,.1)
    assert (q==0).all() and not o.any()


def test_general_discrete_distribution_expected_pit_is_uniform():
    p=np.array([.35,.1,.2,.35])
    bins,*_=pit_bin_mass(np.tile(p,(4,1)),np.arange(4))
    np.testing.assert_allclose(p@bins,np.repeat(.1,10),atol=1e-14)


def test_impossible_outcome_is_kept():
    bins,lo,hi,impossible=pit_bin_mass(np.array([[1.,0.]]),[1])
    assert impossible[0] and bins[0,-1]==1 and hi[0]==1


def test_tiny_tail_is_kept_despite_floating_point_cdf_collapse():
    bins,lo,hi,impossible=pit_bin_mass(np.array([[1.,1e-100]]),[1])
    assert not impossible[0] and bins[0,-1]==1 and hi[0]==1


def test_reference_transfer_cannot_create_value():
    r=paired_position(4,1500,-1,1500,2,-1)
    assert r['raw_difference']==5 and r['relative_difference']==2
    np.testing.assert_allclose(r['raw_plus_schedule'],r['relative_plus_transferred_schedule'])


def test_equalization_is_not_the_same_as_existing_schedule():
    r=paired_position(0,1500,0,1500,2,-1)
    assert r['equalization_gap_per1458']==8.748
    assert r['relative_plus_schedule']!=0
