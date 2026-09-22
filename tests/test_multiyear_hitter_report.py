import sys
from pathlib import Path
import numpy as np
import polars as pl
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from report_multiyear_hitter_v1 import distribution_score, equal_origin, paired_cluster_interval
from evaluate_multiyear_hitter_v1 import baseline


def test_empirical_crps_matches_direct_definition():
    residuals = np.array([-2., 0., 1., 4.])
    obs = np.array([-3., .5, 6.])
    expected = np.mean(np.abs(residuals[:,None]-obs)) - .5*np.mean(np.abs(residuals[:,None]-residuals))
    assert distribution_score(residuals,obs)["crps"] == pytest.approx(expected)


def test_equal_origin_weighting_does_not_weight_large_cohort_more():
    f = pl.DataFrame({"origin_year":[2016,2016,2022],"war_c3":[0.,0.,0.],"prediction":[1.,1.,3.]})
    assert equal_origin(f,"prediction")["mse"] == pytest.approx(5.)


def test_paired_bootstrap_identical_predictions_are_exact_zero():
    f = pl.DataFrame({"origin_year":[2016,2016,2022,2022],"player_id":[1,2,1,2],"war_c3":[0.,1.,2.,3.],"selected_c3":[1.,1.,1.,1.],"B0_c3":[1.,1.,1.,1.]})
    assert paired_cluster_interval(f,draws=20) == [0.,0.]


def test_baseline_cannot_see_unmatured_future_labels():
    frame = pl.DataFrame({"origin_year":[2009,2009,2013,2013,2025], "player_id":[1,2,3,4,5],
        "x":[1.,2.,3.,4.,5.], "war_h1":[1.,2.,3.,4.,None],"war_h2":[2.,3.,4.,5.,None],"war_h3":[3.,4.,5.,6.,None]})
    altered = frame.with_columns(*[pl.when(pl.col("origin_year")>=2013).then(1000.).otherwise(pl.col(c)).alias(c) for c in ("war_h1","war_h2","war_h3")])
    a = baseline(frame,{"base_features":["x"]},2013,True)
    b = baseline(altered,{"base_features":["x"]},2013,True)
    np.testing.assert_equal(a,b)
