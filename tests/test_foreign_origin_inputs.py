import pytest
from universal_baseball.foreign_origin_inputs import qualify_role, materialize_inputs
from test_foreign_mover_support import annual


def population(year=2020):
    return dict(player_id=1, origin_year=year, information_date=f'{year + 1}-01-24',
                candidate_key=f'{year}:1', current_model_origin=True, roster_position_codes=['6'],
                returned_40man=True, roster_team_ids=[119], origin_has_positive_context=True)


def test_unknown_role_can_use_dated_hitter_hint_without_current_profile():
    pair = dict(player_id=1, domestic_year=2021, domestic_role='unknown')
    h = [dict(player_id=1, origin_year=2020, reviewed_role_hint='hitter_hint')]
    result = qualify_role(pair, [], [population()], h)
    assert result['supported_hitter'] and result['original_role'] == 'unknown'
    assert not result['full_historical_position_qualified']


def test_future_role_is_not_used_and_recorded_pitcher_not_overwritten():
    h = [dict(player_id=1, origin_year=2021, reviewed_role_hint='hitter_hint')]
    pair = dict(player_id=1, domestic_year=2021, domestic_role='unknown')
    assert not qualify_role(pair, [], [population(2021)], h)['supported_hitter']
    assert not qualify_role(dict(pair, domestic_role='pitcher'), [], [population()],
                            [dict(h[0], origin_year=2020)])['supported_hitter']
    with pytest.raises(ValueError, match='Future'):
        qualify_role(pair, [], [dict(population(), information_date='2022-01-01')], [])


def test_conflicting_same_year_roles_are_not_assumed_hitter():
    pair = dict(player_id=1, domestic_year=2021, domestic_role='unknown')
    s = [dict(player_id=1, season=2021, position=c, plate_appearances=1) for c in ['1', '3']]
    assert qualify_role(pair, s, [], [])['qualified_role'] == 'conflicting_hints'


def test_future_foreign_and_domestic_rows_do_not_change_origin_inputs():
    rows = [annual(2020, 'KBO')]
    before = materialize_inputs([population()], rows, [], [])
    future = dict(player_id=1, season=2025, sport_id=1, plate_appearances=999)
    assert before == materialize_inputs([population()], rows + [annual(2025, 'NPB', pa=99999)], [future], [])
    assert before[0]['recent_foreign_pa'] == 100
    assert before[0]['age_at_information_date'] != 27
    assert before[0]['foreign_history_counts']['NPB_0']['player_identity_and_stat_observed'] is False
    assert not before[0]['MLB_translation_fitted']


def test_conflicting_birthdays_stop_cross_league_inputs():
    with pytest.raises(ValueError, match='birthday'):
        materialize_inputs([population()], [annual(2020, 'KBO'), annual(2019, 'NPB', birth_date='1991-01-01')], [], [])
