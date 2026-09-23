from datetime import date

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_three_year_opportunity import (
    attach_cohorts, monotone_arrival, reconciliation_beta, training_rows, value_versions,
)


def test_horizon_maturity_and_disjoint_identity():
    p = pl.DataFrame({"origin_year": [2016, 2017, 2019, 2021, 2022], "player_id": [1, 2, 3, 4, 1], "pa_h3": [10]*5})
    assert training_rows(p, 2022, 3)["origin_year"].to_list() == [2016]
    assert training_rows(p, 2022, 3, [1]).is_empty()


def test_future_debut_does_not_select_successful_prospects():
    p = pl.DataFrame({"origin_year": [2021]*4, "player_id": [1, 2, 3, 4],
                      "stage": ["Upper minors", "Lower minors", "Upper minors", "Current MLB"]})
    d = pl.DataFrame({"player_id": [1, 3, 4], "mlb_debut_date": [date(2023, 1, 1), date(2018, 1, 1), date(2021, 1, 1)]})
    t = pl.DataFrame({"season": [2021], "player_id": [4], "mlb_pa": [100]})
    f = attach_cohorts(p, d, t)
    assert f["prospect"].to_list() == [True, True, False, False]
    assert f["minor_returner"].to_list() == [False, False, True, False]
    assert f["recent_debut"].to_list() == [False, False, False, True]
    assert "debut_year" not in f.columns
    with pytest.raises(ValueError, match="contradicts"):
        attach_cohorts(p, d, pl.DataFrame({"season": [2021], "player_id": [1], "mlb_pa": [10]}))


def test_arrival_probability_is_monotone_not_sum():
    np.testing.assert_allclose(monotone_arrival([[.2, .1, .4], [.5, .6, .7]]), [[.2, .2, .4], [.5, .6, .7]])
    with pytest.raises(ValueError):
        monotone_arrival([[.2, .3, 1.1]])


def test_reconciliation_requires_mature_oos_support():
    f = pl.DataFrame({"origin_year": [2016]*200+[2017]*200+[2021]*200,
        "pandemic": [False]*600, "candidate": [400.]*600, "ensemble": [400.]*600, "accepted": [200.]*600,
        "performance_anchor": [3.]*600, "actual_value": [2.]*400+[999.]*200, "delivered": [1.]*600})
    early = reconciliation_beta(f, 2018, 2)
    assert early["fallback"] and early["beta"] == 0
    later = reconciliation_beta(f, 2021, 2)
    assert later["origins"] == [2016, 2017] and later["latest_target"] == 2019
    assert later["beta"] == .8
    v = value_versions(f.head(1), later["beta"])
    assert v["replacement"][0] == 2.
    assert v["reconciled"][0] == 1.8
    assert v["product_control"][0] == 1.
