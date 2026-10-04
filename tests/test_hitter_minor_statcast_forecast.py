import numpy as np
import polars as pl
from universal_baseball.hitter_minor_statcast_forecast import best_half, references, materialize, route, METRICS
from universal_baseball.post_arrival_history import player_fold


def annual():
    pids = [p for p in range(1, 100) if player_fold(p) != 0][:3]
    return pl.DataFrame([dict(player_id=p, season=year, league_id=112,
        measured_ev_contacts=10, measured_la_contacts=10, measured_pair_contacts=10,
        pair_coverage=1., mean_ev=80.+i, ev95=100.+i, best_half_ev=95.+i,
        mean_la=10.+i, la_sd=20.+i, hard_air_fraction=.2+i/10)
        for year in (2022, 2023) for i,p in enumerate(pids)])


def test_best_half_has_explicit_odd_sample_definition():
    assert best_half([]) is None
    assert best_half([50, 80, 100]) == 90
    assert best_half([50, 60, 80, 100]) == 90
    assert best_half([110]) == 110


def test_reference_ignores_later_seasons_and_held_players():
    a = annual(); held = next(p for p in range(100, 200) if player_fold(p) == 0)
    extra = a.head(1).with_columns(pl.lit(held,dtype=pl.Int64).alias('player_id'), pl.lit(999.).alias('mean_ev'))
    original = next(r for r in references(a, 0) if r['season'] == 2022)
    changed = a.with_columns(pl.when(pl.col('season') == 2023).then(999.).otherwise(pl.col('mean_ev')).alias('mean_ev'))
    assert original == next(r for r in references(pl.concat([changed, extra]), 0) if r['season'] == 2022)


def test_untracked_is_unknown_and_no_future_reading_enters_origin():
    a = annual(); pid = a['player_id'][0]
    f = pl.DataFrame(dict(row_id=[1,2], player_id=[pid,999999], origin_year=[2021,2022]))
    got, _ = materialize(f, a, 0)
    assert got['msc_own_ev_n'].to_list() == [0,0]
    assert got['msc_112_0_best_half_ev_known'].to_list() == [0.,0.]
    assert got['msc_112_0_best_half_ev'].to_list() == [0.,0.]


def test_route_does_not_use_test_outcomes_and_disables_absent_context():
    a = annual(); pids = a['player_id'].unique().to_list()
    f = pl.DataFrame(dict(row_id=[1,2], player_id=pids[:2], origin_year=[2022,2022],
                         next_pa=[100,0], prior_debut=[0,0]))
    got, _ = materialize(f, a, 0)
    _, te, contexts, _ = route(got, [1], [2], minimum_people=2)
    assert not te['msc_eligible'][0]
    assert te['msc_112_0_best_half_ev_known'][0] == 0
    _, first, _, _ = route(got, [1], [2], minimum_people=1)
    _, second, _, _ = route(got.with_columns(pl.when(pl.col('row_id') == 2).then(700).otherwise(pl.col('next_pa')).alias('next_pa')), [1], [2], minimum_people=1)
    assert first['msc_eligible'].equals(second['msc_eligible'])
    assert sum(c['enabled'] for c in contexts) == 0
