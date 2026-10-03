from pathlib import Path
import sys
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_hitter_late_role_v46 import strict_frame


def payload():
    return {'stats':[dict(type={'displayName':'byDateRange'},group={'displayName':'hitting'},totalSplits=1,
        splits=[dict(season='2016',sport={'id':1},player={'id':10},stat={'plateAppearances':32,'gamesPlayed':10})])]}


def test_missing_pa_is_not_zero_and_duplicate_aggregate_not_summed():
    p=payload();assert strict_frame(p,2016)['pa'][0]==32
    p['stats'][0]['splits'].append(p['stats'][0]['splits'][0]);p['stats'][0]['totalSplits']=2
    with pytest.raises(AssertionError):strict_frame(p,2016)
    p=payload();del p['stats'][0]['splits'][0]['stat']['plateAppearances']
    with pytest.raises(AssertionError):strict_frame(p,2016)


def test_wrong_season_and_incomplete_response_fail():
    with pytest.raises(AssertionError):strict_frame(payload(),2017)
    p=payload();p['stats'][0]['totalSplits']=2
    with pytest.raises(ValueError):strict_frame(p,2016)
