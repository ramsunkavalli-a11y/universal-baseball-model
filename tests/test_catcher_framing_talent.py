import numpy as np
import pytest

from universal_baseball.catcher_framing_talent import features,preflight,fit,predict,score
from universal_baseball.catcher_framing_baseline import history,recover_unknown_age


def row(pid,origin=2018,quality=.5):
    n=1000+pid*10
    return dict(player_id=pid,origin_year=origin,window_end=origin+3,quality_rate=quality,
                history_pitches=n,history_runs=quality*n/1000,history_rate=quality*n/(n+6000),
                reliability=n/(n+6000),history_left_truncated=origin<2020,age=27.,
                future_pitches=10000,future_runs=quality*10)


def test_mature_labels_and_whole_player_separation():
    with pytest.raises(AssertionError):
        preflight([row(1,2021)],[row(5,2022)],2022,0)
    with pytest.raises(AssertionError):
        preflight([row(5)],[row(5,2022)],2022,0)
    with pytest.raises(AssertionError):
        preflight([{**row(1),'quality_rate':None}],[row(5,2022)],2022,0)


def test_repeated_rows_and_one_origin_do_not_pass_learning_guard():
    c=preflight([row(1),row(1,2019)],[row(5,2022)],2022,0)
    assert c['training_people']==1 and not c['fit_allowed']
    tr=[row(pid) for pid in range(1,101) if pid%5!=0]
    assert not preflight(tr,[row(105,2022)],2022,0)['fit_allowed']


def test_replay_constant_missing_age_features_safe():
    tr=[row(i,2018,float(i%5-2)) for i in range(1,101)]
    m=fit(tr);p=predict(m,tr)
    assert np.isfinite(p).all() and np.std(p)>0
    assert features({**tr[0],'age':None})['age_missing']


def test_value_descriptor_uses_received_pitches_not_defensive_outs():
    r={**row(1),'forecast':.5,'future_pitches':2000,'future_runs':1.,'future_outs':9000}
    s=score([r],'forecast')
    assert s['oracle_exposure_predicted_runs']==1 and s['rmse']==0


def test_transparent_history_shrinks_tiny_sample_and_ignores_future():
    a=dict(season=2022,pitches=5,framing_runs=.1,framing_measurement_valid=True)
    b={**a,'season':2023,'framing_runs':999}
    h=history([a,b],2022)
    assert h['history_rate']==pytest.approx(100/6005)
    assert h['reliability']==pytest.approx(5/6005)
    assert not history([{**a,'framing_measurement_valid':False}],2022)['quality_evidence_observed']


def test_age_carry_uses_only_consistent_dated_past():
    prior=[dict(snapshot_year=2019,age_years=24),dict(snapshot_year=2021,age_years=26),dict(snapshot_year=2022,age_years=None)]
    assert recover_unknown_age(2022,prior)['age']==27
    assert recover_unknown_age(2022,[*prior,dict(snapshot_year=2023,age_years=45)])['age']==27
    assert recover_unknown_age(2022,[*prior,dict(snapshot_year=2020,age_years=22)])['conflict']
    assert recover_unknown_age(2025,[dict(snapshot_year=2020,age_years=25)])['age'] is None
