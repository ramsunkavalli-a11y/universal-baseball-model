from datetime import date
import polars as pl
import pytest
from universal_baseball.hitter_forecast_tracking import project_measurements, materialize_tracking
from universal_baseball.hitter_statcast_measurement import project_measurements as historical
from universal_baseball.hitter_statcast_history import annual_launch_features


def raw(year=2025):
    base = dict(game_date=f'{year}-06-01', game_year=str(year), game_type='R', game_pk='1', batter='2',
        pitcher='3', stand='R', p_throws='L', at_bat_number='1', pitch_number='3', type='X',
        events='home_run', des='Home run.', launch_speed='100', launch_angle='25')
    return pl.DataFrame([base, base | dict(at_bat_number='2', launch_angle=None),
        base | dict(at_bat_number='3', events='single', des='Bunt single.'),
        base | dict(at_bat_number='4', events='field_error', des='A reaches on an interference error.')])


def test_historical_projection_equivalence():
    q, ex = project_measurements(raw(2024), 2024, source_cutoff=2024)
    old, old_ex = historical(raw(2024), 2024)
    assert q.equals(old) and ex.equals(old_ex)


def test_2025_missing_measurements_and_flags():
    q, ex = project_measurements(raw(), 2025, source_cutoff=2025)
    assert len(q) == 2 and len(ex) == 2
    a = annual_launch_features(q)
    f = pl.DataFrame(dict(row_id=[1, 2], origin_year=[2025, 2025], player_id=[2, 99]))
    out, controls, measures = materialize_tracking(f, a, source_cutoff=2025)
    assert len(controls) == 36 and len(measures) == 27
    assert out['sc_0_source_year_available'].to_list() == [1., 1.]
    assert out['sc_0_ev_n'].to_list() == [2, 0]
    assert out['sc_0_pair_n'].to_list() == [1, 0]
    assert out['sc_0_mean_ev_known'].to_list() == [1., 0.]
    assert out['sc_tracked'].to_list() == [True, False]


def test_future_source_duplicate_and_overlay_stop():
    with pytest.raises(ValueError): project_measurements(raw(2026), 2026, source_cutoff=2026)
    with pytest.raises(ValueError): project_measurements(raw(), 2025, source_cutoff=2024)
    with pytest.raises(ValueError): project_measurements(pl.concat([raw(), raw()]), 2025, source_cutoff=2025)
    q, _ = project_measurements(raw(), 2025, source_cutoff=2025); a = annual_launch_features(q)
    f = pl.DataFrame(dict(row_id=[1], origin_year=[2025], player_id=[2]))
    with pytest.raises(ValueError): materialize_tracking(f, a, source_cutoff=2024)
    with pytest.raises(ValueError): materialize_tracking(f, pl.concat([a, a]), source_cutoff=2025)
    out, _, _ = materialize_tracking(f, a, source_cutoff=2025)
    with pytest.raises(ValueError): materialize_tracking(out, a, source_cutoff=2025)


def test_measured_shift_award_not_discarded_as_interference():
    r = raw().head(1).with_columns(pl.lit('field_error').alias('events'),
        pl.lit('A reaches on a defensive shift violation error.').alias('des'))
    q, ex = project_measurements(r, 2025, source_cutoff=2025)
    assert len(q) == 1 and len(ex) == 0 and q['complete_pair'].item()
