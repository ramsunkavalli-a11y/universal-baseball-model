import pytest
from universal_baseball.hitter_numeric_history import BUCKETS
from universal_baseball.prospect_exposure_diagnostic import exposure


def row(**values):
    return {**{f'{b}_0_pa': 0 for b in BUCKETS}, 'scout_listed_0': 0,
            'scout_rank_score_0': 0., **values}


def test_future_outcome_cannot_change_profile():
    a = row(A_0_pa=400, AA_0_pa=24, scout_listed_0=1, scout_rank_score_0=.99)
    assert exposure({**a, 'next_pa': 0}) == exposure({**a, 'next_pa': 700})


@pytest.mark.parametrize('pa,band', [(29,'1to29'),(30,'30to199'),(199,'30to199'),(200,'200plus')])
def test_descriptive_boundaries_fixed(pa,band):
    assert exposure(row(AA_0_pa=pa))['highest_exposure_band'] == band


def test_invalid_origin_count_not_treated_as_missing():
    with pytest.raises(ValueError):
        exposure(row(AA_0_pa=-1))
