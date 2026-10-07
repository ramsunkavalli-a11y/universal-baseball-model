import pytest
from universal_baseball.defense_value import position_value, quality, predicted_runs


def test_positional_credit_is_actual_exposure_not_label():
    row={f'a_{p}':0 for p in range(2,11)}
    assert position_value(row,'a')==0
    row['a_2']=4374/2
    assert position_value(row,'a')==6.25
    row['a_2']=0;row['a_3']=4374
    assert position_value(row,'a')==-12.5
    row['a_3']=0;row['a_10']=162
    assert position_value(row,'a')==-17.5


def test_unknown_history_not_given_calibrated_grade():
    r=dict(channel='range_6',history_rate=0,quality_evidence_observed=False,
           range_calibration_fit_allowed=True,saved_range_calibration=3)
    assert quality(r,'calibrated')==0
    r['quality_evidence_observed']=True
    assert quality(r,'calibrated')==3


def test_channel_units_and_no_actual_count_in_forecast():
    r=dict(channel='framing',history_rate=2,rate_unit=1000,actual_native_opportunities=90000)
    row={'a_native_framing':3000}
    assert predicted_runs(row,r,'a','history')==6
    assert predicted_runs(row,r,'a','neutral')==0


def test_range_position_must_receive_its_own_opportunities():
    r=dict(channel='range_6',history_rate=-2,rate_unit=1500)
    assert predicted_runs({'a_6':750,'a_5':3000},r,'a','history')==-1
