import numpy as np
import pytest
from universal_baseball.hitter_numeric_history import BUCKETS
from universal_baseball.prospect_exposure_diagnostic import exposure, pa_accounting


def row(**values):
    return {**{f'{b}_0_pa': 0 for b in BUCKETS}, 'scout_listed_0': 0,
            'scout_rank_score_0': 0., **values}


def test_brief_promotion_keeps_primary_experience():
    r = exposure(row(A_0_pa=400, AA_0_pa=24))
    assert r['primary_level'] == 'A' and r['highest_level'] == 'AA'
    assert r['promotion_mismatch'] and r['highest_exposure_band'] == '1to29'
    assert r['primary_share'] == 400/424


def test_ties_higher_and_mexico_separate():
    r = exposure(row(A_0_pa=100, Aplus_0_pa=100, MEX_0_pa=500))
    assert r['primary_level'] == 'Aplus' and r['affiliated_pa'] == 200
    assert not r['promotion_mismatch']


def test_rookie_buckets_combined_not_inferred_promotion():
    r = exposure(row(DSL_0_pa=50, RK121_0_pa=100))
    assert r['primary_level'] == r['highest_level'] == 'ROOKIE'
    assert r['affiliated_pa'] == 150


def test_no_affiliated_exposure_and_unknown_rank_kept():
    r = exposure(row(MEX_0_pa=300, scout_listed_0=-1))
    assert r['highest_exposure_band'] == 'none' and r['rank_band'] == 'unknown'


def test_accounting_preserves_nonarrivals():
    r = pa_accounting([.8,.2], [300,100], [400,0])
    assert r['conditional_error'] == -100
    assert r['active_probability_discount'] == pytest.approx(60)
    assert r['nonarrival_allocation'] == 20
    assert r['total_forecast_error'] == -140


def test_no_arrivals_still_valid():
    r = pa_accounting([.1], [100], [0])
    assert r['actual_arrivals'] == 0 and r['total_forecast_error'] == 10


@pytest.mark.parametrize('p,c,y', [([1.1],[1],[0]), ([.2],[np.nan],[0]),
                                  ([.2],[1],[-1]), ([],[],[])])
def test_invalid_pairs_rejected(p,c,y):
    with pytest.raises(ValueError):
        pa_accounting(p,c,y)
