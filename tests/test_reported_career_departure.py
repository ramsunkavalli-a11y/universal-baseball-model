from datetime import date

import pytest

from universal_baseball.reported_career_departure import departure, forecast


def report(**extra):
    return dict(report_id=1, player_id=1, known_date="2018-09-21", event_date="2018-09-22",
                departure_kind="announced_medical_career_end", source_url="https://example.org/report",
                fact="Affirmative departure", **extra)


def test_announcement_and_effective_dates_both_gate():
    r = report()
    for day in [20, 21]:
        assert not departure([r], [], player_id=1, cutoff=date(2018, 9, day))["reported_departure"]
    assert departure([r], [], player_id=1, cutoff=date(2018, 9, 22))["reported_departure"]
    assert not departure([r], [], player_id=2, cutoff=date(2019, 1, 1))["reported_departure"]


def test_future_semantics_not_read_and_release_not_departure():
    future = dict(known_date="2020-01-01", event_date="2020-01-01")
    assert not departure([future], [], player_id=1, cutoff=date(2019, 1, 1))["reported_departure"]
    bad = report()
    bad["departure_kind"] = "released"
    with pytest.raises(ValueError):
        departure([bad], [], player_id=1, cutoff=date(2019, 1, 1))


def test_rights_transfer_not_return_but_playing_signing_is():
    captured = dict(transaction_id=10, player_id=1, known_date=date(2018, 11, 1),
                    event_date=date(2018, 11, 1), kind="return", type_code="TR")
    assert departure([report()], [captured], player_id=1, cutoff=date(2019, 1, 1))["reported_departure"]
    captured["type_code"] = "SFA"
    s = departure([report()], [captured], player_id=1, cutoff=date(2019, 1, 1))
    assert not s["reported_departure"] and s["return_evidence"] == captured


def test_explicit_return_and_later_departure():
    r = report()
    returning = dict(r, report_id=2, known_date="2018-12-01", event_date="2018-12-01",
                     departure_kind="announced_playing_return")
    later = dict(r, report_id=3, known_date="2019-12-01", event_date="2019-12-01")
    assert not departure([r, returning, later], [], player_id=1, cutoff=date(2019, 1, 1))["reported_departure"]
    assert departure([r, returning, later], [], player_id=1, cutoff=date(2020, 1, 1))["reported_departure"]


def test_gate_changes_only_unconditional_contribution():
    old = dict(p=.9, conditional_pa=500., rate=2., pa=450., value=3.)
    fixed = forecast(old, dict(reported_departure=True))
    assert fixed == dict(p=0., conditional_pa=500., rate=2., pa=0., value=0.)
    assert forecast(old, dict(reported_departure=False)) == old
