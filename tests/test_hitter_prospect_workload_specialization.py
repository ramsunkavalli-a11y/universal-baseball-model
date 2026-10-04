"""Training eligibility and exact fixed-head connection regressions."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
import polars as pl
from evaluate_hitter_prospect_workload_specialization import specialize, connect, conditional_score


def test_only_origin_never_debut_positive_training():
    f = pl.DataFrame(dict(row_id=[0,1,2,3],prior_debut=[0,1,0,1],next_pa=[400,400,0,0]))
    assert specialize(f)['row_id'].to_list()==[0]
    mutated = f.with_columns(pl.when(pl.col('row_id')==2).then(600).otherwise(pl.col('next_pa')).alias('next_pa'))
    assert specialize(mutated)['row_id'].to_list()==[0,2]


def test_connection_preserves_nonarrivals_and_established_exact():
    q = pl.DataFrame(dict(prior_debut=[0,0,1],preseason_raw_conditional_pa=[200.,200.,300.],preseason_p=[.5,0.,.9],
        preseason_pa=[100.,0.,270.],preseason_value=[.2,0.,.54],translated_ridge_value=[.3,0.,.54],
        baseline_rate=[0.,0.,0.],translated_ridge_rate=[.6,.6,0.],origin_replacement_rate=[.002,.002,.002]))
    out = connect(q,'x',np.array([400.,-10.]))
    assert out['x_pa'].to_list()==[200.,0.,270.]
    assert out['x_value'].to_list()==[.4,0.,.54]
    assert out['x_conditional_pa'].to_list()==[400.,1.,300.]
    assert out['x_translated_value'].to_list()==[.6,0.,.54]
    assert out.select(q.columns).equals(q)


def test_no_arrival_means_no_conditional_error_score():
    f = pl.DataFrame(dict(next_pa=[0,0],target_year=[2022,2023],player_id=[1,2],x_conditional_pa=[100.,200.]))
    assert conditional_score(f,'x')['rmse'] is None
