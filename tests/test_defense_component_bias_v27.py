from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_defense_component_bias_v27 import decompose


def row(**changes):
    r=dict(actual_official_exposure=300,actual_native_opportunities=300,
           history_rate=-2.,rate_unit=1500.,repair_predicted_opportunities=150.,
           repair_history=-.2,history_oracle_runs=-.4,actual_runs=-1.)
    r.update(changes)
    return r


def test_opportunity_and_rate_errors_recompose():
    d=decompose(row())
    assert d['opportunity_error']==pytest.approx(.2)
    assert d['rate_error']==pytest.approx(.6)
    assert d['total_error']==pytest.approx(.8)


def test_unknown_native_denominator_is_not_zero():
    d=decompose(row(actual_native_opportunities=None,history_oracle_runs=None))
    assert d['actual_opportunity_runs'] is None
    assert d['rate_error'] is None
    assert d['opportunity_error'] is None
    assert d['total_error']==pytest.approx(.8)


def test_unknown_measured_runs_are_not_average_skill():
    d=decompose(row(actual_runs=None))
    assert d['actual_opportunity_runs']==pytest.approx(-.4)
    assert d['total_error'] is None and d['rate_error'] is None


def test_certified_no_exposure_has_zero_delivered_opportunity():
    d=decompose(row(actual_official_exposure=0,actual_native_opportunities=None,
                    actual_runs=0.,history_oracle_runs=0.))
    assert d['actual_opportunities']==0 and d['actual_opportunity_runs']==0
    assert d['opportunity_error']==pytest.approx(-.2)
    assert d['rate_error']==0


def test_reject_stale_oracle_and_wrong_unit_products():
    with pytest.raises(AssertionError):decompose(row(history_oracle_runs=-.5))
    with pytest.raises(AssertionError):decompose(row(repair_history=-2.))
