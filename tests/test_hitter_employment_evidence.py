from universal_baseball.hitter_employment_evidence import features


def test_states_and_missingness():
    assert features(2023,{'latest_employment_date':'2023-11-02','recorded_open_fa':1})==dict(employment_capture_scope=1,employment_year_known=1,employment_year_fa=1)
    assert features(2023,{'latest_employment_date':'2023-12-02','recorded_open_fa':0})==dict(employment_capture_scope=1,employment_year_known=1,employment_year_fa=0)
    assert features(2023,{'latest_employment_date':None,'recorded_open_fa':-1})==dict(employment_capture_scope=1,employment_year_known=0,employment_year_fa=0)


def test_older_and_conflicting_not_deals():
    assert features(2023,{'latest_employment_date':'2022-11-02','recorded_open_fa':0})['employment_year_known']==0
    assert features(2023,{'latest_employment_date':'2023-11-02','recorded_open_fa':1},True)['employment_year_known']==0
    assert features(2014,{'latest_employment_date':'2014-11-02','recorded_open_fa':1})==dict(employment_capture_scope=0,employment_year_known=0,employment_year_fa=0)
