import pytest
from universal_baseball.defense_first_base_prior import estimate, reference


def rows():
    return [dict(player_id=i*5+1,season=y,position=3,range_valid=True,
                 native_outs=100,range_runs=-1.) for i in range(20) for y in (2021,2022)]


def test_no_history_is_prior_not_measured_zero():
    assert estimate(0,0,-2)==-2


def test_prior_does_not_center_the_observation():
    assert estimate(2,3000,-2)==pytest.approx(-.5)
    assert estimate(2,3000,0)==.5


def test_future_and_entire_held_fold_excluded():
    r=rows();a=reference(r,2022,0)
    r+=[dict(player_id=1000,season=2022,position=3,range_valid=True,native_outs=1000,range_runs=1000),
        dict(player_id=1001,season=2023,position=3,range_valid=True,native_outs=1000,range_runs=1000)]
    assert reference(r,2022,0)==a
    assert a['rate']==-15 and a['people']==20


def test_people_and_seasons_required():
    assert reference(rows()[:2],2022,0)['fallback']
    assert reference([r for r in rows() if r['season']==2022],2022,0)['fallback']


def test_invalid_measurement_not_zero_skill():
    r=rows();a=reference(r,2022,0)
    r.append(dict(player_id=999,season=2022,position=3,range_valid=False,native_outs=1000,range_runs=None))
    assert reference(r,2022,0)==a


def test_short_2020_uses_actual_exposure():
    r=rows()
    r=[dict(x,season=x['season']-1) for x in r]
    assert reference(r,2021,0)['outs']==3000
