import importlib.util
from pathlib import Path
import polars as pl
import pytest

path=Path(__file__).resolve().parents[1]/'scripts/resume_hitter_evidence_representation.py'
import sys
sys.path.insert(0,str(path.parent))
spec=importlib.util.spec_from_file_location('fit_recovery',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def frame():
    q=pl.DataFrame({'source_addition':[False,True],'current_rate':[1.,None],'current_pa':[100.,None]})
    for arm in ['repaired_domestic','repaired_overseas']:
        for s in ['raw_p','p','raw_conditional_pa','conditional_pa','pa','rate','value']:
            q=q.with_columns(pl.lit(1.).alias(arm+'_'+s))
        for s in ['workload_only_value','talent_only_value']:
            q=q.with_columns(pl.Series(arm+'_'+s,[1.,None]))
    return q


def test_missing_baseline_is_allowed_not_zero():
    module.valid_outputs(frame())


def test_new_forecast_must_be_finite_even_for_addition():
    q=frame().with_columns(pl.Series('repaired_overseas_rate',[1.,float('nan')]))
    with pytest.raises(AssertionError):module.valid_outputs(q)


def test_mechanical_comparison_cannot_invent_zero_baseline():
    q=frame().with_columns(pl.lit(0.).alias('repaired_domestic_workload_only_value'))
    with pytest.raises(AssertionError):module.valid_outputs(q)
