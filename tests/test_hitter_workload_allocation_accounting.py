"""Retrospective accounting must not confuse mean bias with calibration."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import polars as pl
from diagnose_hitter_workload_specialization import account


def test_exact_probability_and_nonarrival_accounting():
    q = pl.DataFrame(dict(next_pa=[100,200,0],player_id=[1,2,3],preseason_p=[.5,.8,.1],x_conditional_pa=[120.,180.,100.]))
    a = account(q,'x')
    assert a['conditional_error']==0
    assert abs(a['active_probability_discount']-96)<1e-10
    assert a['nonarrival_allocation']==10
    assert abs(a['total_forecast_error']+86)<1e-10
    assert a['conditional_pa_for_actual_arrivals']==300
