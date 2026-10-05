from pathlib import Path
import sys
import polars as pl

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_overseas_opportunity_inventory_v2 import saved_digest
from audit_overseas_opportunity_inventory import totals
from universal_baseball.storage import sha256_file


def test_saved_manifest_string_path_is_supported():
    p=Path(__file__)
    assert saved_digest(str(p))==saved_digest(p)==sha256_file(p)


def test_equal_totals_do_not_hide_bad_allocation():
    q=pl.DataFrame(dict(origin_year=[2021,2021],source_addition=[False,False],next_pa=[600,0],current_p=[.5,.5],current_pa=[300.,300.]))
    s=totals(q,'current')
    assert s['expected_PA']==600
    assert s['PA_RMSE']==300
    assert s['PA_allocated_to_nonarrivals']==300


def test_added_missing_current_forecast_does_not_become_zero():
    q=pl.DataFrame(dict(source_addition=[True]))
    assert totals(q,'current')==dict(missing_current_forecasts=True)
