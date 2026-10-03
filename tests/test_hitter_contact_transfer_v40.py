import sys
from pathlib import Path
import polars as pl

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_hitter_contact_transfer_v40 import shape_totals


def test_uppercase_mlb_does_not_become_minor_evidence():
    f=pl.DataFrame(dict(season=[2021,2021,2021],player_id=[1,1,2],level_group=['MLB','aaa','a'],occurrence_count=[100,20,90]))
    q=shape_totals(f).sort('player_id')
    assert q['shape_mlb'].to_list()==[100,0]
    assert q['shape_minor'].to_list()==[20,90]
    assert q['shape_all'].to_list()==[120,90]
