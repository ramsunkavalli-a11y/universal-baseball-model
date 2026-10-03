from datetime import date
from universal_baseball.hitter_observed_return import reconcile, as_of


def event(day, kind='other', il=None, tid=1, known=None, text='record'):
    return dict(player_id=1, transaction_id=tid, event_date=day,
                available_date=known or day, kind=kind, il_kind=il,
                description=text, category='upper', surgery=False)


def test_observed_return_bounds_without_claiming_recovery():
    spells = reconcile([event('2022-07-10', il='placement')],
        [dict(start='2022-09-06', end='2022-10-05', pa=100)], date(2022,12,31))
    assert not spells[0]['open_observation']
    assert spells[0]['end_upper'] == date(2022,10,5)
    assert not spells[0]['exact_return_date_known']
    assert not spells[0]['medical_recovery_certified']


def test_late_entry_and_inside_window_are_not_cleared():
    w = [dict(start='2022-09-06', end='2022-10-05', pa=29)]
    for day in ['2022-09-16', '2022-10-12']:
        s = reconcile([event(day, il='placement')], w, date(2022,12,31))
        assert s[0]['open_observation']


def test_new_entry_and_transfer_prevent_blanket_clearing():
    rows = [event('2022-07-10', il='placement'),
            event('2022-09-16', il='transfer', tid=2)]
    s = reconcile(rows, [dict(start='2022-09-06',end='2022-10-05',pa=29)], date(2022,12,31))
    assert s[0]['open_observation']
    s = reconcile([rows[0], event('2022-10-12',il='placement',tid=3)],
                  [dict(start='2022-09-06',end='2022-10-05',pa=29)], date(2022,12,31))
    assert len(s) == 2 and not s[0]['open_observation'] and s[1]['open_observation']


def test_plain_return_not_unrelated_list_activation():
    placement = event('2022-07-10', il='placement')
    for text, expected in [('activated from reserve list', False),
                           ('activated from paternity list', True),
                           ('activated for All-Stars', True)]:
        s = reconcile([placement, event('2022-07-21','mlb_activation',tid=2,text=text)],
                      [], date(2022,12,31))
        assert s[0]['open_observation'] == expected


def test_future_version_and_no_pa_do_not_infer_health():
    rows = [event('2022-07-10', il='placement'),
            event('2022-08-01','mlb_return',tid=2,known='2023-01-01')]
    s = reconcile(rows, [dict(start='2022-09-06',end='2022-10-05',pa=0)],date(2022,12,31))
    assert s[0]['open_observation']
    assert len(as_of(rows,date(2022,12,31))) == 1
