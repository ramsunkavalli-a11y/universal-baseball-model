import pytest
import numpy as np

from universal_baseball.defense_position_transfer import other_history, features, matrix, EXTRA, preflight


def source(pos,year=2022,n=3000,runs=12,valid=True):
    return dict(position=pos,season=year,native_outs=n,range_runs=runs,range_valid=valid)


def row(pid=5,year=2022,pos=7):
    h,_=other_history([source(8,year=year)],year,pos)
    return dict(player_id=pid,origin_year=year,window_end=year+3,window_has_2020=False,
                quality_rate=1.,position=pos,age=27.,history_outs=3000.,history_rate=2.,
                reliability=.5,**h)


def test_same_position_not_counted_twice_and_no_cross_family():
    h,used=other_history([source(7),source(8),source(6)],2022,7)
    assert h['other_outs']==3000 and [s['position'] for s in used]==[8]
    h,_=other_history([source(8)],2022,6)
    assert h['other_outs']==0
    assert other_history([source(6)],2022,3)[0]['other_outs']==0


def test_missing_invalid_and_future_are_not_measured_zero():
    h,used=other_history([source(8,2023),source(9,valid=False),source(8,2018)],2022,7)
    assert used==[] and h['other_outs']==0 and h['other_invalid_outs']==3000
    assert all(features(row(pos=3))[c]==0 for c in EXTRA)


def test_small_samples_shrink_directly_and_target_evidence_attenuates():
    h,_=other_history([source(8,n=3,runs=.012)],2022,7)
    assert h['other_rate']==pytest.approx(1500*.012/3003)
    a=row();b={**a,'reliability':.9}
    assert features(b)['other_range_OF']==pytest.approx(features(a)['other_range_OF']*.2)


def test_recency_pivot_and_family_direction():
    h,_=other_history([source(8,2020,n=900,runs=3),source(9,2022)],2022,7)
    assert h['other_outs']==3225 and h['other_pivot_share']==225/3225
    f=features({**row(),**h})
    assert f['CF_to_corners']>0 and f['corners_to_CF']==0 and f['other_range_IF']==0


def test_distinct_person_feature_guard_and_chronology():
    tr=[row(pid=1,year=2016),row(pid=1,year=2017)]
    check,_=preflight(tr,[row()],2022,0)
    assert check['added_feature_people']['other_range_OF']==1
    assert 'other_range_OF' in check['disabled_features']
    assert np.all(matrix([row()],check['disabled_features'])[:,len(matrix([row()])[0])-len(EXTRA):]==0)
    with pytest.raises(AssertionError):
        preflight([row(pid=1,year=2021)],[row()],2022,0)
