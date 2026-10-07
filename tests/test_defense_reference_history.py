import pytest
from universal_baseball.defense_reference_history import annual_references,history,origin_reference,measured_quality


def row(pid,year,outs,runs,p=8,valid=True):
    return dict(player_id=pid,season=year,native_outs=outs,range_runs=runs,position=p,range_valid=valid)


def test_average_center_fielder_shrinks_to_position_average():
    records=[row(1,2022,1500,3),row(2,2022,1500,3)]
    refs=annual_references(records)
    h=history([records[0]],2022,8,1,refs)
    assert h['legacy_raw']==1 and h['centered']==0
    assert h['reliability']==pytest.approx(1/3)


def test_tiny_corner_sample_does_not_get_full_baseline_credit():
    records=[row(1,2022,24,0,7),row(2,2022,1500,-1.5,7)]
    refs=annual_references(records)
    h=history([records[0]],2022,7,1,refs)
    assert h['centered']==pytest.approx(1.5*24/3024)
    assert h['centered']<.012


def test_unknown_talent_has_prior_mean_not_measured_grade():
    h=history([],2022,8,1,{})
    assert h['centered']==0 and not h['talent_known'] and h['reliability']==0


def test_held_people_cannot_change_reference():
    rows=[row(1,2022,1500,3),row(6,2022,1500,99),row(2,2022,3000,6)]
    ref=annual_references(rows)[2022,8,1]
    assert ref['people']==1 and ref['rate']==3


def test_future_cannot_change_forecast_history_or_origin_reference():
    rows=[row(1,2022,1500,4),row(2,2022,1500,3),row(2,2023,1500,99)]
    refs=annual_references(rows)
    h=history(rows[:1],2022,8,1,refs);r=origin_reference(2022,8,1,refs)
    rows[2]['range_runs']=-999
    ref2=annual_references(rows)
    assert history(rows[:1],2022,8,1,ref2)==h
    assert origin_reference(2022,8,1,ref2)==r


def test_all_rows_weighted_by_exposure_and_recency():
    rows=[row(1,2021,1500,6),row(1,2022,3000,3),row(2,2021,1500,3),row(2,2022,3000,6)]
    h=history(rows[:2],2022,8,1,annual_references(rows))
    assert h['history_outs']==3750 and h['weighted_relative_runs']==-1.5
    assert h['centered']==pytest.approx(-1/3)


def test_infield_history_unchanged():
    h=history([row(1,2022,1500,6,6)],2022,6,1,{})
    assert h['centered']==h['legacy_raw']==2


def test_future_measured_reference_only_enters_target():
    r=[row(1,2023,1500,6),row(1,2024,1500,3)]
    assert measured_quality(r,2022,8,{(2023,8):3,(2024,8):3})==1.5


def test_missing_positive_reference_is_an_error():
    with pytest.raises(KeyError):history([row(1,2022,25,1)],2022,8,1,{})
    with pytest.raises(AssertionError):origin_reference(2022,8,1,{})
