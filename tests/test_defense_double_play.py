import pytest
from universal_baseball.defense_double_play import history, profile


def source(year=2022, pos=6, outs=3000, runs=2., valid=True):
    return dict(season=year, position=pos, native_outs=outs, official_outs=outs,
        dp_runs=runs, exposure_valid=valid)


def test_small_sample_is_actually_shrunk():
    h = history([source(outs=30, runs=1.)], 2022, 6)
    assert h['dp_raw_rate'] == 50.
    assert h['candidate'] == pytest.approx(1500/3030)
    assert h['dp_reliability'] == pytest.approx(30/3030)


def test_recency_uses_matching_run_and_out_weights():
    h = history([source(2020), source(2021), source(2022)], 2022, 6)
    assert h['dp_history_outs'] == 5250
    assert h['dp_history_runs'] == 3.5
    assert h['candidate'] == pytest.approx(5250/8250)


def test_future_old_and_other_position_cannot_leak():
    h = history([source(2019, runs=1000), source(2023, runs=1000), source(pos=4, runs=1000)], 2022, 6)
    assert h['candidate'] == 0 and h['fallback']


@pytest.mark.parametrize('row', [source(runs=None), source(valid=False), source(outs=0, runs=None)])
def test_unknown_is_not_measured_zero(row):
    h = history([row], 2022, 6)
    assert h['dp_history_seasons'] == 0 and h['dp_raw_rate'] is None and h['fallback']
    assert h['trace'][0]['weighted_runs'] is None


def test_measured_zero_and_negative_are_real_evidence():
    h = history([source(runs=0.)], 2022, 6)
    assert h['dp_history_seasons'] == 1 and not h['fallback']
    assert history([source(runs=-2.)], 2022, 6)['candidate'] == -.5


def test_invalid_duplicate_and_wrong_position_fail():
    for rows in ([source(), source()], [source(outs=-1)], [source(runs=float('inf'))]):
        with pytest.raises(ValueError):
            history(rows, 2022, 6)
    with pytest.raises(ValueError):
        history([], 2022, 8)


def test_profile_uses_dp_not_range_exposure():
    assert profile(dict(position=6, age=21, history_outs=9000, dp_history_outs=40)) == (6, '<=24', '<1500')


def test_short_2020_counts_actual_outs_only():
    h = history([source(year=2020, outs=450, runs=1.)], 2022, 6)
    assert h['dp_history_outs'] == 112.5 and h['dp_history_runs'] == .25
