import numpy as np
import polars as pl
import pytest

from universal_baseball.finite_return_baseline import (
    FEATURES,
    frame,
    matrix,
    readiness,
    transfer_allowed,
    unrestricted,
)


def report(**kw):
    return dict(
        player_id=1,
        target_year=2023,
        known_date="2022-10-25",
        surgery_reported=True,
        expected_ready_before_season=True,
        source_url="https://example.org",
        **kw,
    )


def row():
    r = dict.fromkeys(FEATURES, 0.0)
    r.update(
        player_id=1,
        target_year=2023,
        ctx_information_date="2023-01-26",
        age=23.0,
        work_0=0.0,
        work_1=546.0,
        work_2=695.0,
        career_mlb_observed_pa=1175,
        last_MLB_lag=1 / 3,
        last_MLB_known=1.0,
        last_MLB_work=546 / 600,
        prior_debut=1,
        medical_recent_surgery=0.0,
        obs_status_finite_nonmedical=1.0,
        obs_status_unresolved_nonmedical=0.0,
        status_hard_unavailable=0.0,
        status_retired=0.0,
        status_major_link=1.0,
    )
    return r


def test_known_report_retains_old_inputs_and_corrects_unrecorded_surgery():
    original = pl.DataFrame([row()]).drop(
        "role_age",
        "role_age_squared",
        "role_career",
        "role_active_mean",
        "role_gap",
        "role_surgery",
    )
    f = frame(original, [report()])
    assert f.select(original.columns).equals(original)
    assert f["role_active_mean"][0] == (546 + 695) / 1200
    assert f["role_gap"][0] == 1 and f["role_surgery"][0] == 1
    assert f["anticipated_preseason_readiness"][0]


@pytest.mark.parametrize(
    "change", [dict(player_id=2), dict(target_year=2024), dict(known_date="2023-02-01")]
)
def test_medical_report_must_match_cutoff_and_player(change):
    r = report()
    r.update(change)
    assert readiness([r], 1, 2023, "2023-01-26") is None


def test_conflicting_reports_rejected():
    r = report()
    r["expected_ready_before_season"] = False
    with pytest.raises(ValueError):
        readiness([r, report()], 1, 2023, "2023-01-26")


@pytest.mark.parametrize(
    "field", ["status_employment_conflict", "status_retired", "status_hard_unavailable"]
)
def test_incompatible_status_blocks_transfer(field):
    r = frame(pl.DataFrame([row()]), [report()]).row(0, named=True)
    r[field] = 1.0
    assert not transfer_allowed(r, {"state": "reported_finite_season_budget"})


@pytest.mark.parametrize(
    "state",
    [
        "parallel_restriction_requires_scenarios",
        "finite_budget_unknown",
        "hard_unavailable",
        "no_current_observed_restriction",
    ],
)
def test_only_explicit_finite_budget_allows_transfer(state):
    r = frame(pl.DataFrame([row()]), [report()]).row(0, named=True)
    assert not transfer_allowed(r, {"state": state})


def test_reference_and_scenario_only_differ_in_gap_not_role_or_health():
    f = frame(pl.DataFrame([row()]), [report()])
    ordinary, ready = matrix(f), matrix(f, remove_explained_gap=True)
    changed = np.flatnonzero(ordinary[0] != ready[0])
    assert changed.tolist() == [FEATURES.index("role_gap")]
    assert ready[0, FEATURES.index("role_surgery")] == 1
    assert ordinary[0, FEATURES.index("last_MLB_work")] == 546 / 600
    assert unrestricted(f).height == 0


def test_nonarrival_labels_do_not_change_features_or_gate():
    a = frame(pl.DataFrame([row() | {"next_pa": 635}]), [report()])
    b = frame(pl.DataFrame([row() | {"next_pa": 0}]), [report()])
    assert np.array_equal(matrix(a), matrix(b))
    assert transfer_allowed(
        a.row(0, named=True), {"state": "reported_finite_season_budget"}
    )


def test_missing_report_or_job_cannot_clear_medical_gap():
    for reports, link in [([], 1.0), ([report()], 0.0)]:
        f = frame(pl.DataFrame([row() | {"status_major_link": link}]), reports)
        assert not transfer_allowed(
            f.row(0, named=True), {"state": "reported_finite_season_budget"}
        )
