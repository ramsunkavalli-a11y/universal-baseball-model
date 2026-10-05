import polars as pl
import pytest

from universal_baseball.hitter_dated_context import materialize


def source(position='UNKNOWN', age_unknown=1):
    r = dict(row_id=1, player_id=808975, origin_year=2024, target_year=2025, on_40man=0,
             source_position=position, age=27., age_centered=0., age_squared=0., age_unknown=age_unknown,
             next_pa=999, domestic_pa=0)
    r.update({'position_' + p: int(p == position) for p in [*[str(i) for i in range(1, 11)], 'Y', 'UNKNOWN']})
    return pl.DataFrame([r])


def context(codes=None, **extra):
    return dict(player_id=808975, origin_year=2024, target_year=2025, information_date='2025-01-24',
                returned_40man=True, roster_position_codes=['4'] if codes is None else codes,
                roster_cross_team_conflict=False, roster_status_conflict=False, **extra)


def foreign():
    return dict(player_id=808975, origin_year=2024, birth_date='1999-01-27', dated_role_hint='hitter_hint')


def test_only_declared_source_inputs_change():
    before = source()
    after, changes = materialize(before, [context()], [foreign()])
    r = after.row(0, named=True)
    assert r['on_40man'] == 1 and r['position_4'] == 1 and r['position_UNKNOWN'] == 0
    assert 25 < r['age'] < 26 and r['age_unknown'] == 0
    assert r['next_pa'] == 999 and r['domestic_pa'] == 0
    assert r['age_squared'] == r['age_centered'] ** 2
    assert len(changes) == 1


def test_known_age_and_position_are_not_overwritten():
    after, _ = materialize(source('3', 0), [context()], [foreign()])
    assert after['source_position'][0] == '3' and after['age'][0] == 27


@pytest.mark.parametrize('codes', [['I'], ['1', 'Y'], ['3', '4']])
def test_generic_ambiguous_and_two_way_listings_do_not_invent_a_position(codes):
    after, _ = materialize(source(), [context(codes)], [])
    assert after['source_position'][0] == 'UNKNOWN'


def test_missing_duplicate_or_wrong_date_fails():
    for rows in [[], [context(), context()], [dict(context(), information_date='2026-01-01')]]:
        with pytest.raises(ValueError):
            materialize(source(), rows, [])


def test_future_context_does_not_change_an_earlier_origin():
    before = materialize(source(), [context()], [foreign()])[0]
    extra = dict(context(), origin_year=2025, target_year=2026, information_date='2026-01-24', returned_40man=False)
    after = materialize(source(), [context(), extra], [foreign()])[0]
    assert before.equals(after)
