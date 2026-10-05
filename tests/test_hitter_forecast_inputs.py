import polars as pl
import pytest

from universal_baseball.hitter_forecast_inputs import pooled_inputs,BUCKETS,EVENTS


def fixtures():
    f=pl.DataFrame([dict(row_id=1,player_id=1,origin_year=2025,
        **{f'pa_{k}':(100 if k==0 else 0) for k in range(3)},
        **{f'quality_{k}':0. for k in range(3)},
        **{f'{b}_{k}_pa':(100. if b=='MLB' and k==0 else 0.) for b in BUCKETS for k in range(3)})])
    c=pl.DataFrame([dict(season=2025,player_id=1,bucket='MLB',plate_appearances=100,
        strike_outs=10,unintentional_walks=5,hit_by_pitch=1,babip_hits=15,
        babip_opportunities=60,home_runs=1,doubles=3,triples=1)])
    d=pl.DataFrame([dict(player_id=1,draft_year=2025,drafted=True,pick_number=4,school_class='4YR')])
    return f,c,d


def test_2025_production_and_draft_are_not_silently_omitted():
    f,c,d=fixtures();r=pooled_inputs(f,c,d,source_cutoff=2025).row(0,named=True)
    assert r['pooled_MLB_pa']==100 and r['draft_known']==1 and r['draft_elapsed']==0


def test_future_source_rejected_and_not_called_missing():
    f,c,d=fixtures()
    with pytest.raises(ValueError):pooled_inputs(f,c.with_columns(pl.lit(2026).alias('season')),d,source_cutoff=2025)
    with pytest.raises(ValueError):pooled_inputs(f,c,d,source_cutoff=2024)


def test_row_uses_its_own_origin_not_the_global_latest_year():
    f,c,d=fixtures();f=f.with_columns(pl.lit(2024).alias('origin_year'))
    r=pooled_inputs(f,c,d,source_cutoff=2025).row(0,named=True)
    assert r['pooled_MLB_pa']==0 and r['draft_known']==0


def test_duplicate_counts_rejected():
    f,c,d=fixtures()
    with pytest.raises(ValueError):pooled_inputs(f,pl.concat([c,c]),d,source_cutoff=2025)


def test_fractional_recency_after_initial_zero_rows_is_not_truncated():
    f,c,d=fixtures()
    many=pl.concat([f.with_columns(pl.lit(i).alias('row_id'),pl.lit(i).alias('player_id')) for i in range(1,103)])
    c=c.with_columns(pl.lit(102).alias('player_id'),pl.lit(2024).alias('season'),pl.lit('DSL').alias('bucket'),pl.lit(57).alias('plate_appearances'))
    result=pooled_inputs(many,c,d,source_cutoff=2025)
    assert result['pooled_DSL_pa'][-1]==45.6
    assert result.schema['pooled_DSL_pa']==pl.Float64
