import pytest
from universal_baseball.hitter_preseason_population import (
    available_date, classify_event, reconcile_transactions, roster_people, transaction_key)


def event(pid=1, **updates):
    row = dict(id=10, person=dict(id=pid, fullName='Player', link='/api/v1/people/'+str(pid)),
               fromTeam=dict(id=1), toTeam=dict(id=2), date='2017-12-09',
               effectiveDate='2017-12-09', resolutionDate='2017-12-09',
               typeCode='TR', typeDesc='Trade', description='Trade')
    row.update(updates)
    return row


def test_one_trade_keeps_all_people_and_cash():
    rows = [event(1), event(2), event(0)]
    summary = reconcile_transactions(rows, [('2017-12-01','2017-12-31',rows)], '2017-12-01','2017-12-31')
    assert summary == dict(records=3, transaction_ids=1, composite_events=3, identical_duplicate_rows=0)
    assert len({transaction_key(r) for r in rows}) == 3


def test_partition_cannot_erase_person_or_duplicate():
    rows = [event(1), event(2), event(2)]
    with pytest.raises(AssertionError):
        reconcile_transactions(rows, [('2017-12-01','2017-12-31',rows[:2])], '2017-12-01','2017-12-31')


def test_window_bounds_are_checked():
    with pytest.raises(AssertionError):
        reconcile_transactions([event()], [('2017-12-10','2017-12-31',[event()])], '2017-12-01','2017-12-31')


def test_later_resolution_not_backdated():
    assert available_date(event(resolutionDate='2018-02-01')) == '2018-02-01'
    assert available_date(event(effectiveDate='2018-03-27')) == '2018-03-27'
    assert available_date({'effectiveDate':'2017-12-09'}) is None


def test_bad_date_fails():
    with pytest.raises(ValueError):
        available_date(event(date='2017-99-09'))


def test_roster_duplicate_identity_and_diagnostics():
    first = dict(person=dict(id=1, fullName='Player',link='one'),status=dict(code='A'))
    second = dict(first,status=dict(code='D'))
    assert len(roster_people([first, second])[1]) == 2
    with pytest.raises(AssertionError):
        roster_people([first, dict(first, person=dict(id=1,fullName='Other',link='one'))])


def test_minor_contract_not_guaranteed_job():
    row = event(typeDesc='Signed as Free Agent',description='Team signed RHP/DH Player to a minor league contract.')
    assert classify_event(row,{1,2}) == 'minor_agreement'
    assert classify_event(event(typeDesc='Signed as Free Agent',description='Team signed Player.'),{1,2}) == 'agreement_unspecified'


def test_later_outcomes_not_part_of_event_classification():
    row = event(description='Team signed RF Player.', typeDesc='Signed as Free Agent')
    assert classify_event(row,{1,2}) == classify_event(dict(row,next_pa=700,country='Japan'),{1,2})
    assert classify_event(event(description='Player elected free agency.',typeDesc='Declared Free Agency'),{1,2}) == 'scope_exit'
