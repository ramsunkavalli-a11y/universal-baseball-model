from copy import deepcopy
import pytest

from universal_baseball.defensive_talent_position import label, origin_context, preflight, person_weights


def origin():
    return dict(origin_year=2021, player_id=10, position=6, ground_balls=100., credits=20.,
                age=None, level="INACTIVE", player_name=None, dsl_ground_balls=0.,
                source_history_left_truncated=False, prior_mlb_defense=False, complete_rate=0.)


def context():
    r = origin()
    minor = {(10, 6): [dict(season=2021, level="a-", ground_balls=100.), dict(season=2022, level="aaa", ground_balls=9000.)]}
    return origin_context(r, minor, {10: dict(birth_date="2001-08-01", captured_name="Test")}, {}, {})


def test_identity_and_shortseason_context_uses_cutoff():
    r = context()
    assert r["age"] == 19 and r["fielding_level"] == "a-"
    assert r["share_a-"] == 1 and r["share_aaa"] == 0
    assert r["original_level"] == "INACTIVE"


def test_missing_current_fielding_not_retired():
    r = origin()
    r["ground_balls"] = 50.
    out = origin_context(r, {(10, 6): [dict(season=2020, level="aa", ground_balls=100.)]}, {}, {}, {})
    assert out["fielding_level"] == "NO_CURRENT_MINOR_FIELDING" and out["share_aa"] == 1
    assert out["age_missing"] and not out["current_fielding"]


def test_nonarrival_unknown_not_zero_quality():
    value, path = label(context(), 3, {}, {})
    assert value["quality_rate"] is None and value["window_mature"]
    assert len(path) == 3


def test_measured_quality_requires_two_seasons_and_complete_window():
    native = {(10, 6): {2022: dict(season=2022, native_outs=3000, range_runs=6., measurement_valid=True)}}
    value, _ = label(context(), 3, native, {})
    assert value["quality_rate"] is None
    native[(10, 6)][2023] = dict(season=2023, native_outs=1500, range_runs=-3., measurement_valid=True)
    value, _ = label(context(), 3, native, {})
    assert value["quality_rate"] == 1.
    later = context(); later["origin_year"] = 2023
    assert label(later, 3, native, {})[0]["quality_rate"] is None


def test_null_metric_and_other_position_not_quality():
    native = {(10, 5): {2022: dict(season=2022, native_outs=3000, range_runs=9., measurement_valid=True)},
              (10, 6): {2022: dict(season=2022, native_outs=3000, range_runs=None, measurement_valid=False)}}
    value, _ = label(context(), 3, native, {(2022, 10, 6): 3000})
    assert value["quality_rate"] is None and value["unmeasured_official_outs"] == 3000


def test_preflight_rejects_unmature_label_and_same_player():
    r = context(); r.update(horizon=3, window_end=2024, quality_rate=1.)
    with pytest.raises(AssertionError):
        preflight([r], [], 2022, 1, 3)
    r.update(origin_year=2017, window_end=2020)
    t = context(); t.update(horizon=3, origin_year=2022)
    with pytest.raises(AssertionError):
        preflight([r], [t], 2022, 0, 3)


def test_repeated_rows_not_independent_support():
    rows = []
    for y in (2016, 2017):
        r = context(); r.update(origin_year=y, horizon=3, window_end=y + 3, quality_rate=1.)
        rows.append(r)
    check, _ = preflight(rows, [], 2022, 1, 3)
    assert check["training_people"] == 1 and not check["fit_allowed"]
    assert person_weights(rows).tolist() == [.5, .5]
