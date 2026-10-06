from copy import deepcopy
from universal_baseball.defensive_talent_support import measurable, window_label, training_snapshot


def sources(pos=6, runs=2, outs=900):
    r = {f"outs_{p}": outs if p == pos else 0 for p in range(2, 10)}
    r.update(outs_total=outs, range_runs=runs)
    o = {f"outs_{p}": outs if p == pos else 0 for p in range(2, 10)}
    o["official_outs"] = outs
    return r, o


def origin(year=2016, pid=11):
    return dict(origin_year=year, player_id=pid, position=6, age=20.0,
                level="AA", prior_mlb_defense=False)


def test_native_unmapped_outs_cannot_be_position_quality():
    r, o = sources()
    r["outs_total"] += 3
    assert not measurable(r, o, (6,))


def test_mixed_positions_not_apportioned_but_group_inventory_allowed():
    r, o = sources()
    r["outs_6"] = o["outs_6"] = 600
    r["outs_4"] = o["outs_4"] = 300
    assert not measurable(r, o, (6,))
    assert measurable(r, o, (4, 5, 6))


def test_official_other_position_blocks_native_purity():
    r, o = sources()
    o["outs_8"] = 1
    assert not measurable(r, o, (6,))


def test_null_runs_or_outs_not_zero_quality():
    r, o = sources(runs=None)
    assert not measurable(r, o, (6,))
    r, o = sources()
    r["outs_8"] = None
    assert not measurable(r, o, (6,))


def test_nonarrival_has_unknown_not_zero_talent():
    result, path = window_label(origin(), 5, {}, {})
    assert result["window_mature"]
    assert result["quality_rate"] is None
    assert result["quality_status"] == "no_recorded_mlb_fielding"
    assert len(path) == 5


def test_partial_window_retains_observation_without_completed_label():
    r, o = sources(outs=1800)
    result, path = window_label(origin(2023), 3, {11: {2024: r, 2025: r}}, {11: {2024: o, 2025: o}})
    assert result["observed_same_position_rate"] is not None
    assert result["quality_rate"] is None
    assert not result["window_mature"]
    assert len(path) == 2


def test_pool_includes_all_fixed_seasons_not_best_season():
    r1, o1 = sources(runs=9)
    r2, o2 = sources(runs=-3)
    row, _ = window_label(origin(), 3, {11: {2017: r1, 2018: r2}}, {11: {2017: o1, 2018: o2}})
    assert row["quality_rate"] == 5


def test_outfield_performance_does_not_label_shortstop_talent():
    r, o = sources(pos=8)
    row, _ = window_label(origin(), 3, {11: {2017: r, 2018: r}}, {11: {2017: o, 2018: o}})
    assert row["quality_rate"] is None
    assert not row["infield_group_quality_available"]


def test_actual_cutoff_and_held_player_support_counts_people_not_rows():
    r, o = sources()
    labels = []
    for year, pid in [(2016, 11), (2017, 11), (2016, 10), (2018, 12)]:
        row, _ = window_label(origin(year, pid), 3, {pid: {year + 1: r, year + 2: r}}, {pid: {year + 1: o, year + 2: o}})
        labels.append(row)
    stats, _ = training_snapshot(labels, 2020, 0, 3)
    assert stats["training_rows"] == 2
    assert stats["training_people"] == 1
    assert stats["training_origins"] == [2016, 2017]
    assert not stats["small_comparison_count_screen"]


def test_future_test_quality_does_not_change_origin_or_support():
    r, o = sources()
    old, _ = window_label(origin(2016, 11), 3, {11: {2017: r, 2018: r}}, {11: {2017: o, 2018: o}})
    test, _ = window_label(origin(2021, 10), 3, {}, {})
    labels = [old, test]
    before = training_snapshot(labels, 2021, 0, 3)
    changed = deepcopy(labels)
    changed[1]["quality_rate"] = 1000
    assert before == training_snapshot(changed, 2021, 0, 3)
    assert all(test[key] == origin(2021, 10)[key] for key in origin(2021, 10))
