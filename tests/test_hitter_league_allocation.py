import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_league_allocation import (
    allocate, budget_at_cutoff, calibration, capped_allocation, grouped,
)


def test_group_boundaries_and_no_outcome_membership():
    frame = pl.DataFrame({"stage": ["MLB"]*5, "pa_00": [0, 49, 50, 200, 400]})
    assert grouped(frame)["allocation_group"].to_list() == ["MLB|0", "MLB|0", "MLB|1", "MLB|2", "MLB|3"]


def history():
    return pl.DataFrame({"origin_year": [2016, 2017, 2018, 2019, 2021],
        "player_id": [1]*5, "stage": ["MLB"]*5, "pa_00": [300.]*5,
        "pa_h2": [600., 0., 99999., 99999., 99999.]})


def test_calibration_maturity_and_pandemic_exclusion():
    f = history()
    assert calibration(f, 2017) == []
    assert calibration(f, 2018)[0]["origins"] == [2016]
    assert calibration(f, 2022)[0]["origins"] == [2016, 2017]
    assert calibration(f, 2022)[0]["multiplier"] == 1.
    changed = f.with_columns(pl.when(pl.col("origin_year") >= 2018).then(-999.)
                            .otherwise(pl.col("pa_h2")).alias("pa_h2"))
    assert calibration(f, 2022) == calibration(changed, 2022)


def test_shrinkage_and_clipping():
    f = history().head(1)
    assert calibration(f, 2018)[0]["multiplier"] == pytest.approx(30600/30300)
    assert calibration(f.with_columns(pl.lit(1e9).alias("pa_h2")), 2018)[0]["multiplier"] == 2.


def test_capped_budget_and_explicit_slack():
    np.testing.assert_allclose(capped_allocation([100, 100], [1, .1], 500), [420, 80])
    np.testing.assert_allclose(capped_allocation([1, 1], [.1, .1], 1000), [80, 80])
    np.testing.assert_allclose(capped_allocation([0, 0], [1, 1], 100), [0, 0])
    np.testing.assert_allclose(capped_allocation([1, 2], [1, 1], 0), [0, 0])
    for weights, p, budget in (([-1], [1], 10), ([1], [1.1], 10), ([1], [1], -1), ([np.nan], [1], 1)):
        with pytest.raises(ValueError):
            capped_allocation(weights, p, budget)


def test_allocate_does_not_read_test_outcomes():
    f = history().tail(1).with_columns(pl.lit(.8).alias("old_p"))
    before = allocate(f, calibration(history(), 2021), 400)
    after = allocate(f.with_columns(pl.lit(-1e9).alias("pa_h2")), calibration(history(), 2021), 400)
    np.testing.assert_array_equal(before["candidate_pa"], after["candidate_pa"])
    assert before["old_p"].to_list() == [.8]


def test_missing_group_falls_back_and_preserves_all_players():
    f = history().tail(1).with_columns(pl.lit(.8).alias("old_p"))
    out = allocate(f, [], 400)
    assert out.height == f.height
    assert out["allocation_multiplier"].to_list() == [1.]
    np.testing.assert_allclose(out["candidate_pa"], out["uniform_pa"])


def test_allocation_invariant_to_order_and_weight_units():
    weights, p = np.array([20., 5., 300.]), np.array([.1, .05, .9])
    a = capped_allocation(weights, p, 600)
    np.testing.assert_allclose(a, capped_allocation(weights*100, p, 600))
    np.testing.assert_allclose(a, capped_allocation(weights[::-1], p[::-1], 600)[::-1])
    assert a.sum() == pytest.approx(600)


def test_budget_cannot_see_future_or_future_cohort():
    panel = pl.DataFrame({"origin_year": [2012, 2013, 2014, 2025], "player_id": [1]*4})
    targets = pl.DataFrame({"season": [2014, 2014, 2015, 2015, 2016, 2016, 2025],
                           "player_id": [1, 2, 1, 2, 1, 2, 2], "mlb_pa": [900., 100., 900., 100., 900., 100., 1e9]})
    schedules = pl.DataFrame({"season": [2014, 2015, 2016, 2025], "completed_games": [2430]*4, "teams": [30]*4})
    result = budget_at_cutoff(panel, targets, schedules, 2016)
    assert result["pool"] == 1000
    assert result["reserve_pa"] == 100
    assert result["named_budget"] == 900
    assert [r["origin"] for r in result["reserve_support"]] == [2012, 2013, 2014]
    assert result == budget_at_cutoff(panel.filter(pl.col("origin_year") < 2025),
        targets.filter(pl.col("season") < 2025), schedules.filter(pl.col("season") < 2025), 2016)
    with pytest.raises(ValueError, match="Protected"):
        budget_at_cutoff(panel, targets, schedules, 2026)
