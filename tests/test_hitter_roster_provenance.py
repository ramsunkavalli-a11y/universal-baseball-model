"""Dated roster-event diagnostics cannot certify unknown reserve membership."""
import importlib.util
from pathlib import Path
import sys

SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('roster_inventory',SCRIPTS/'audit_hitter_roster_provenance.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def event(day,description,team=113,**more):
    return dict(id=1,date=day,toTeam={'id':team},description=description,**more)


def test_explicit_addition_and_later_removal():
    positive=event('2023-05-15','Cincinnati Reds selected the contract of SS Matt McLain.')
    negative=event('2023-11-02','SS Matt McLain elected free agency.')
    assert module.event_at_cutoff([positive],2023,{113})['sign']=='positive'
    assert module.event_at_cutoff([positive,negative],2023,{113})['sign']=='negative'


def test_future_and_conflicting_effective_dates():
    positive=event('2023-05-15','Cincinnati Reds selected the contract of SS Matt McLain.')
    future=event('2024-01-01','Cincinnati Reds released SS Matt McLain.')
    original=module.event_at_cutoff([positive],2023,{113})
    assert module.event_at_cutoff([positive,future],2023,{113})==original
    delayed=event('2023-12-15','Cincinnati Reds selected the contract of SS Matt McLain.',effectiveDate='2024-05-15')
    result=module.event_at_cutoff([delayed],2023,{113})
    assert result['sign']=='unknown' and result['date_conflicts']==[delayed]


def test_ambiguous_activation_assignment_and_minor_release():
    assert module.classify(event('2023-11-06','Los Angeles Dodgers activated SS Gavin Lux from the 60-day injured list.'),{113})=='positive'
    assert module.classify(event('2023-11-06','Los Angeles Dodgers activated SS Gavin Lux.'),{113}) is None
    assert module.classify(event('2021-07-12','2B Ozzie Albies assigned to National League All-Stars.',160),{113}) is None
    assert module.classify(event('2023-11-06','Glendale Desert Dogs released SS Matt McLain.',160),{113}) is None


def test_same_date_opposite_events_remain_conflicting():
    positive=event('2023-11-06','Cincinnati Reds selected the contract of SS Matt McLain.')
    negative=event('2023-11-06','Cincinnati Reds released SS Matt McLain.')
    assert module.event_at_cutoff([positive,negative],2023,{113})['sign']=='conflicting'
