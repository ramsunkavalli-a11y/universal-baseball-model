import pytest
from universal_baseball.minor_fielding_counts import extract, count, pool_quality


def test_missing_not_zero():
    r = extract({'putOuts':0,'errors':'','chances':None})
    assert r['putOuts'] == 0 and r['putOuts_status'] == 'recorded'
    assert r['errors'] is None and r['errors_status'] == 'missing'
    assert r['chances_identity'] is None


@pytest.mark.parametrize('bad',[-1,1.5,'oops','NaN',float('inf')])
def test_invalid_counts_unknown(bad):
    assert count(bad) == (None,'invalid')


def test_source_inconsistency_is_retained():
    r = extract(dict(putOuts=5,assists=2,errors=1,chances=9,throwingErrors=2))
    assert r['chances'] == 9 and r['chances_identity'] is False
    assert r['throwing_subset_identity'] is False


def measured(opportunities,runs):
    return dict(valid=True,opportunities=opportunities,runs=runs)


def test_nonarrival_unknown_not_average_skill():
    r = pool_quality(2018,5,'range',6,{}, {})
    assert r['quality_rate'] is None and r['quality_status'] == 'no_same_position_exposure'


def test_later_arrival_before_tracking_absence_not_fabricated_zero():
    r = pool_quality(2013,5,'range',6,{2017:1000,2018:1000},
        {2017:measured(1000,2),2018:measured(1000,4)})
    assert r['quality_rate'] == 4.5 and r['future_measured_seasons'] == 2
    assert r['unmeasured_official_outs'] == 0


def test_actual_pretracking_exposure_blocks_label():
    r = pool_quality(2013,5,'range',6,{2015:100,2017:1000,2018:1000},
        {2017:measured(1000,2),2018:measured(1000,4)})
    assert r['quality_rate'] is None and r['unmeasured_official_outs'] == 100


def test_cameo_and_incomplete_window_remain_unknown():
    r = pool_quality(2022,3,'range',6,{2023:150}, {2023:measured(150,4)})
    assert r['quality_rate'] is None and r['quality_status'] == 'insufficient_measurement'
    r = pool_quality(2023,3,'range',6,{2024:1000,2025:1000},
        {2024:measured(1000,2),2025:measured(1000,4)})
    assert r['quality_status'] == 'window_incomplete' and r['quality_rate'] is None


def test_catcher_opportunities_are_not_innings():
    r = pool_quality(2022,3,'throwing',2,{2023:1500,2024:1500},
        {2023:measured(40,1),2024:measured(60,2)})
    assert r['quality_rate'] == 3 and r['unit'] == 100
    r = pool_quality(2022,3,'blocking',2,{2023:1500,2024:1500},
        {2023:measured(1400,1),2024:measured(1500,2)})
    assert r['quality_rate'] is None  # 2,900 chances, not 3,000 innings.


def test_invalid_catcher_measurement_not_ignored():
    r = pool_quality(2022,3,'throwing',2,{2023:1000,2024:1000,2025:100},
        {2023:measured(60,2),2024:measured(60,3),2025:dict(valid=False,opportunities=20,runs=0)})
    assert r['quality_rate'] is None and r['unmeasured_official_outs'] == 100


def test_real_short_mlb_season_kept():
    r = pool_quality(2019,3,'range',8,{2020:600,2021:1800},
        {2020:measured(600,2),2021:measured(1800,4)})
    assert r['quality_rate'] == 3.75 and r['window_has_2020']


def test_no_cross_position_confirmation():
    with pytest.raises(ValueError):
        pool_quality(2022,3,'range',2,{}, {})
    with pytest.raises(ValueError):
        pool_quality(2022,3,'throwing',6,{}, {})
