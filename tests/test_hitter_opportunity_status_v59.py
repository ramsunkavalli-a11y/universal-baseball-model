"""Dated context semantics, not a certificate of predictive quality."""
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
import evaluate_hitter_opportunity_status_v59 as e


def row(year=2022,pa0=0,pa1=500):
    return dict(row_id=0,player_id=1,origin_year=year,pa_0=pa0,pa_1=pa1)


def record(kind,known='2022-07-01',**extras):
    return dict(transaction_id=1,player_id=1,available_date=date.fromisoformat(known),
        event_date=date.fromisoformat(known),kind=kind,description=kind,
        il_kind=None,category='unspecified',surgery=False,duration_years=None,**extras)


def test_nonmedical_is_not_ordinary_departure_or_permanent_zero():
    x,h=e.context(row(),[record('suspended_unspecified')],{})
    assert x['status_nonmedical_unresolved']==1
    assert x['status_ordinary_departure']==0
    assert not h['hard_unavailable']


def test_early_missing_capture_and_medical_scope_are_explicit():
    x,h=e.context(row(year=2014),[],{})
    assert x['status_capture_scope']==0 and x['status_medical_scope']==0
    assert h['il_status']=='unknown_scope' and h['il_days730'] is None


def test_minor_scope_is_not_medically_healthy():
    x,h=e.context(row(pa0=0,pa1=0),[],{})
    assert x['status_capture_scope']==1 and x['status_medical_scope']==0
    assert h['il_status']=='unknown_scope'


def test_future_backdated_status_is_invisible():
    old=record('org_acquisition')
    future={**record('deceased','2023-01-01'),'event_date':date(2022,1,1),'transaction_id':2}
    assert e.context(row(),[old],{})==e.context(row(),[old,future],{})


def test_acquisition_is_context_not_roster_or_health_certification():
    x,h=e.context(row(),[record('org_acquisition')],{})
    assert x['status_acquired']==1
    assert not h['medical_recovery_certified'] and not h['hard_unavailable']
