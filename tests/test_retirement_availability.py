from datetime import date
from universal_baseball.retirement_availability import events,state


def capture(rows):return [(2022,'fixture',dict(transactions=rows))]
def raw(i,code,day,text='',effective=None):return dict(id=i,person=dict(id=1),typeCode=code,date=day,effectiveDate=effective or day,description=text)


def test_retirement_is_dated_and_reversible_not_il_or_release():
    rows=[raw(1,'RET','2022-10-01'),raw(2,'REL','2022-11-01'),raw(3,'ACT','2022-11-02','activated from injured list'),raw(4,'SFA','2023-02-01')]
    r=events(capture(rows),date(2023,12,31))
    assert state(r,date(2022,9,30))['reported_retired'] is False
    assert state(r,date(2022,12,31))['reported_retired'] is True
    s=state(r,date(2023,12,31));assert not s['reported_retired'] and s['return_evidence']['transaction_id']==4


def test_late_backdated_return_cannot_change_earlier_forecast():
    rows=[raw(1,'RET','2022-10-01'),raw(2,'SFA','2023-02-01',effective='2022-12-01')]
    r=events(capture(rows),date(2022,12,31));assert len(r)==1
    assert state(r,date(2022,12,31))['reported_retired']


def test_retirement_list_activation_clears_but_unrelated_activation_does_not():
    r=events(capture([raw(1,'RET','2022-10-01'),raw(2,'ACT','2022-11-01','activated from retired list')]),date(2022,12,31))
    assert not state(r,date(2022,12,31))['reported_retired']
