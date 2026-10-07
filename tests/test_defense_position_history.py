import pytest
import polars as pl

from universal_baseball.defense_position_history import normalize, annual_usage, index_usage, origin_summary


def row(year=2019, sport=16, league=124, pos="2", outs=90):
    return dict(season=year, sport_id=sport, league_id=league, team_id=1,
                team_name="Returned label", player_id=7, player_name="Example",
                position_code=pos, fielding_outs=outs, source_innings=f"{outs // 3}.{outs % 3}",
                games_started=4, games_played=5)


def test_early_rookie_label_cannot_become_exact_dsl_history():
    n = normalize(pl.DataFrame([row(league=130)]), "early")
    assert n["normalized_level"][0] == "ROOKIE_COMBINED"
    assert not n["level_subtype_certified"][0] and not n["team_usage_certified"][0]


def test_current_dsl_is_not_complex():
    n = normalize(pl.DataFrame([row(year=2025, league=130)]), "modern2025")
    assert n["normalized_level"][0] == "DSL"


def test_older_repair_cannot_be_added_to_full_rookie_totals():
    with pytest.raises(ValueError):
        normalize(pl.DataFrame([row(year=2018, sport=16, league=120)]), "repair2019")


def test_disjoint_2019_scopes_are_added_once():
    a = normalize(pl.DataFrame([row()]), "early")
    b = normalize(pl.DataFrame([row(sport=5442, league=120, outs=120)]), "repair2019")
    annual = annual_usage(pl.concat([a, b]))
    r = origin_summary(index_usage(annual)[7], 2019)
    assert r["minor_weighted_outs_2"] == 210
    assert not r["minor_level_subtype_certified"]


def test_duplicate_sport_totals_under_different_team_labels_fail():
    with pytest.raises(ValueError):
        normalize(pl.DataFrame([row(), {**row(), "team_id": 2}]), "early")


def test_source_innings_and_dh_are_validated():
    with pytest.raises(ValueError):
        normalize(pl.DataFrame([{**row(), "fielding_outs": 89}]), "early")
    with pytest.raises(ValueError):
        normalize(pl.DataFrame([row(pos="10")]), "early")


def test_dh_starts_are_visible_without_fake_fielding_outs():
    annual = annual_usage(normalize(pl.DataFrame([row(pos="10", outs=0)]), "early"))
    r = origin_summary(index_usage(annual)[7], 2019)
    assert r["primary_start_position"] == "10"
    assert r["primary_defensive_position"] == "unknown"
    assert r["minor_history_observed"] and r["minor_weighted_defensive_outs"] == 0


def test_future_records_cannot_change_origin_and_cancellation_is_not_zero_skill():
    a = annual_usage(normalize(pl.DataFrame([row(year=2019)]), "early"))
    future = annual_usage(normalize(pl.DataFrame([row(year=2021, league=130, outs=300)]), "modern"))
    older = index_usage(a)[7]
    assert origin_summary(older, 2020) == origin_summary(older + index_usage(future)[7], 2020)
    r = origin_summary(older, 2020)
    assert r["minor_2020_canceled_in_window"]
    assert r["minor_latest_season"] == 2019 and r["minor_weighted_outs_2"] == 45
    empty = origin_summary([], 2020)
    assert not empty["minor_history_observed"] and empty["primary_start_position"] == "unknown"
