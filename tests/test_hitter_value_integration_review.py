from pathlib import Path
import sys
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from score_hitter_value_integration_v76 import peers


def test_peer_selection_uses_origin_exposure_not_future_success():
    rows=[]
    for pid in range(6):
        rows.append(dict(row_id=pid,player_id=pid,origin_year=2023,stage='Upper minors',
            prior_debut=0,age=22.,pa_0=0.,minor_pa_0=500.,AA_0_pa=300. if pid<2 else 50.,
            AAA_0_pa=0.,scout_rank_score_0=.8,translated_K=.1,translated_UBB=.2,
            translated_HR=.3,pooled_mlb_quality=0.,next_pa=pid*100.,next_value=float(pid)))
    source=pl.DataFrame(rows)
    selected=peers(source,rows[0])['player_id'].to_list()
    assert selected[0]==1
    changed=source.with_columns((10000-pl.col('next_pa')).alias('next_pa'),(-pl.col('next_value')).alias('next_value'))
    assert peers(changed,rows[0])['player_id'].to_list()==selected
