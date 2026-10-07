import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_catcher_native_opportunity_v3 import decode


def page(tmp_path, year=2019, minimum=1, rows=None):
    p=tmp_path/'response.html'
    params=dict(seasonStart=year,seasonEnd=year,minPitches=minimum)
    if rows is None:
        rows=[dict(id=1,pitches=100,rv_tot=.2)]
    p.write_text('const serverParams = '+json.dumps(params)+'; const data = '+json.dumps(rows)+';',encoding='utf8')
    return p


def test_year_verified_before_metrics(tmp_path):
    with pytest.raises(AssertionError):
        decode(page(tmp_path,year=2026),2019,True)


def test_minimum_must_be_actual_pitch_setting(tmp_path):
    with pytest.raises(AssertionError):
        decode(page(tmp_path,minimum='q'),2019,True)


def test_qualified_anchor_separate(tmp_path):
    rows,params=decode(page(tmp_path,minimum='q'),2019,False)
    assert len(rows)==1 and params['minPitches']=='q'


def test_duplicate_player_and_zero_pitch_denominator_rejected(tmp_path):
    with pytest.raises(AssertionError):
        decode(page(tmp_path,rows=[dict(id=1,pitches=0,rv_tot=0)]),2019,True)
    with pytest.raises(AssertionError):
        decode(page(tmp_path,rows=[dict(id=1,pitches=100,rv_tot=0)]*2),2019,True)
