import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_history_calibration import add_history, calibrate, calibration_pool, LEVELS
from universal_baseball.multiyear_hitter_value import CORE_RATES


def history_panel():
    p = pl.DataFrame({'origin_year': [2018, 2019, 2021, 2022], 'player_id': [1]*4,
                      'pa_lag0': [100., 200., 30., 400.], 'missing_lag0': [0]*4,
                      'age_centered': [-3., -2., 0., 1.], 'log_pa_lag0': np.log1p([100, 200, 30, 400]),
                      'path0__level_path__primary_level_change': [0., 1., 1., 1.]})
    return p.with_columns(*[pl.Series(r+'_lag0', [.1, .2, .3, .9]) for r in CORE_RATES],
                          *[pl.lit(float(l == 'AA')).alias('share_'+l+'_lag0') for l in LEVELS])


def test_gap_retained_no_future_history_and_no_synthetic_season():
    p = history_panel()
    q, names = add_history(p)
    r = q.filter(pl.col('origin_year') == 2021)
    assert r['history__last_gap'][0] == 2
    assert r['history__prior_seasons'][0] == 2
    expected = (.1*100*.7**3+.2*200*.7**2)/(100*.7**3+200*.7**2)
    assert r['history__prior_ubb_rate'][0] == pytest.approx(expected)
    assert q['history__prior_ubb_rate'][0] is None
    assert add_history(p.filter(pl.col('origin_year') <= 2021))[0].select(names).equals(q.head(3).select(names))
    assert not any(c.startswith('_h') for c in q.columns)


def test_missing_or_zero_exposure_is_not_history():
    p = history_panel().with_columns(pl.when(pl.col('origin_year') == 2019).then(1).otherwise(0).alias('missing_lag0'),
                                    pl.when(pl.col('origin_year') == 2018).then(0.).otherwise(pl.col('pa_lag0')).alias('pa_lag0'))
    q, _ = add_history(p)
    r = q.filter(pl.col('origin_year') == 2021)
    assert r['history__prior_seasons'][0] == 0
    assert r['history__last_gap'][0] is None
    assert r['history__pooled_ubb_rate'][0] == pytest.approx(.3)


def calibration_history():
    return pl.DataFrame({'origin_year': np.repeat([2013, 2014, 2015, 2016, 2019, 2021, 2022], 100),
                         'player_id': np.tile(np.arange(100), 7), 'prospect': [True]*700,
                         'probability': np.tile(np.linspace(.001, .5, 100), 7),
                         'actual': np.tile([0]*85+[1]*15, 7), 'target': ['regular_three']*700})


def test_calibration_maturity_pandemic_and_monotonicity():
    f = calibration_history()
    pool = calibration_pool(f, 2022, 'regular_three')
    assert pool['origin_year'].unique().sort().to_list() == [2013, 2014, 2015, 2016]
    test = f.filter(pl.col('origin_year') == 2022)
    p, note = calibrate(f, test, 2022, 'regular_three')
    assert not note['fallback'] and note['latest_label'] == 2019
    assert np.all(np.diff(p) > 0)
    changed = f.with_columns(pl.when(pl.col('origin_year') >= 2019).then(1-pl.col('actual')).otherwise(pl.col('actual')).alias('actual'))
    np.testing.assert_array_equal(p, calibrate(changed, test, 2022, 'regular_three')[0])


def test_calibration_fallback_other_cohorts_and_duplicates():
    f = calibration_history()
    test = f.tail(100).with_columns(pl.lit(False).alias('prospect'))
    np.testing.assert_array_equal(calibrate(f, test, 2022, 'regular_three')[0], test['probability'])
    p, note = calibrate(f.head(200), test, 2022, 'regular_three')
    assert note['fallback']
    np.testing.assert_array_equal(p, test['probability'])
    with pytest.raises(ValueError): calibrate(pl.concat([f, f]), test, 2022, 'regular_three')
    with pytest.raises(ValueError): calibration_pool(f, 2024, 'regular_three')
