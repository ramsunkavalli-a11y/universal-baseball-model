from copy import deepcopy

import pytest

from universal_baseball.nonmedical_observation import continuing_absence
from universal_baseball.hitter_status_evidence_v2 import absence_state
from datetime import date


def state(channels, hard=False):
    return dict(state='captured_legal_state', active_restrictions=channels,
        hard_unavailable=hard, return_report=None, reported_return_date=None)


def restriction(day='2022-08-12', kind='suspended_unspecified', **extra):
    return dict(event_date=day, kind=kind, ambiguous=False, **extra)


def window(start='2023-09-01', end='2023-10-01', pa=100, **extra):
    return dict(player_id=1, start=start, end=end, pa=pa, label='late') | extra


def run(a, windows, cutoff='2024-01-24'):
    return continuing_absence(1, a, windows, cutoff, list(range(2010, 2025)))


def test_positive_later_window_separates_observation_without_changing_legal_history():
    a = state({'suspended': restriction(duration_games=80)})
    before = deepcopy(a)
    r = run(a, [window()])
    assert a == before and r['captured_active_restrictions'] == a['active_restrictions']
    assert r['observation_unresolved_channels'] == {}
    assert r['channels_with_subsequent_observed_MLB_use']['suspended']['observed_return_upper'] == '2023-10-01'
    assert not r['observation_finite_nonmedical']
    assert not r['legal_reinstatement_certified'] and not r['medical_recovery_certified']
    assert r['unresolved_original_duration_games'] is None


@pytest.mark.parametrize('day', ['2023-08-31', '2023-09-01', '2023-10-02'])
def test_overlapping_same_day_and_earlier_windows_cannot_clear_new_restriction(day):
    a = state({'restricted': restriction(day, 'restricted')})
    # Overlap for the first two days; for Aug 31 use an annual interval.
    w = window(start='2023-01-01') if day == '2023-08-31' else window()
    r = run(a, [w])
    assert r['observation_unresolved_channels'] == a['active_restrictions']


def test_newer_parallel_channel_survives_and_new_entry_reopens_observation():
    a = state({'suspended': restriction(),
               'administrative': restriction('2023-09-15', 'administrative_leave')})
    r = run(a, [window()])
    assert set(r['channels_with_subsequent_observed_MLB_use']) == {'suspended'}
    assert set(r['observation_unresolved_channels']) == {'administrative'}
    assert r['observation_unresolved_nonmedical']
    new = state({'suspended': restriction('2023-10-02', duration_games=5)})
    assert run(new, [window()])['observation_finite_nonmedical']


@pytest.mark.parametrize('kind,scope', [('deceased', 'deceased'), ('permanent_ineligible', 'ineligible')])
def test_hard_rules_survive_unexpected_positive_appearances(kind, scope):
    a = state({scope: restriction(kind=kind)}, hard=True)
    r = run(a, [window()])
    assert r['hard_unavailable'] and r['observation_unresolved_channels'] == a['active_restrictions']
    assert scope in r['hard_status_activity_conflicts']
    assert not r['channels_with_subsequent_observed_MLB_use']


def test_future_or_backdated_availability_is_not_origin_evidence():
    a = state({'restricted': restriction(kind='restricted')})
    r = run(a, [window()], '2023-01-26')
    assert r == run(a, [], '2023-01-26')
    assert run(a, [window(available_date='2024-02-01')]) == run(a, [])


def test_no_positive_window_is_unknown_not_confirmation_of_absence():
    a = state({'restricted': restriction(kind='restricted')})
    r = run(a, [window(pa=0)])
    assert r['observation_unresolved_nonmedical']
    assert not r['absence_continuity_certified']
    assert not r['absence_of_positive_window_means_unavailable']


def test_earliest_upper_bound_does_not_invent_first_return_or_remaining_games():
    a = state({'suspended': restriction(duration_games=80)})
    a.update(return_report={'known_date': '2022-10-25'}, reported_return_date='2023-04-20')
    r = run(a, [window(), window('2023-08-01', '2023-08-31', label='preceding')])
    assert r['channels_with_subsequent_observed_MLB_use']['suspended']['observed_return_upper'] == '2023-08-31'
    assert r['current_return_date'] is None and a['reported_return_date'] == '2023-04-20'
    assert run(a, [], '2023-01-26')['current_return_date'] == '2023-04-20'


@pytest.mark.parametrize('w', [window(player_id=2), window('2023-10-02', '2023-10-01'),
    window(pa=-1), window(pa=1.5), window(available_date='2023-09-30')])
def test_invalid_windows_fail(w):
    with pytest.raises(ValueError):
        run(state({}), [w])


def test_future_legal_state_cannot_be_used():
    with pytest.raises(ValueError):
        run(state({'restricted': restriction('2025-01-01', 'restricted')}), [])


def test_medical_activation_is_not_a_legal_reinstatement_and_future_entry_is_ignored():
    def record(day, kind, tid, **extra):
        return dict(transaction_id=tid, player_id=1, event_date=date.fromisoformat(day),
            available_date=date.fromisoformat(day), kind=kind, description='injured list activation',
            il_kind=None, category='unspecified', surgery=False, duration_years=None) | extra
    rs = [record('2022-08-12', 'suspended_unspecified', 1, duration_games=80),
          record('2023-10-10', 'mlb_activation', 2, il_kind='activation')]
    cutoff = date(2024, 1, 24)
    a = absence_state(rs, cutoff)
    assert 'suspended' in a['active_restrictions']
    r = run(a, [window()])
    assert 'suspended' in r['captured_active_restrictions']
    assert not r['observation_finite_nonmedical']
    future = record('2023-10-02', 'restricted', 3, available_date=date(2024, 2, 1))
    assert run(absence_state(rs + [future], cutoff), [window()]) == r


def test_actual_legal_replay_precedes_observation_and_same_channel_reentry_survives():
    rs = [dict(transaction_id=i, player_id=1, event_date=date.fromisoformat(day),
        available_date=date.fromisoformat(day), kind=kind, description=text,
        il_kind=None, duration_years=None) for i, (day, kind, text) in enumerate([
            ('2022-08-01', 'restricted', 'placed on restricted list'),
            ('2022-08-03', 'nonmedical_activation', 'activated from restricted list'),
            ('2023-10-02', 'restricted', 'placed on restricted list')])]
    a = absence_state(rs, date(2024, 1, 24))
    r = run(a, [window()])
    assert r['observation_unresolved_channels']['restricted']['event_date'] == '2023-10-02'
    assert r['observation_unresolved_nonmedical']
