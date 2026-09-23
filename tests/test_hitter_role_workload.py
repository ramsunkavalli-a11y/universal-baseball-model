import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_role_workload import (
    mature_mask, projection_vintage_audit, role_features, state_mean, workload_states,
)


def test_state_boundaries_and_probability_mean():
    np.testing.assert_array_equal(workload_states([0, 1, 199, 200, 449, 450, 700]), [0, 1, 1, 2, 2, 3, 3])
    assert state_mean([[.5, .1, .2, .2]], [[0, 100, 300, 600]])[0] == 190
    with pytest.raises(ValueError):
        state_mean([[0, 0, 0, 1]], [[0, 100, 300, 300]])
    with pytest.raises(ValueError):
        state_mean([[0, 0, 0, .5]], [[0, 100, 300, 600]])


def test_training_maturity_and_pandemic():
    p = pl.DataFrame({"origin_year": [2016, 2018, 2019, 2021, 2022, 2023], "pa_h2": [1]*6})
    np.testing.assert_array_equal(mature_mask(p, 2023, 2), [True, False, False, True, False, False])


def test_role_dates_dh_and_pitcher_exclusion():
    p = pl.DataFrame({"origin_year": [2021], "player_id": [1], "mlb_pa_lag0": [400], "mlb_pa_lag1": [200]})
    f = pl.DataFrame({"season": [2020, 2021, 2021, 2021, 2022], "player_id": [1]*5,
        "team_id": [1]*5, "position_abbreviation": ["DH", "DH", "C", "P", "DH"],
        "games_started": [30, 70, 30, 20, 150]})
    a, _ = role_features(p, f, {2020: .37, 2021: 1., 2022: 1.})
    assert a["role_starts_0"][0] == 100
    assert a["role_DH_0"][0] == .7
    assert a["role_C_0"][0] == .3
    assert a["role_starts_1"][0] == 30/.37
    with pytest.raises(ValueError, match="Duplicate"):
        role_features(p, pl.concat([f, f.head(1)]), {2021: 1.})


def test_no_mlb_usage_is_not_missing_source():
    p = pl.DataFrame({"origin_year": [2021], "player_id": [2], "mlb_pa_lag0": [0], "mlb_pa_lag1": [0]})
    f = pl.DataFrame({"season": [2021], "player_id": [1], "team_id": [1], "position_abbreviation": ["C"], "games_started": [50]})
    a, _ = role_features(p, f, {2021: 1.})
    assert a["role_history_available_0"][0] == 1
    assert a["role_starts_0"][0] == 0
    assert a["role_history_available_1"][0] == 0


def test_projection_vintage_invariance_veto_not_automatic_certification():
    frame = pl.DataFrame({"player_id": list(range(101)), "projected_pa": list(range(101)),
                          "projected_ip": [None]*101})
    report = projection_vintage_audit({2023: frame, 2025: frame})
    assert report["status"] == "quarantined_cross_year_invariance"
    assert not report["historical_workload_eligible"]
    changed = frame.with_columns((pl.col("projected_pa")+2).alias("projected_pa"))
    report = projection_vintage_audit({2023: frame, 2025: changed})
    assert report["status"] == "vintage_still_unverified"
    assert not report["historical_workload_eligible"]
