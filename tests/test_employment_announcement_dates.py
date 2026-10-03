import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_hitter_employment_v70b import event,state


def row(day,effective,kind='Signed as Free Agent'):
    return dict(id=1,person={'id':9},date=day,effectiveDate=effective,resolutionDate=day,
        typeDesc=kind,typeCode='SFA',description='Team signed free agent Player.')


def test_signing_not_delayed_to_later_option_date():
    r=event(row('2018-12-15','2019-05-15'))
    assert r['available_date']=='2018-12-15'
    assert state([r],2018)['recorded_open_fa']==0


def test_future_announcement_not_backdated():
    r=event(row('2019-01-03','2018-12-30'))
    assert state([r],2018)['recorded_open_fa']==-1


def test_old_fa_is_not_indefinitely_confirmed():
    r=event(row('2018-11-02','2018-11-02','Declared Free Agency'))
    assert state([r],2018)['recorded_open_fa']==1
    assert state([r],2019)['recorded_open_fa']==-1


def test_same_day_contradiction_unknown():
    a=event(row('2018-11-02','2018-11-02','Declared Free Agency'))
    b=event(row('2018-11-02','2018-11-02'))
    assert state([a,b],2018)['recorded_open_fa']==-1
