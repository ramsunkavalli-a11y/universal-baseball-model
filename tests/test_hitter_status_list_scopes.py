from datetime import date
from universal_baseball.hitter_status_evidence_v2 import absence_state


def event(day, kind, text, tid, **fields):
    return dict(player_id=1, transaction_id=tid, available_date=date.fromisoformat(day),
        event_date=date.fromisoformat(day), kind=kind, description=text, il_kind=None, **fields)


def test_activation_clears_named_list_only():
    rows = [event('2022-08-12','suspended_unspecified','Suspended.',1,duration_games=80),
        event('2022-09-01','restricted','Placed on restricted list.',2),
        event('2022-09-03','nonmedical_activation','Activated from restricted list.',3)]
    out = absence_state(rows,date(2023,1,26))
    assert set(out['active_restrictions']) == {'suspended'}
    assert out['original_duration_games'] == 80 and out['known_calendar_end'] is None


def test_plain_activation_is_traced_and_not_a_medical_clearance():
    rows = [event('2024-08-12','suspended_unspecified','Suspended.',1),
        event('2024-08-14','mlb_activation','Club activated Hitter.',2,)]
    rows[1]['il_kind'] = 'unqualified_activation'
    out = absence_state(rows,date(2025,1,24))
    assert out['state'] == 'reported_nonmedical_reinstatement'
    assert out['trace'][-1]['date'] == '2024-08-14'
    rows[1]['il_kind'] = 'activation'
    assert 'suspended' in absence_state(rows,date(2025,1,24))['active_restrictions']


def test_same_day_is_not_ordered_by_id_and_permanent_cannot_be_bypassed():
    ban = event('2024-06-04','permanent_ineligible','Ineligible.',1)
    ordinary = event('2024-06-06','nonmedical_activation','Activated from restricted list.',2)
    assert absence_state([ban,ordinary],date(2025,1,24))['hard_unavailable']
    legal = event('2024-06-04','reinstated','Reinstated from ineligible list.',3)
    a = absence_state([ban,legal],date(2025,1,24)); b = absence_state([legal,ban],date(2025,1,24))
    assert a == b and a['hard_unavailable'] and a['active_restrictions']['ineligible']['ambiguous']
    later = dict(legal,transaction_id=4,event_date=date(2024,6,7),available_date=date(2024,6,7))
    assert not absence_state([ban,later],date(2025,1,24))['hard_unavailable']


def test_return_report_must_match_active_event_and_future_is_excluded():
    r = event('2022-08-12','suspended_unspecified','Suspended.',1,duration_games=80)
    report = dict(known_date='2022-10-25',event_date='2022-08-12',reported_return_date='2023-04-20')
    assert absence_state([r],date(2023,1,26),[report])['reported_return_date']=='2023-04-20'
    assert absence_state([r],date(2023,1,26),[dict(report,event_date='2021-08-12')])['return_report'] is None
    later = event('2022-07-01','deceased','Died.',2);later['available_date']=date(2023,2,1)
    assert absence_state([r,later],date(2023,1,26),[report])==absence_state([r],date(2023,1,26),[report])


def test_finite_calendar_expiry_is_not_reported_activation_or_game_count():
    r=event('2020-02-29','finite_ineligible','One year.',1,duration_years=1)
    before=absence_state([r],date(2020,12,31));after=absence_state([r],date(2021,3,1))
    assert before['known_calendar_end']=='2021-02-28' and before['original_duration_games'] is None
    assert after['state']=='finite_end_elapsed_return_unconfirmed' and not after['hard_unavailable']
