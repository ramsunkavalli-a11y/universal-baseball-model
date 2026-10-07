import numpy as np
import pytest

from universal_baseball.defense_native_range import history, preflight, fit, predict, player_weights


def row(pid, origin, quality=1., pos=6):
    return dict(player_id=pid, origin_year=origin, window_end=origin+3,
                quality_rate=quality, position=pos, age=27., history_outs=3000.,
                history_rate=quality*.6, reliability=.5, window_has_2020=False)


def test_defensive_exposure_not_batting_pa():
    h, _ = history([dict(season=2022, position=6, range_valid=True, native_outs=3000,
                         range_runs=12, batting_pa=0)], 2022, 6)
    assert h['history_rate'] == 3
    assert h['reliability'] == .5


def test_unknown_and_other_position_not_imputed():
    h, p = history([dict(season=2022, position=4, range_valid=True, native_outs=3000,
                         range_runs=12)], 2022, 6)
    assert h['history_outs'] == 0 and p == []


def test_short_season_by_outs_and_recency():
    h, _ = history([dict(season=y, position=6, range_valid=True, native_outs=n, range_runs=r)
                    for y,n,r in [(2020,900,3),(2021,3000,10),(2022,3000,10)]], 2022, 6)
    assert h['history_outs'] == 4725
    assert h['history_runs'] == 15.75


def test_person_weights_not_repeated_support():
    assert np.allclose(player_weights([row(1,2016), row(1,2017), row(2,2016)]), [.5,.5,1])
    check, _ = preflight([row(1,2016),row(1,2017)], [row(5,2022)], 2022,0)
    assert check['training_people'] == 1 and not check['fit_allowed']


def test_chronology_and_identity_gate():
    with pytest.raises(AssertionError):
        preflight([row(1,2021)], [row(5,2022)], 2022,0)
    with pytest.raises(AssertionError):
        preflight([row(5,2016)], [row(5,2022)], 2022,0)


def test_ridge_replays_and_constant_features_safe():
    train = [row(i,2016,float(i%7-3)) for i in range(1,101)]
    model = fit(train)
    p = predict(model,train)
    assert np.isfinite(p).all() and p.shape == (100,)
    assert np.std(p) > 0
