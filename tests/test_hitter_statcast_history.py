import polars as pl
import pytest
from universal_baseball.hitter_statcast_history import project_launch_history, annual_launch_features


def raw(rows=None):
    base = dict(game_date='2023-06-01', game_year='2023', game_type='R', game_pk='1',
                batter='2', at_bat_number='1', pitch_number='3', type='X', events='home_run',
                des='A home run.', launch_speed='100', launch_angle='25')
    return pl.DataFrame([base | r for r in (rows or [{}])])


def test_excludes_foul_and_bunt_but_keeps_missing_geometry():
    q = project_launch_history(raw([{}, dict(type='S', events=None, at_bat_number='2'),
                                    dict(des='Bunt single', at_bat_number='3')]), 2023)
    assert len(q) == 1 and q['complete_pair'].item()


def test_missing_measurements_are_not_zero():
    q = project_launch_history(raw([dict(launch_speed=None, launch_angle=None)]), 2023)
    r = annual_launch_features(q).row(0, named=True)
    assert r['terminal_nonbunt_contacts'] == 1 and r['measured_pair_contacts'] == 0
    assert r['mean_ev'] is None and r['ev95'] is None and r['hard_air_fraction'] is None


def test_ev_only_remains_useful_without_fabricated_angle():
    q = project_launch_history(raw([dict(launch_angle=None)]), 2023)
    r = annual_launch_features(q).row(0, named=True)
    assert r['measured_ev_contacts'] == 1 and r['ev95'] == 100
    assert r['measured_pair_contacts'] == 0 and r['mean_la'] is None


def test_invalid_measurements_preserved_outside_summary():
    q = project_launch_history(raw([dict(launch_speed='150')]), 2023)
    assert q['launch_speed'].item() == 150 and q['invalid_ev'].item()
    assert annual_launch_features(q)['mean_ev'].item() is None


def test_duplicate_and_multiple_terminal_contacts_fail():
    with pytest.raises(ValueError, match='Duplicate'):
        project_launch_history(raw([{}, {}]), 2023)
    with pytest.raises(ValueError, match='Duplicate'):
        project_launch_history(raw([{}, dict(pitch_number='4')]), 2023)


def test_historical_season_boundary():
    with pytest.raises(ValueError):
        project_launch_history(raw(), 2026)
    with pytest.raises(ValueError):
        project_launch_history(raw(), 2024)


def test_quantile_and_separate_denominators():
    q = project_launch_history(raw([dict(launch_speed='80'), dict(at_bat_number='2', launch_speed='100'),
                                    dict(at_bat_number='3', launch_speed=None)]), 2023)
    r = annual_launch_features(q).row(0, named=True)
    assert r['ev95'] == 99 and r['hard_hit_fraction'] == .5
    assert r['measured_la_contacts'] == 3 and r['measured_pair_contacts'] == 2
    assert r['hard_sweet_spot_contacts'] == 1 and r['pair_coverage'] == 2/3


def test_empty_regular_season_chunk_is_not_a_cross_season_error():
    q = project_launch_history(raw([dict(game_type='S')]), 2023)
    assert q.is_empty() and 'complete_pair' in q.columns
