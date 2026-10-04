import numpy as np
import polars as pl
from universal_baseball.hitter_workload_location import scalar_median, location_score
from universal_baseball.hitter_workload_risk import mixture_pmf


def test_zero_median_retains_positive_expected_pa_and_exact_tie():
    assert scalar_median(.1, 500, 3)['median'] == 0
    assert scalar_median(.5, 500, 3)['median'] == 0
    pmf = mixture_pmf(np.array([.1]), np.array([500]), 3)[0]
    assert np.isclose(pmf@np.arange(801), 50)


def test_scalar_crossing_matches_grid_with_skew_and_boundaries():
    for p in [.5001, .8, .99, 1]:
        for c in [1, 80, 400, 650, 800]:
            for k in [.1, 3, 1000]:
                pmf = mixture_pmf(np.array([p]), np.array([c]), k)[0]
                expected = int(np.argmax(np.cumsum(pmf) >= .5))
                assert scalar_median(p, c, k)['median'] == expected


def test_equal_year_scoring_not_pooled_and_zero_outcomes_kept():
    f = pl.DataFrame(dict(target_year=[2022, 2022, 2023], next_pa=[0, 0, 100], x=[0, 0, 0]))
    s = location_score(f, 'x')
    assert s['mae'] == 50 and s['bias'] == -50 and np.isclose(s['rmse'], np.sqrt(5000))


def test_median_totals_not_expected_pa_totals():
    f = pl.DataFrame(dict(target_year=[2022, 2022], next_pa=[0, 500], mean=[50, 50], median=[0, 0]))
    assert location_score(f, 'median')['mae'] == location_score(f, 'mean')['mae']
    assert location_score(f, 'median')['rmse'] > location_score(f, 'mean')['rmse']
    assert location_score(f, 'median')['total'] == 0 and location_score(f, 'mean')['total'] == 100
