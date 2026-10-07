import pytest
import numpy as np

from universal_baseball.defense_opportunity_bridge import role_mix, estimate, sufficient, choose, predict, native_from_outs, native_conversion, ROLES


def row(pid=1, pa=100):
    return dict(player_id=pid, row_id=pid, next_pa=pa, preseason_pa=50, stage="Upper minors", age_band="4", source_position="2",
                **{f"{kind}_weighted_{measure}_{p}": 0. for kind in ("mlb", "minor") for measure in ("starts", "outs") for p in ROLES})


def test_mixed_roles_and_mlb_history_do_not_delete_minor_positions():
    r = row()
    r.update(mlb_weighted_starts_2=1., minor_weighted_starts_8=9.)
    shares, kind = role_mix(r)
    assert shares[ROLES.index(2)] == .1 and shares[ROLES.index(8)] == .9
    assert kind == "observed_starts" and sum(shares) == 1


def test_dh_can_have_role_without_defensive_outs():
    r = row()
    r["minor_weighted_starts_10"] = 30
    shares, _ = role_mix(r)
    assert shares[-1] == 1 and sum(shares[:-1]) == 0


def test_unknown_and_outs_fallback_are_not_observed_starts():
    r = row()
    r["source_position"] = "1"
    assert role_mix(r)[1] == "unknown_role"
    r["minor_weighted_outs_6"] = 100
    assert role_mix(r)[1] == "observed_outs_fallback"


def test_fit_is_ratio_of_total_opportunities_and_exposure_not_average_tiny_rates():
    a, b = row(1, 1), row(2, 100)
    target = {1: [10.] * 9, 2: [100.] * 9}
    c = estimate([a, b], ("all",), target)
    assert np.allclose(c["rates"], [110 / 101] * 9)
    assert c["people"] == 2


def test_repeated_seasons_do_not_create_distinct_people_or_effective_support():
    r = row()
    c = estimate([r] * 50, ("all",))
    assert c["people"] == 1 and c["effective_people"] == 1
    assert not sufficient(c)


def test_sparse_context_falls_back_without_changing_playing_time():
    r = row()
    cell = dict(people=30, effective_people=20., denominator_PA=1000., rates=[2.] * 9, numerator=[2000.] * 9, rows=30)
    sparse = {**cell, "people": 1}
    tables = {("role_stage_age", "2", "Upper minors", "4"): {**sparse, "scope": ["role_stage_age", "2", "Upper minors", "4"]},
              ("role_stage", "2", "Upper minors"): {**sparse, "scope": ["role_stage", "2", "Upper minors"]},
              ("role", "2"): {**cell, "scope": ["role", "2"]}, ("all",): {**cell, "scope": ["all"]}}
    out = predict(tables, r, True)
    assert out["values"] == [100.] * 9 and out["coarse_mass"] == 1
    r["preseason_pa"] = 0
    assert predict(tables, r, True)["values"] == [0.] * 9


def test_native_channels_use_distinct_exposure_and_never_dh():
    conversion = {c: {"rate": 2} for c in ("framing", "throwing", "blocking", "arm", "receiving")}
    values = [3, 5, 0, 0, 0, 7, 11, 13, 100]
    out = native_from_outs(values, conversion)
    assert out == dict(framing=6, throwing=6, blocking=6, arm=62, receiving=10)


def test_native_rate_excludes_future_and_held_players():
    records = [dict(player_id=i, season=y, valid=True, opportunities=4, official_exposure=2)
               for y in (2021, 2022) for i in range(1, 31)]
    future = dict(player_id=999, season=2023, valid=True, opportunities=10000, official_exposure=1)
    out = native_conversion(records + [future], 2022, 0, lambda pid: pid % 5)
    assert out["rate"] == 2 and out["people"] == 24


def test_unsupported_native_channel_stops_instead_of_inventing_rate():
    with pytest.raises(ValueError):
        native_conversion([], 2022, 0, lambda pid: pid % 5)
