import pytest
from universal_baseball.defense_budget_source import dual_start, reviewed_dh_starts


def box(order='200', starts=1, roles=('1', '10')):
    p = dict(person={'id': 7}, battingOrder=order,
             stats={'pitching': {'gamesStarted': starts}},
             allPositions=[{'code': r} for r in roles])
    return {'teams': {'home': {'players': {'ID7': p}}}}


def test_dual_start_requires_both_roles_and_starting_order():
    assert dual_start(box(), 7, 2022)['certified']
    assert not dual_start(box(roles=('10',)), 7, 2022)['certified']
    assert not dual_start(box(order='201'), 7, 2022)['certified']
    assert not dual_start(box(order=None), 7, 2022)['certified']


def test_relief_and_pre_rule_starts_do_not_receive_dh_credit():
    assert not dual_start(box(starts=0), 7, 2022)['certified']
    assert dual_start(box(), 7, 2021)['status'] == 'outside_rule_scope'


def test_identity_duplicates_remain_unresolved():
    b = box()
    b['teams']['away'] = b['teams']['home']
    assert dual_start(b, 7, 2022)['status'] == 'unresolved_identity'


def test_additive_ledger_does_not_count_nonstarting_appearances():
    a = dict(game_id=1, **dual_start(box(), 7, 2022))
    b = dict(game_id=2, **dual_start(box(order='201'), 7, 2022))
    assert reviewed_dh_starts(125, [a, b])['reviewed_starts'] == 126
    with pytest.raises(ValueError): reviewed_dh_starts(125, [a, a])
    c = dict(game_id=3, **dual_start(box(roles=('10',)), 7, 2022))
    with pytest.raises(ValueError): reviewed_dh_starts(125, [c])


def test_rule_certifies_start_even_without_later_dh_appearance():
    r = dual_start(box(roles=('1',)), 7, 2022)
    assert r['certified'] and r['DH_evidence_basis'] == 'rule_5_11b_starting_pitcher_in_lineup'
    assert not dual_start(box(roles=('1',),order='201'), 7, 2022)['certified']
    assert dual_start(box(roles=()), 7, 2022)['status'] == 'unresolved_dual_role'
