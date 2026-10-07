import pytest
from universal_baseball.defense_reference import (
    center, cutoff_center, relative_rate, relative_runs, reference_offset,
    neutral_position_prior)


def rec(pid, year, outs, runs, pos=8, valid=True):
    return dict(player_id=pid, season=year, native_outs=outs, range_runs=runs,
                position=pos, range_valid=valid)


def test_exposure_weighted_not_average_of_rates():
    c = center([rec(1, 2020, 1500, 3), rec(2, 2020, 3000, -3)])
    assert c['rate'] == 0 and c['outs'] == 4500 and c['people'] == 2


def test_unknown_center_not_zero():
    assert center([])['rate'] is None


def test_cutoff_excludes_all_held_people_and_future():
    rows = [rec(1, 2020, 100, 1), rec(6, 2022, 100, 9),
            rec(2, 2021, 100, 2), rec(2, 2022, 100, 3),
            rec(3, 2023, 100, 100), rec(3, 2019, 100, 100)]
    c = cutoff_center(rows, 2022, 1, 8)
    assert c['people'] == 1 and c['seasons'] == [2021, 2022]
    assert c['weighted_outs'] == 150 and c['weighted_runs'] == 4
    assert c['rate'] == 40


def test_changing_future_and_held_runs_does_not_change_cutoff():
    r = [rec(1, 2022, 1500, 10), rec(2, 2022, 1500, 3), rec(2, 2023, 1500, 10)]
    base = cutoff_center(r, 2022, 1, 8)
    r[0]['range_runs'] = r[2]['range_runs'] = -999
    assert cutoff_center(r, 2022, 1, 8) == base


@pytest.mark.parametrize('p', [3, 4, 5, 6])
def test_infield_unchanged(p):
    assert relative_rate(2, p, None) == 2
    assert relative_runs(3, p, 1500, None) == 3


def test_coordinate_shift_preserves_rank_and_can_preserve_value():
    a, b, c = 4., -2., 1.5
    assert relative_rate(a, 8, c) - relative_rate(b, 8, c) == a - b
    offset = reference_offset(8, 3000, c)
    assert relative_runs(8, 8, 3000, c) + (5 + offset) == 8 + 5
    assert relative_rate(relative_rate(a, 8, c), 8, -c) == a


def test_unknown_skill_not_measured_zero():
    assert relative_rate(None, 8, 2) is None
    assert relative_runs(None, 8, 1500, 2) is None
    assert relative_runs(None, 8, 0, 2) == 0


def test_neutral_prior_different_from_native_zero():
    prior = neutral_position_prior(8, 2)
    assert prior == dict(intrinsic_mean=2, relative_mean=0., measured_skill=False)
    assert relative_rate(0, 8, 2) == -2
    assert neutral_position_prior(7, None)['relative_mean'] is None


def test_missing_reference_not_imputed():
    assert relative_runs(3, 8, 1500, None) is None
    assert relative_rate(3, 8, None) is None
    assert reference_offset(8, 0, None) == 0


def test_invalid_exposure_rejected():
    with pytest.raises(AssertionError):
        reference_offset(8, -1, 2)
    with pytest.raises(AssertionError):
        center([rec(1, 2022, 0, 3)])
