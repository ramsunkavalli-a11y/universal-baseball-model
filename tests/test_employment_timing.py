import pytest
from universal_baseball.employment_timing import timing,complete_frame
from test_employment_comparison import sample,indicators
import polars as pl


def test_assignment_freshness_is_replaced_by_minor_signing():
    old=timing('2022-03-18','2022-03-17');new=timing('2022-03-18','2021-12-29')
    f=sample().with_columns([pl.lit(v).alias(n) for n,v in old.items()])
    dates=pl.DataFrame([dict(origin_year=2021,player_id=553988,information_date='2022-03-18',
        **{'old_'+n:v for n,v in old.items()},**{'new_'+n:v for n,v in new.items()})])
    r=complete_frame(f,indicators(),dates)
    assert r['employment_evidence_age_years'][0]==79/365
    assert r['signed_first_team_work'][0]==0 and r['next_pa'][0]==17


def test_no_date_is_not_a_known_recent_event():
    assert timing('2022-03-18',None)=={'employment_evidence_unknown':1.,'employment_evidence_age_years':0.}


def test_future_dates_and_existing_units_preserved():
    with pytest.raises(ValueError,match='Future'):timing('2022-03-18','2022-03-19')
    assert timing('2022-03-18','2000-01-01')['employment_evidence_age_years']==10.
