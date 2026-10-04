import importlib.util
from pathlib import Path
import sys
import polars as pl

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('risk_prepare',Path(__file__).resolve().parents[1]/'scripts/prepare_hitter_workload_risk.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_inner_training_excludes_both_groups_and_future_outcomes():
    f=pl.DataFrame(dict(row_id=[1,2,3,4,5],player_id=[10,20,30,40,50],outer_fold=[1,2,2,3,3],
        origin_year=[2016,2014,2016,2017,2014],target_year=[2017,2015,2017,2018,2015],next_pa=[500,50,500,500,0]))
    train,val,j=module.nested_rows(f,0,2016)
    assert j==1 and val['player_id'].to_list()==[10]
    assert train['player_id'].to_list()==[20]
    assert not set(train['player_id'])&set(val['player_id'])


def test_outer_contamination_cannot_pass_nested_selection():
    f=pl.DataFrame(dict(row_id=[1],player_id=[10],outer_fold=[0],origin_year=[2016],target_year=[2017],next_pa=[500]))
    import pytest
    with pytest.raises(AssertionError):
        module.nested_rows(f,0,2016)
