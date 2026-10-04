"""The supplementary uncertainty uses candidate-minus-benchmark loss units."""
from pathlib import Path
import sys
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from review_hitter_team_record_v75 import crossed


def test_crossed_loss_direction_and_equal_forecast():
    f=pl.DataFrame([dict(player_id=pid, origin_year=year, target_year=year+1,
                        context_parent_id=team, org_record_known=1,
                        a_pa=1., b_pa=0., next_pa=0.)
                    for year in [2016,2017] for pid,team in [(1,108),(2,108),(3,144),(4,144)]])
    r=crossed(f,'a','b','pa')
    assert r['difference']==1. and r['lower']==1. and r['upper']==1.
    same=crossed(f,'a','a','pa')
    assert same['difference']==0. and same['lower']==0. and same['upper']==0.
