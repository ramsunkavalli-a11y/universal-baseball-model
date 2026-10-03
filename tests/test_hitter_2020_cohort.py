import sys
from pathlib import Path
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from materialize_hitter_2020_cohort import eligible_ids


def test_eligibility_carries_canceled_minors_and_exits():
    prior=pl.DataFrame({'player_id':[10,11]})
    current=pl.DataFrame({'player_id':[12,13],'position':['6','1']})
    roster=pl.DataFrame({'player_id':[14,15,16],'position':['3','1','X']})
    old=pl.DataFrame({'player_id':[17]})
    assert eligible_ids(prior,current,roster,old)==[10,11,12,14,17]


def test_mutable_person_fields_do_not_select_hitters():
    prior=pl.DataFrame({'player_id':[]},schema={'player_id':pl.Int64})
    current=pl.DataFrame({'player_id':[],'position':[]},schema={'player_id':pl.Int64,'position':pl.String})
    roster=pl.DataFrame({'player_id':[10,11],'position':['1','6'],
        'current_primary_position':['6','1'],'future_pa':[600,0]})
    assert eligible_ids(prior,current,roster,prior)==[11]
    assert eligible_ids(prior,current,roster.with_columns(pl.lit(999).alias('future_pa')),prior)==[11]
