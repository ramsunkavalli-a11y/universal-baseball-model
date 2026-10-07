import pytest
from universal_baseball.older_fielding_coverage import coverage, exposure_valid, older_valid


def old(outs, valid=True):
    return dict(fielding_outs=outs, older_conversion_valid=valid)


def native(outs, valid=True):
    return dict(native_outs=outs, range_valid=valid)


def test_no_arrival_is_unknown_not_average():
    r = coverage(2009, 5, {}, {}, {})
    assert not r['potential_coverage_available'] and r['potential_observed_outs'] == 0
    assert not any('runs' in k or 'rate' in k for k in r)


def test_old_two_seasons_supply_only_possible_coverage():
    r = coverage(2009, 3, {2011: 300, 2012: 1500}, {2011: old(300), 2012: old(1500)}, {})
    assert r['potential_new_coverage'] and not r['native_quality_available']
    assert r['native_missing_official_outs'] == 1800


def test_single_late_arrival_season_is_not_qualified():
    r = coverage(2009, 5, {2014: 3000}, {2014: old(3000)}, {})
    assert not r['potential_coverage_available']


def test_post2016_older_credit_cannot_fill_native_gap():
    r = coverage(2015, 3, {2016: 3000, 2017: 3000}, {2016: old(3000), 2017: old(3000)}, {})
    assert not r['potential_coverage_available'] and r['older_pre2016_observed_outs'] == 0


def test_a_missing_cameo_stays_missing():
    r = coverage(2013, 3, {2014: 1500, 2015: 1500, 2016: 1},
                 {2014: old(1500), 2015: old(1500)}, {})
    assert r['remaining_unmeasured_official_outs'] == 1 and not r['potential_coverage_available']


def test_cancelled_minor_season_does_not_cancel_real_mlb_2020():
    r = coverage(2019, 3, {2020: 500, 2021: 1500}, {}, {2020: native(500), 2021: native(1500)})
    assert r['native_quality_available'] and r['native_observed_outs'] == 2000


def test_incomplete_window_not_training_quality():
    r = coverage(2024, 3, {2025: 2000}, {}, {2025: native(2000)})
    assert not r['window_mature'] and not r['potential_coverage_available']


@pytest.mark.parametrize('measured,official,valid', [(3000,3003,True), (20,23,False),
    (3000,3006,False), (0,None,False), (3000,None,False), (100,101,True)])
def test_independent_exposure_limits(measured, official, valid):
    assert exposure_valid(measured, official) == valid


def test_null_run_is_not_measured_zero():
    assert not older_valid(dict(fielding_outs=3000, older_conversion_runs=None), 3000)
    assert older_valid(dict(fielding_outs=3000, older_conversion_runs=0.), 3000)
