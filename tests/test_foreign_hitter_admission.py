import pytest
from universal_baseball.foreign_hitter_admission import materialize,COUNTS


def inputs(role='hitter_hint'):
    p=dict(candidate_key='2021:1',player_id=1,player_name='Hitter',origin_year=2021,
        information_date='2022-03-18',current_model_origin=False)
    f=dict(candidate_key=p['candidate_key'],player_id=1,origin_year=2021,information_date=p['information_date'],
        original_source_origin=False,dated_role_hint=role,recent_observed_domestic_pa=90,recent_observed_MLB_pa=10,recent_foreign_pa=500)
    def stint(y,b,n):
        return dict(season=y,player_id=1,team_id=2,sport_id=1 if b=='MLB' else 11,bucket=b,position='9',
            **{c:n if c=='plate_appearances' else 0 for c in COUNTS})
    return f,p,[stint(2019,'AAA',80),stint(2021,'MLB',10)]


def test_real_domestic_history_retained_and_future_cannot_change_inputs():
    f,p,rows=inputs();before=materialize([f],[p],rows)
    later=dict(rows[-1],season=2022,plate_appearances=700)
    assert materialize([f],[p],rows+[later])==before
    r=before[0];assert r['qualified_for_batting_input'] and r['recent_observed_mlb_pa']==10
    assert r['three_year_domestic_history'][1]['milb_season_canceled']
    assert r['three_year_domestic_history'][2]['levels']['AAA']['counts']['plate_appearances']==80
    assert r['new_forecast'] is None


def test_pitchers_and_unknowns_retained_but_not_approved_and_mixed_is_flagged():
    for role in ['pitcher_hint','unknown','two_way_or_conflicting_hints']:
        f,p,rows=inputs(role);r=materialize([f],[p],rows)[0]
        assert r['qualified_for_batting_input']==(role=='two_way_or_conflicting_hints')
        assert r['mixed_role_uncertain']==(role=='two_way_or_conflicting_hints')
        assert not r['ordinary_fulltime_hitter_role_certified'] and not r['current_employment_guaranteed']


def test_bad_joins_and_conflicting_history_fail():
    f,p,rows=inputs()
    with pytest.raises(ValueError):materialize([dict(f,information_date='2023-01-26')],[p],rows)
    with pytest.raises(ValueError):materialize([f,f],[p],rows)
    with pytest.raises(ValueError):materialize([dict(f,recent_observed_MLB_pa=0)],[p],rows)


def test_original_rows_are_not_reclassified_as_new_forecasts():
    f,p,rows=inputs();f['original_source_origin']=True;p['current_model_origin']=True
    assert materialize([f],[p],rows)==[]
