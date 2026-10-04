import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_talent_bridge import (
    event_counts, fit_graph, make_pairs, materialize, translated_probability,
)
from universal_baseball.post_arrival_history import player_fold


def source():
    rows = []
    for year in [2011, 2012]:
        for pid in range(1, 15):
            for level in ['AAA', 'MLB']:
                rows.append(dict(season=year, player_id=pid, bucket=level,
                                 plate_appearances=100, strike_outs=20,
                                 unintentional_walks=10, hit_by_pitch=1,
                                 home_runs=3 if level == 'MLB' else 5,
                                 babip_hits=25, doubles=6, triples=1))
    return pl.DataFrame(rows)


def test_accounting_and_normalization():
    f = source()
    c = event_counts(f)
    assert c[0, 4] == 18  # Singles do not subtract HR from BABIP hits again.
    assert np.all(c.sum(1) == 100)
    p = translated_probability(c[0], np.zeros(8))
    assert p.sum() == pytest.approx(1)
    bad = f.with_columns(pl.lit(2).alias('babip_hits'))
    with pytest.raises(ValueError):
        event_counts(bad)


def test_chronology_player_exclusion_and_disconnection():
    f = source()
    pairs = make_pairs(f, event_counts(f))
    pairs.append(dict(player_id=999, season=2011, fold=player_fold(999),
                      a='DSL', b='RK121', weight=100, delta=[0.] * 8))
    fold = 0
    offsets, note = fit_graph(pairs, cutoff=2011, held_fold=fold)
    assert set(offsets) == {'AAA', 'MLB'}
    assert note['max_source_year'] == 2011
    assert all(player_fold(p) != fold for p in note['people'])
    assert set(note['disconnected_buckets']) == {'DSL', 'RK121'} if player_fold(999) != fold else not note['disconnected_buckets']
    changed = [dict(p, delta=[100.] * 8) if p['season'] > 2011 or p['fold'] == fold else p for p in pairs]
    other, _ = fit_graph(changed, cutoff=2011, held_fold=fold)
    for b in offsets:
        np.testing.assert_array_equal(offsets[b], other[b])


def test_training_row_uses_own_cutoff():
    s = source()
    f = pl.DataFrame(dict(row_id=[0, 1], player_id=[1, 2], origin_year=[2011, 2012]))
    a, _ = materialize(s, f, held_fold=4)
    changed = s.with_columns(pl.when(pl.col('season') == 2012).then(8).otherwise(pl.col('home_runs')).alias('home_runs'))
    b, _ = materialize(changed, f, held_fold=4)
    assert a.row(0) == b.row(0)
    assert a.row(1) != b.row(1)
    with pytest.raises(ValueError):
        materialize(s.with_columns(pl.lit(2026).alias('season')), f, held_fold=4)
