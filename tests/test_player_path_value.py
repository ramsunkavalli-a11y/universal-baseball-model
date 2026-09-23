import numpy as np
import pytest

from universal_baseball.player_path_value import marginal_price, value_paths
from universal_baseball.player_path_distribution import crps, path_events, coarse_draws, forest_draws
import polars as pl


def price(war, rights=None, costs=None, **kwargs):
    w = np.asarray(war, float)
    args = dict(target_kind='whole_war', tail_complete=True, breakpoints=[2], rates=[1, 2])
    args.update(kwargs)
    return value_paths(w, np.ones_like(w) if rights is None else rights,
                       np.zeros_like(w) if costs is None else costs, **args)


def test_upside_is_priced_before_averaging():
    uncertain = price([[0], [12]])
    certain = price([[6]])
    assert uncertain['mean_controlled_war'] == certain['mean_controlled_war'] == 6
    assert uncertain['mean_surplus'] == 11
    assert certain['mean_surplus'] == 10
    assert price([[0], [12]], breakpoints=[], rates=[1])['mean_surplus'] == 6


def test_obligations_survive_no_rights_and_failure():
    assert price([[0, 0]], rights=[[0, 0]], costs=[[2, 3]])['mean_surplus'] == -5
    assert price([[4, 8]], rights=[[1, 0]], costs=[[1, 3]])['mean_surplus'] == 2


def test_no_double_risk_discount_or_hidden_floor():
    assert price([[0], [12]], weights=[.75, .25])['mean_surplus'] == 5.5
    assert price([[-2]], costs=[[3]])['mean_surplus'] == -3


def test_unknown_or_partial_value_fails_closed():
    assert price([[4]], target_kind='batting_replacement')['mean_surplus'] is None
    assert price([[4]], tail_complete=False)['mean_surplus'] is None
    assert price([[4]], costs=[[np.nan]])['mean_surplus'] is None
    with pytest.raises(ValueError):
        price([[4]], rights=[[1.5]])
    with pytest.raises(ValueError):
        price([[4]], weights=[2])


def test_continuous_price_and_crps():
    np.testing.assert_allclose(marginal_price([0, 1, 2, 3], [2], [1, 2]), [0, 1, 2, 4])
    np.testing.assert_allclose(crps([[0, 2], [2, 2]], [1, 1]), [.5, 1])


def test_events_preserve_failure_returns_and_negative_production():
    e = path_events([[0, 0, 0], [4, -1, 4]], [[0, 0, 0], [500, 0, 500]])
    assert e.tolist() == [[True, False, False, False], [False, True, True, True]]
    with pytest.raises(ValueError):
        path_events([[np.nan]], [[0]])


def test_donors_are_disjoint_and_never_self():
    n = 180
    f = pl.DataFrame({'player_id': np.arange(n), 'stage': ['Lower minors']*n,
                      'age': np.arange(n)%10+17., 'feature': np.arange(n)%13,
                      'war_h1': np.arange(n)%5., 'war_h2': np.arange(n)%3., 'war_h3': np.arange(n)%7.})
    q = f.head(3)
    draws, notes = forest_draws(f, q, ['age', 'feature'], 3)
    assert all(x['overlap'] == 0 for x in notes)
    assert not (draws == np.arange(3)[:, None]).any()
    assert not (coarse_draws(f, q) == np.arange(3)[:, None]).any()
    np.testing.assert_array_equal(draws, forest_draws(f, q, ['age', 'feature'], 3)[0])
