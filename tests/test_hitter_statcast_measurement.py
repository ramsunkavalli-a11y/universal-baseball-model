import polars as pl
import pytest
from universal_baseball.hitter_statcast_measurement import project_measurements,annual_launch_features


def raw(rows=None):
    base=dict(game_date='2015-06-01',game_year='2015',game_type='R',game_pk='1',batter='2',pitcher='3',
        stand='R',p_throws='L',at_bat_number='1',pitch_number='3',type='X',events='home_run',des='A home run.',
        launch_speed='100',launch_angle='25')
    return pl.DataFrame([base|r for r in (rows or [{}])])


def test_interference_award_distinct_from_later_fielding_interference():
    q,ex=project_measurements(raw([dict(events='field_error',des='A reaches on an interference error by pitcher B.'),
        dict(at_bat_number='2',events='field_error',des='A reaches on a fielding error. Interference error by B.')]),2015)
    assert len(q)==1 and q['at_bat_number'].item()==2
    assert ex['measurement_exclusion'].item()=='interference_award'


def test_missing_angle_not_zero_or_missing_ev():
    q,_=project_measurements(raw([dict(launch_angle=None)]),2015)
    f=annual_launch_features(q).row(0,named=True)
    assert f['ev95']==100 and f['measured_pair_contacts']==0 and f['mean_la'] is None


def test_no_geometry_filter_and_preserved_invalid_values():
    q,_=project_measurements(raw([dict(launch_speed='150')]),2015)
    assert q['invalid_ev'].item() and q['launch_speed'].item()==150


def test_terminal_bunt_exclusions_and_duplicate_stop():
    q,ex=project_measurements(raw([{},dict(type='S',events='catcher_interf',at_bat_number='2'),
        dict(des='A bunt single.',events='single',at_bat_number='3')]),2015)
    assert len(q)==1 and set(ex['measurement_exclusion'])=={'bunt','not_terminal_inplay'}
    with pytest.raises(ValueError): project_measurements(raw([{},{}]),2015)


def test_strict_historical_boundary():
    with pytest.raises(ValueError): project_measurements(raw(),2026)
    with pytest.raises(ValueError): project_measurements(raw(),2016)
