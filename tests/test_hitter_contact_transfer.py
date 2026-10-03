import polars as pl
import numpy as np
from universal_baseball.hitter_contact_transfer import bucket,classify,materialize


def test_actual_league_and_missing_counts():
    assert bucket('aaa',125)=='MEX' and bucket('rk',130)=='DSL' and bucket('MLB',103)=='MLB'
    f=pl.DataFrame({'row_id':[1,2],'origin_year':[2022,2022],'player_id':[1,2]})
    c=pl.DataFrame({'season':[2022],'player_id':[1],'bucket':['MLB'],'core_bin':['PULL_OFFB'],'contacts':[27]})
    o=pl.DataFrame({'season':[2022],'player_id':[1],'bucket':['MLB'],'plate_appearances':[40]})
    q,_=materialize(f,c,o,['MLB'])
    assert np.isclose(q['shape_MLB_PULL_OFFB'][0],37/127)
    assert q['shape_MLB_available'].to_list()==[1,0]
    assert q['shape_MLB_log_n'][1]==0 and q['shape_MLB_PULL_OFFB'][1]==.1
    assert q['shape_MLB_coverage'][0]==27/40


def test_side_and_missing_direction():
    f=pl.DataFrame({'hc_x':[80.,80.,None,None],'hc_y':[150.,150.,None,None],'stand':['R','L','R','R'],'bb_type':['fly_ball','fly_ball','fly_ball','popup']})
    q=classify(f)
    assert q['core_bin'].to_list()==['PULL_OFFB','OPPO_OFFB',None,'IFFB']
