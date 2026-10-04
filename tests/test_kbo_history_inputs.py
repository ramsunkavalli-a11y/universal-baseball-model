import pytest

from universal_baseball.kbo_history import FIELDS1,FIELDS2
from universal_baseball.kbo_history_inputs import history_at


def row(year,**changes):
    r={k:0 for k in FIELDS1+FIELDS2}
    r.update(kbo_id='0001',season=year,pa=10,ab=8,hits=2,hr=1,tb=5,so=2,bb=2,ibb=1)
    r.update(changes)
    return r


def test_partial_coverage_cannot_be_a_complete_feature():
    h=history_at([row(2024)],'0001',2024,[2024])
    assert h['observed_recent_counts']['pa']==10
    assert h['recent_counts'] is None and h['k_rate'] is None
    assert h['recent_missing_coverage']==[2022,2023]


def test_complete_absence_is_zero_first_team_exposure_not_zero_talent():
    h=history_at([],'0001',2024,[2022,2023,2024])
    assert h['recent_counts']['pa']==0 and h['k_rate'] is None
    assert h['certified_recent_first_team_zero_pa_seasons']==[2022,2023,2024]
    assert not h['minor_Futures_history_known'] and not h['MLB_translation_fitted']


def test_future_rows_and_future_coverage_do_not_change_history():
    rows=[row(2022),row(2023),row(2024)]
    before=history_at(rows,'0001',2024,[2022,2023,2024])
    assert before==history_at(rows+[row(2099,pa=9999,hr=999)],'0001',2024,[2022,2023,2024,2099])
    assert before['recent_counts']['pa']==30
    assert before['ubb_rate']==.1 and before['k_rate']==.2


def test_past_history_and_years_are_not_full_professional_experience():
    h=history_at([row(2005),row(2024)],'0001',2024,[2005,2022,2023,2024])
    assert h['observed_history_pa']==20 and h['recent_counts']['pa']==10
    assert h['experience_left_truncated']


def test_duplicate_or_unqualified_year_cannot_be_counted():
    with pytest.raises(ValueError,match='Duplicate'):
        history_at([row(2024),row(2024)],'0001',2024,[2024])
    with pytest.raises(ValueError,match='unqualified'):
        history_at([row(2024)],'0001',2024,[2022,2023])


def test_no_unverified_id_guessing():
    with pytest.raises(ValueError):
        history_at([],None,2024,[2024])
