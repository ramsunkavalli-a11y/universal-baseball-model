import polars as pl
import pytest
from universal_baseball.hitter_numeric_history import repair, BUCKETS
from universal_baseball.practical_hitter_v30 import EVENTS


def test_fractional_draft_time_and_pooled_pa_survive_unknown_initial_rows():
    source = pl.DataFrame(dict(row_id=[1, 2], player_id=[10, 20], origin_year=[2015, 2015],
        draft_known=[0, 1], draft_year=[None, 2012], draft_elapsed=[0, 0], label=[0., 2.]))
    source = source.with_columns(pl.lit(0).alias(f'pooled_{b}_pa') for b in BUCKETS)
    source = source.with_columns(pl.lit(prior).alias(f'pooled_{b}_{ev}')
        for b in BUCKETS for ev, (_, _, prior) in EVENTS.items())
    counts = pl.DataFrame([dict(player_id=20, season=2014, bucket='DSL',
        plate_appearances=101, strike_outs=20, unintentional_walks=10, hit_by_pitch=1,
        home_runs=2, babip_hits=30, babip_opportunities=60, doubles=4, triples=1),
        dict(player_id=20, season=2016, bucket='DSL', plate_appearances=999,
        strike_outs=500, unintentional_walks=100, hit_by_pitch=10, home_runs=20,
        babip_hits=300, babip_opportunities=600, doubles=40, triples=10)])
    fixed, changes = repair(source, counts)
    assert fixed['draft_elapsed'].to_list() == [0., .3]
    assert fixed['pooled_DSL_pa'][1] == pytest.approx(80.8)
    assert fixed['pooled_DSL_HR'][1] == pytest.approx((.8*2+3)/(80.8+100))
    assert fixed['label'].equals(source['label'])
    assert fixed.schema['pooled_DSL_pa'] == pl.Float64
    assert {c['feature'] for c in changes} >= {'draft_elapsed', 'pooled_DSL_pa'}
