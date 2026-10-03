import importlib.util
from pathlib import Path
import sys
import polars as pl
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_hitter_games_v38 as s


def test_role_stabilization_and_empty_evidence():
    assert s.role(0,0)==4
    assert s.role(400,100)==4
    assert s.role(40,40)<2


def test_schedule_exposure_role_and_origin_cutoff():
    base=pl.DataFrame(dict(row_id=[0,1],origin_year=[2020,2021],player_id=[1,1],next_pa=[500,0]))
    counts=pl.DataFrame(dict(season=[2020,2021,2022],player_id=[1,1,1],bucket=['MLB','AAA','MLB'],
        plate_appearances=[200,480,800],games_played=[50,100,162]))
    out,cols=s.features(base,counts)
    assert len(cols)==40 and out.select(base.columns).equals(base)
    assert out['games_mlb_0'][0]==135
    assert out['role_mlb_0'][0]==4
    assert out['games_minor_0'][0]==0
    assert out['games_pool_MLB'][1]==108
    assert out['games_minor_0'][1]==100
    changed=counts.with_columns(pl.when(pl.col('season')==2022).then(1).otherwise(pl.col('plate_appearances')).alias('plate_appearances'))
    alternate,_=s.features(base.with_columns(pl.lit(999).alias('next_pa')),changed)
    assert np.array_equal(out.select(cols).to_numpy(),alternate.select(cols).to_numpy())


def test_saved_tree_path_accounting_matches_prediction():
    from sklearn.ensemble import HistGradientBoostingRegressor
    from threadpoolctl import threadpool_limits
    from universal_baseball.histogram_prediction_trace import trace
    x=np.array([[i,i%3] for i in range(100)],dtype=float)
    with threadpool_limits(limits=2):
        m=HistGradientBoostingRegressor(max_iter=4,max_depth=3,min_samples_leaf=5,early_stopping=False).fit(x,x[:,0]*2+x[:,1])
        t=trace(m,x[20],['games_mlb_0','age'])
        assert np.isclose(t['raw_prediction'],m.predict(x[[20]])[0])
        assert np.isclose(t['reference']+sum(v['path_effect'] for v in t['feature_effects']),t['raw_prediction'])
