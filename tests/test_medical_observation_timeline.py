from copy import deepcopy
from datetime import date

import pytest

from universal_baseball.medical_observation_timeline import rebuild, union_days


def record(when, kind="placement", *, tid=1, **kw):
    return dict(
        player_id=1,
        transaction_id=tid,
        event_date=date.fromisoformat(when),
        available_date=date.fromisoformat(when),
        kind="other",
        il_kind=kind,
        category="upper",
        surgery=False,
        **kw,
    )


def appearance(when):
    return dict(player_id=1, game_date=when, game_pk=int(when.replace("-", "")))


def run(records, apps=(), windows=(), cutoff="2017-01-26", origin=2016):
    return rebuild(1, records, apps, windows, cutoff, origin)


def test_return_splits_later_injury_instead_of_truncating_old_merged_spell():
    rs = [record("2016-04-01"), record("2016-08-01", tid=2)]
    r = run(rs, [appearance("2016-05-01")])
    assert len(r["spells"]) == 2
    assert r["spells"][0]["observation_end_upper"] == date(2016, 5, 1)
    assert r["spells"][1]["closure_kind"] == "pending_at_cutoff"
    assert r["pending_observation"]
    assert not r["medical_recovery_certified"] and r["true_injury_days"] is None


def test_scope_exit_censors_not_recovery_and_does_not_censor_finished_episode():
    scope = record("2016-08-01", None, tid=2)
    scope["kind"] = "suspended_unspecified"
    r = run([record("2016-04-01"), scope])
    assert r["observation_state"] == "medical_followup_censored"
    assert not r["pending_observation"]
    assert r["recent_censored_followup_upper_days"] == 122
    r = run([record("2016-04-01"), scope], [appearance("2016-05-01")])
    assert r["observation_state"] == "observed_MLB_use"
    assert r["recent_censored_followup_upper_days"] == 0
    assert not r["legal_or_employment_status_changed"]


def test_same_day_play_does_not_clear_injury():
    r = run([record("2016-09-01")], [appearance("2016-09-01")])
    assert r["pending_observation"]


def test_transfer_without_placement_retains_left_truncation():
    r = run([record("2016-04-01", "transfer")])
    assert r["spells"][0]["entry_is_transfer"]
    assert r["recent_placement_reports"] == 0


def test_same_day_activation_and_new_placement_preserves_new_unresolved_entry():
    r = run(
        [
            record("2016-04-01"),
            record("2016-05-01", "activation", tid=2),
            record("2016-05-01", tid=3),
        ],
        [appearance("2016-05-01")],
    )
    assert r["pending_observation"]
    assert r["same_day_timing_ambiguous"] == [date(2016, 5, 1)]


def test_reported_activation_is_not_observed_play_or_medical_clearance():
    r = run([record("2016-04-01"), record("2016-11-01", "activation", tid=2)])
    assert r["observation_state"] == "reported_IL_activation"
    assert r["observed_returns"] == []
    assert not r["medical_recovery_certified"]


def test_positive_window_only_gives_return_upper_bound():
    w = dict(
        player_id=1, start="2016-06-01", end="2016-06-30", pa=100, source_path="source"
    )
    r = run([record("2016-04-01")], windows=[w])
    s = r["spells"][0]
    assert s["observation_end_upper"] == date(2016, 6, 30)
    assert s["return_evidence"]["start"] == date(2016, 6, 1)
    assert s["closure_kind"] == "observed_MLB_use"


@pytest.mark.parametrize(
    "start,end,pa",
    [
        ("2016-03-01", "2016-05-01", 10),
        ("2016-04-01", "2016-05-01", 10),
        ("2016-04-02", "2016-05-01", 0),
    ],
)
def test_straddling_same_start_or_zero_window_cannot_clear(start, end, pa):
    w = dict(player_id=1, start=start, end=end, pa=pa, source_path="source")
    assert run([record("2016-04-01")], windows=[w])["pending_observation"]


def test_window_straddling_scope_boundary_does_not_certify_use_after_exit():
    boundary = record("2016-06-15", None, tid=2)
    boundary["kind"] = "scope_exit"
    w = dict(
        player_id=1, start="2016-06-01", end="2016-06-30", pa=5, source_path="source"
    )
    assert (
        run([record("2016-04-01"), boundary], windows=[w])["observation_state"]
        == "medical_followup_censored"
    )


def test_no_entry_and_no_contacts_are_not_healthy_certificate():
    r = run([])
    assert r["observation_state"] == "no_captured_medical_entry"
    assert not r["medical_recovery_certified"]


def test_partial_source_coverage_has_unknown_burden_not_zero():
    r = run([], cutoff="2016-01-26", origin=2015)
    assert r["missing_recent_source_years"] == [2014]
    assert r["recent_followup_calendar_upper_days"] is None
    assert r["recent_episode_count"] is None


def test_future_backdated_sources_cannot_change_inputs():
    rs, apps = [record("2016-04-01")], [appearance("2016-05-01")]
    original = deepcopy(rs)
    future = record("2016-04-15", tid=2)
    future["available_date"] = date(2017, 2, 1)
    app = appearance("2016-04-02")
    app["available_date"] = "2017-02-01"
    assert run(rs, apps) == run(rs + [future], apps + [app])
    assert rs == original


def test_wrong_identity_rejected():
    app = appearance("2016-05-01")
    app["player_id"] = 2
    with pytest.raises(ValueError, match="identity"):
        run([], [app])


def test_nonmedical_activation_does_not_close_medical_spell():
    r = record("2016-05-01", None, tid=2)
    r["kind"] = "nonmedical_activation"
    assert run([record("2016-04-01"), r])["pending_observation"]


def test_interval_union_not_double_counted_or_off_window():
    assert (
        union_days(
            [
                ("2016-01-01", "2016-01-10"),
                ("2016-01-05", "2016-01-20"),
                ("2015-12-01", "2016-01-03"),
            ],
            date(2016, 1, 1),
            date(2016, 1, 15),
        )
        == 14
    )
