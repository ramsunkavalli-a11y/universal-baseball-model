import pytest
from universal_baseball.hitter_team_record import context, record_rows, team_rows, rights_events, latest_rights


def test_dated_affiliation_and_unknown_are_distinct():
    teams = {(2018, 556): dict(club='Nashville', parent_id=133, parent_name='Oakland'),
             (2019, 556): dict(club='Nashville', parent_id=140, parent_name='Texas')}
    records = {(2018, 133): dict(wins=97, losses=65, win_pct=97/162)}
    r = context(origin=2018, club_year=2018, club_id=556, rostered=False, teams=teams, records=records)
    assert r['context_parent_id'] == 133 and r['org_record_known'] == 1
    assert r['org_record_centered'] == 97/162-.5
    stale = context(origin=2019, club_year=2018, club_id=556, rostered=False, teams=teams, records=records)
    assert stale['org_record_known'] == 0 and stale['org_record_centered'] == 0
    with pytest.raises(ValueError):
        context(origin=2018, club_year=2019, club_id=556, rostered=False, teams=teams, records=records)


def test_reject_future_or_incomplete_sources():
    with pytest.raises(ValueError):
        team_rows({'teams': []}, 2026)
    with pytest.raises(ValueError):
        record_rows({'records': []}, 2024)
    with pytest.raises(ValueError):
        team_rows({'teams': [{'season': 2019}]}, 2018)


def test_rights_resolution_uses_known_dates_and_flags_conflicts():
    teams = {(2017, 108): dict(parent_id=108)}
    raw = {'transactions': [dict(id=1, person={'id': 670867}, typeCode='SFA',
        date='2017-12-16', effectiveDate='2017-12-16', resolutionDate='2017-12-16', toTeam={'id':108})]}
    events = rights_events(raw, 2017, teams)
    assert latest_rights(events, 2016) is None
    assert latest_rights(events, 2017)['parent_id'] == 108
    conflict = dict(events[0], transaction_id=2, parent_id=144)
    assert latest_rights(events+[conflict], 2017)['parent_id'] is None
