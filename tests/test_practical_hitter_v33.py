import sys
from pathlib import Path
import numpy as np
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_practical_hitter_v33 as s


def sample():
    o=dict(row_id=1,origin_year=2021,player_id=7)
    for lag in range(3):
        o.update({f'pa_{lag}':0,f'quality_{lag}':0})
        o.update({f'{b}_{lag}_pa':0 for b in s.r.BUCKETS})
    c=pl.DataFrame([dict(player_id=7,season=2019,bucket='AAA',plate_appearances=100,
        strike_outs=20,unintentional_walks=10,hit_by_pitch=1,home_runs=10,babip_hits=25,
        babip_opportunities=65,doubles=7,triples=0)])
    d=pl.DataFrame([dict(player_id=7,draft_year=2020,pick_number=4,school_class='4YR JR',drafted=True),
        dict(player_id=7,draft_year=2024,pick_number=100,school_class='4YR SR',drafted=True)])
    return pl.DataFrame([o]),c,d


def test_pooled_actual_counts_not_separate_season_priors():
    f,c,d=sample();v=s.materialize(f,c,d).row(0,named=True)
    assert np.isclose(v['pooled_AAA_pa'],60)
    assert np.isclose(v['pooled_AAA_HR'],(6+3)/(60+100))
    assert np.isclose(v['pooled_DSL_HR'],.03)


def test_future_pick_and_future_counts_do_not_change_inputs():
    f,c,d=sample();a=s.materialize(f,c,d)
    d=d.with_columns(pl.when(pl.col('draft_year')==2024).then(1).otherwise(pl.col('pick_number')).alias('pick_number'))
    c=pl.concat([c,c.with_columns(pl.lit(2024).alias('season'),pl.lit(800).alias('plate_appearances'))],how='vertical_relaxed')
    assert a.equals(s.materialize(f,c,d))
    assert a['pick_number'][0]==4


def test_fixed_scale_has_no_rare_training_sd_division():
    f=pl.DataFrame({'pooled_MEX_HBP':[.01,.06],'pooled_MEX_pa':[0.,300.], 'career_mlb_observed_pa':[0,6000]})
    np.testing.assert_allclose(s.safe_matrix(f,f.columns),[[0,0,0],[.5,.5,1]])
