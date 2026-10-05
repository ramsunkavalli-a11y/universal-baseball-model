from datetime import date

from universal_baseball.hitter_status_evidence import employment_events, organization_state, absence_state, reconcile

TEAMS = {135, 147}


def raw(day, text, code='SFA', target=135, source=None, tid=1, **extra):
    return dict(id=tid, date=day, effectiveDate=day, person=dict(id=1, fullName='Hitter'),
        typeCode=code, typeDesc='Signed as Free Agent' if code=='SFA' else 'Status Change',
        description=text, toTeam=dict(id=target) if target else {},
        fromTeam=dict(id=source) if source else {}, **extra)


def record(day, kind, tid=1, **extra):
    return dict(player_id=1, transaction_id=tid, available_date=date.fromisoformat(day),
        event_date=date.fromisoformat(day), kind=kind, il_kind=None, description='plain event',
        category='unspecified', surgery=False, duration_years=None, **extra)


def state(events):
    return organization_state(employment_events(events, TEAMS, date(2023,1,26)))


def test_latest_event_replaces_cumulative_signing():
    signed=raw('2022-11-01','Club signed Hitter.')
    released=raw('2022-12-01','Club released Hitter.','REL',tid=2)
    assert state([signed,released])['state']=='reported_release'
    rejoin=raw('2023-01-01','Club signed Hitter to a minor league contract.',tid=3)
    assert state([signed,released,rejoin])['state']=='minor_agreement'
    assert not state([signed,released,rejoin])['explicit_major_link']


def test_options_and_outrights_are_not_equivalent():
    activated=raw('2022-11-01','Club activated Hitter.','SC')
    option=raw('2022-12-01','Club optioned Hitter.','OPT',target=777,source=135,tid=2)
    assert state([activated,option])['explicit_major_link']
    outright=raw('2022-12-01','Club outrighted Hitter.','OUT',target=777,source=135,tid=3)
    assert not state([activated,outright])['explicit_major_link']
    assert state([activated,outright])['state']=='reserve_departure_organization_unconfirmed'


def test_same_day_ties_depend_on_endpoints_not_event_ids():
    release=raw('2023-01-01','Old club released Hitter.','REL',target=147)
    signed=raw('2023-01-01','New club signed Hitter.',target=135,tid=2)
    assert state([release,signed])['state']=='agreement_unspecified'
    same_club=raw('2023-01-01','Club released Hitter.','REL',target=135,tid=3)
    assert state([same_club,signed])['state']=='ambiguous_same_date'
    assert state([same_club,signed])==state([signed,same_club])


def test_late_resolution_and_rehab_do_not_create_job():
    late=raw('2022-11-01','Club activated Hitter.','SC',resolutionDate='2023-02-01')
    rehab=raw('2022-12-01','Club sent Hitter on a rehab assignment.','ASG',target=777,source=135,tid=2)
    assert state([late,rehab])['state']=='unknown'


def test_finite_game_count_not_days_and_future_report_not_used():
    finite=record('2022-08-12','suspended_unspecified',duration_games=80)
    future=dict(player_id=1,known_date='2023-02-01',event_date='2022-08-12',reported_return_date='2023-04-20')
    output=absence_state([finite],date(2023,1,26),[future])
    assert output['state']=='finite_game_suspension' and output['known_calendar_end'] is None
    assert output['original_duration_games']==80 and output['reported_return_date'] is None
    medical=record('2022-12-01','mlb_activation',tid=2)
    medical['il_kind']='activation'
    assert absence_state([finite,medical],date(2023,1,26))['state']=='finite_game_suspension'


def test_plain_activation_clears_suspension_not_legal_ban():
    suspended=record('2022-08-12','suspended_unspecified')
    activate=record('2022-08-14','mlb_activation',tid=2)
    assert absence_state([suspended,activate],date(2023,1,26))['state']=='reported_nonmedical_reinstatement'
    permanent=record('2022-08-12','permanent_ineligible')
    assert absence_state([permanent,activate],date(2023,1,26))['hard_unavailable']
    legal=record('2022-12-01','reinstated',tid=3)
    assert not absence_state([permanent,legal],date(2023,1,26))['hard_unavailable']


def test_negative_listing_conflict_and_later_release():
    pop=dict(candidate_key='2022:1',player_id=1,origin_year=2022,target_year=2023,
        information_date='2023-01-26',returned_40man=False,roster_cross_team_conflict=False,roster_status_conflict=False)
    activated=raw('2023-01-26','Club activated Hitter.','SC')
    output=reconcile(pop,[activated],[],TEAMS)
    assert not output['literal_returned_40man'] and output['status_major_link'] and output['status_negative_listing_conflict']
    old=raw('2022-11-01','Club activated Hitter.','SC')
    release=raw('2023-01-01','Club released Hitter.','REL',tid=2)
    output=reconcile(dict(pop,returned_40man=True),[old,release],[],TEAMS)
    assert output['literal_returned_40man'] and output['status_positive_listing_conflict'] and not output['status_major_link']
