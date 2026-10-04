"""Earlier inputs must not turn future arrival or missing coverage into evidence."""
from datetime import date
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_hitter_extended_training import bucket,debut_inputs
from score_hitter_extended_training import probability
import numpy as np
import polars as pl


def test_future_debut_does_not_change_origin_inputs():
    assert debut_inputs(2008,None,False)==debut_inputs(2008,date(2012,4,1),False)==(-1,0,0)
    assert debut_inputs(2008,None,True)==(-1,1,1)
    assert debut_inputs(2008,date(2001,4,1),True)==(7,1,0)


def test_dsl_and_mexico_remain_separate():
    assert bucket({'sport_id':16,'league_id':130})=='DSL'
    assert bucket({'sport_id':11,'league_id':125})=='MEX'
    assert bucket({'sport_id':15,'league_id':127})=='Aminus'


def test_binary_scores_use_all_players_including_nonarrivals():
    f=pl.DataFrame({'target_year':[2025,2025],'next_pa':[400,0],'test_p':[.75,.25]})
    result=probability(f,'test')
    assert result['brier']==.0625
    assert np.isclose(result['log_loss'],-np.log(.75))
    assert result['expected_active']==result['actual_active']==1
