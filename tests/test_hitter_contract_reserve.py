import polars as pl
import pytest

from universal_baseball.hitter_contract_reserve import contract_source_usable, dh_budget


def fixture():
    panel = pl.DataFrame({"origin_year": [2016, 2017, 2021], "player_id": [1, 1, 1]})
    targets = pl.DataFrame({"season": [2018, 2018, 2018, 2019, 2019, 2019, 2021, 2022, 2023],
        "player_id": [1, 2, 3, 1, 2, 3, 1, 1, 1],
        "mlb_pa": [900., 50., 50., 900., 50., 50., 1000., 1000., 1e9]})
    schedules = pl.DataFrame({"season": [2018, 2019, 2021, 2022, 2023], "completed_games": [2430]*5, "teams": [30]*5})
    pitching = pl.DataFrame({"season": [2018, 2019, 2023], "player_id": [2, 2, 3], "pitching_bf": [100, 100, 999]})
    return panel, targets, schedules, pitching


def test_separate_pitcher_slot_and_keep_other_reserve():
    b = dh_budget(*fixture(), 2022)
    assert b["old_reserve_pa"] == 100
    assert b["reserve_pa"] == 50
    assert b["named_budget"] == 950
    assert b["structural_pitcher_slot_reserve"] == 0
    assert all(r["pitcher_proxy_pa"] == 50 for r in b["reserve_support"])


def test_no_hindsight_rule_or_protected_cutoff():
    for cutoff in [2021, 2026]:
        with pytest.raises(ValueError, match="rule-known"):
            dh_budget(*fixture(), cutoff)


def test_future_targets_and_pitching_do_not_change_reserve():
    panel, targets, schedules, pitching = fixture()
    before = dh_budget(panel, targets, schedules, pitching, 2022)
    assert before == dh_budget(panel.filter(pl.col("origin_year") < 2021),
        targets.filter(pl.col("season") <= 2022), schedules.filter(pl.col("season") <= 2022),
        pitching.filter(pl.col("season") <= 2022), 2022)


def test_high_volume_two_way_batter_is_not_removed():
    panel, targets, schedules, pitching = fixture()
    targets = targets.with_columns(pl.when(pl.col("player_id") == 2).then(200.).otherwise(pl.col("mlb_pa")).alias("mlb_pa"))
    b = dh_budget(panel, targets, schedules, pitching, 2022)
    assert b["reserve_pa"] == pytest.approx(b["old_reserve_pa"])
    assert all(r["pitcher_proxy_pa"] == 0 for r in b["reserve_support"])


def test_contract_snapshot_does_not_backdate_itself():
    assert not contract_source_usable("2026-01-31T16:51:13Z", 2025)
    assert not contract_source_usable("2026-09-08", 2023)
    assert not contract_source_usable(None, 2023)
    assert contract_source_usable("2023-12-31", 2023)
    assert not contract_source_usable("2026-01-31", 2023, event_history_certified=True)
    assert not contract_source_usable("2026-01-31", 2023, event_known_date="2023-12-01")
    assert not contract_source_usable("2026-01-31", 2023, event_known_date="2024-01-01", event_history_certified=True)
    assert contract_source_usable("2026-01-31", 2023, event_known_date="2023-12-01", event_history_certified=True)
