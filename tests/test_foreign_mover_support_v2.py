from universal_baseball.foreign_mover_support_v2 import make_pairs, support
from universal_baseball.post_arrival_history import player_fold
from test_foreign_mover_support import annual


def test_full_korean_2020_season_is_not_cancelled_domestic_evidence():
    p = make_pairs([annual(2020, 'KBO'), annual(2021, 'MLB')])
    assert p[0]['touches_2020'] and not p[0]['domestic_2020_exception']
    assert p[0]['domestic_year'] == 2021
    assert support(p, 2021, (player_fold(1) + 1) % 5)[0]['people'] == 1


def test_overseas_2020_to_normal_2021_retained():
    p = make_pairs([annual(2020, 'NPB'), annual(2021, 'MLB')])
    assert support(p, 2021, (player_fold(1) + 1) % 5)


def test_domestic_2020_exception_in_both_directions():
    p = make_pairs([annual(2019, 'NPB'), annual(2020, 'MLB'), annual(2021, 'NPB')])
    assert all(r['domestic_2020_exception'] for r in p)
    assert support(p, 2024, (player_fold(1) + 1) % 5) == []


def test_fold_and_cutoff_survive_repair():
    p = make_pairs([annual(2020, 'KBO'), annual(2021, 'MLB')])
    assert support(p, 2020, (player_fold(1) + 1) % 5) == []
    assert support(p, 2021, player_fold(1)) == []
