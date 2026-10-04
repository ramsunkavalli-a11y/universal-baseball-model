from datetime import date
from urllib.parse import parse_qs, urlsplit
import polars as pl
import pytest
from universal_baseball.hitter_minor_statcast_source import (
    COLUMNS, contact_url, split_window, validate_contact_response)


def test_date_and_source_boundary():
    a=date(2023,4,1); b=date(2023,4,7)
    q=parse_qs(urlsplit(contact_url(a,b)).query)
    assert q['hfGT']==['R|'] and q['hfPR']==[r'hit\.\.into\.\.play|']
    assert 'hfFlag' not in q and 'hfLevel' not in q
    assert parse_qs(urlsplit(contact_url(a,b,tracked=True)).query)['chk_is..tracked']==['on']
    for y in [2020,2025,2026]:
        with pytest.raises(ValueError):contact_url(date(y,4,1),date(y,4,2))
    assert split_window(a,b)==[(a,date(2023,4,4)),(date(2023,4,5),b)]
    with pytest.raises(ValueError):split_window(a,a)


def test_contact_identity_measurement_is_not_eligibility():
    values={c:None for c in COLUMNS}
    values.update(game_date='2023-04-01',game_year='2023',game_type='R',
        game_pk='1',batter='2',at_bat_number='1',pitch_number='3',type='X',events='home_run')
    f=pl.DataFrame([values],schema={c:pl.String for c in COLUMNS})
    assert validate_contact_response(f,date(2023,4,1),date(2023,4,1))
    with pytest.raises(ValueError):validate_contact_response(pl.concat([f,f]),date(2023,4,1),date(2023,4,1))
    with pytest.raises(ValueError):validate_contact_response(f.with_columns(pl.lit('S').alias('type')),date(2023,4,1),date(2023,4,1))


def test_additive_nonterminal_projection_boundary():
    from universal_baseball.hitter_minor_statcast_source_v2 import validate_contact_response as checked
    values={c:None for c in COLUMNS}
    values.update(game_date='2023-07-01',game_year='2023',game_type='R',game_pk='729589',
        batter='694025',at_bat_number='71',pitch_number='2',type='X',events='sac_fly')
    first=dict(values,pitch_number='1',type='S',events=None,launch_speed='71.4',launch_angle='15')
    f=pl.DataFrame([first,values],schema={c:pl.String for c in COLUMNS})
    assert checked(f,date(2023,7,1),date(2023,7,1))
    with pytest.raises(ValueError):validate_contact_response(f,date(2023,7,1),date(2023,7,1))
    with pytest.raises(ValueError):checked(f.with_columns(pl.lit('sac_fly').alias('events')),date(2023,7,1),date(2023,7,1))
