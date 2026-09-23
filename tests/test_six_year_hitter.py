import polars as pl
import pytest

from universal_baseball.six_year_hitter import ServiceSeason, account_control_path, extend_labels, mature_mask


def test_six_service_years_can_take_nine_calendar_years():
    years = [ServiceSeason(y, 0 if y < 2029 else 172, 0 if y < 2029 else 2.) for y in range(2026,2035)]
    r = account_control_path(0, years)
    assert r['exhaustion_year'] == 2034
    assert r['full_control_value'] == 12
    assert account_control_path(0, years[:6])['full_control_value'] is None


def test_partial_first_year_and_whole_final_season():
    years = [ServiceSeason(2026, 50, 1.)] + [ServiceSeason(y, 172, 2.) for y in range(2027,2034)]
    r = account_control_path(0, years)
    assert r['exhaustion_year'] == 2032
    assert r['full_control_value'] == 13  # no midseason prorating


def test_veteran_does_not_get_six_fresh_years():
    assert account_control_path(5*172, [ServiceSeason(2026,172,3.),ServiceSeason(2027,172,4.)])['full_control_value'] == 3
    assert account_control_path(6*172, [ServiceSeason(2026,172,3.)])['full_control_value'] == 0
    assert account_control_path(None, [ServiceSeason(2026,172,3.)])['full_control_value'] is None


def test_injured_zero_value_year_can_accrue_service():
    assert account_control_path(5*172, [ServiceSeason(2026,172,0.)])['exhaustion_year'] == 2026
    assert account_control_path(0, [ServiceSeason(2026,0,-1.)],terminal=True)['full_control_value'] == -1


@pytest.mark.parametrize('years', [[ServiceSeason(2026,173,1)], [ServiceSeason(2026,-1,1)],
    [ServiceSeason(2026,172,1),ServiceSeason(2028,172,1)], [ServiceSeason(2026,172,float('nan'))]])
def test_bad_paths_rejected(years):
    with pytest.raises(ValueError): account_control_path(0,years)


def test_labels_future_null_nonarrival_zero_and_pandemic():
    f=pl.DataFrame({'origin_year':[2010,2014,2025],'player_id':[1,1,1],
        **{f'war_h{h}':[0.,0.,None] for h in (1,2,3)}})
    t=pl.DataFrame({'season':[2016,2020,2025],'player_id':[2,2,2], 'component_war':[1.,1.,1.], 'mlb_pa':[100,100,100]})
    p=extend_labels(f,t)
    assert p['war_h6'].to_list() == [0.,0.,None]
    assert mature_mask(p,2025,6).tolist() == [True,False,False]
    assert mature_mask(p,2025,6,[1]).sum() == 0
    with pytest.raises(ValueError): mature_mask(p,2026,6)
