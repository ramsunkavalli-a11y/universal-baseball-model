import sys
from pathlib import Path

import polars as pl

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_defense_transition_v10 import share_score


def test_list_valued_position_matrix_scores_correctly():
    q=pl.DataFrame({'transition_prediction_shares':[[0.,0.,0.,0.,0.,.5,.5,0.],[0.,0.,0.,0.,0.,0.,0.,1.]],
        **{f'actual_{p}':[100 if p==8 else 0,100 if p==9 else 0] for p in range(2,10)}})
    s=share_score(q,'transition')
    assert s['rows']==2 and s['mean_cell_squared_share_error']==.03125
    assert share_score(q.head(0),'transition') is None
