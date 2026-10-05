import pytest
from universal_baseball.foreign_mover_support import COUNTS, make_pairs, support, aggregate_foreign
from universal_baseball.post_arrival_history import player_fold


def annual(year, league, pid=1, role='hitter', **changes):
    r = dict(season=year, league=league, player_id=pid, role=role,
             source_name='Example', birth_date='1990-01-01', **{c: 0 for c in COUNTS})
    r.update(pa=100, ab=80, hits=20, so=10, hr=2, bb=20)
    r.update(changes)
    return r


def test_same_season_not_counted_twice_and_direction_is_preserved():
    rows = [annual(2018, 'NPB'), annual(2018, 'MLB'), annual(2019, 'MLB'), annual(2020, 'NPB')]
    p = make_pairs(rows)
    assert len([r for r in p if r['mechanism'] == 'same_season']) == 1
    assert {(r['a'], r['b']) for r in p if r['mechanism'] == 'consecutive_season'} == {('NPB', 'MLB'), ('MLB', 'NPB')}


def test_completed_year_and_whole_player_holdout():
    p = make_pairs([annual(2018, 'NPB'), annual(2019, 'MLB')])
    other = (player_fold(1) + 1) % 5
    assert support(p, 2018, other) == []
    assert support(p, 2019, player_fold(1)) == []
    assert support(p, 2019, other)[0]['people'] == 1


def test_future_extra_rows_do_not_change_earlier_support():
    p = make_pairs([annual(2018, 'NPB'), annual(2019, 'MLB')])
    q = make_pairs([annual(2018, 'NPB'), annual(2019, 'MLB'), annual(2024, 'NPB', pid=2)])
    assert support(p, 2019, 4) == support(q, 2019, 4)


def test_repeated_seasons_are_not_people_and_pitchers_separate():
    rows = [annual(2016, 'NPB'), annual(2017, 'MLB'), annual(2018, 'NPB'), annual(2019, 'MLB'),
            annual(2018, 'NPB', pid=2), annual(2019, 'MLB', pid=2, role='pitcher')]
    p = make_pairs(rows)
    k = next(f for f in range(5) if f not in {player_fold(1), player_fold(2)})
    a = support(p, 2019, k)
    hitter = next(r for r in a if r['a'] == 'NPB' and r['domestic_role'] == 'hitter')
    assert hitter['pairs'] == 2 and hitter['people'] == 1
    assert any(r['domestic_role'] == 'pitcher' for r in a)


def test_shortened_2020_is_not_normal_bridge_evidence():
    p = make_pairs([annual(2019, 'NPB'), annual(2020, 'MLB')])
    assert p[0]['touches_2020'] and support(p, 2024, (player_fold(1) + 1) % 5) == []


def test_duplicates_or_future_source_fail():
    with pytest.raises(ValueError, match='Duplicate'):
        make_pairs([annual(2018, 'NPB'), annual(2018, 'NPB')])
    with pytest.raises(ValueError, match='Future'):
        make_pairs([annual(2025, 'NPB')])


def test_traded_foreign_stints_sum_once_and_unmapped_dont_become_zero_talent():
    rows = [annual(2018, 'NPB'), annual(2018, 'NPB'), annual(2018, 'NPB', pid=None)]
    result = aggregate_foreign(rows, 'NPB')
    assert len(result) == 1 and result[0]['pa'] == 200
    assert len(rows) == 3
