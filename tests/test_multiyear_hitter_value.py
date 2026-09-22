import numpy as np
import polars as pl
import pytest

from scripts.materialize_multiyear_hitter_v1 import completed_schedule
from universal_baseball.multiyear_hitter_value import calendar_targets, attach_outcomes, training_mask, prepare_features
from test_hitter_value_panel import _mlb, _stat_rows


def test_schedule_excludes_cancelled_postponed_and_duplicate_suspended_games():
    def game(i, code):
        return {"gamePk": i, "gameType": "R", "status": {"abstractGameState": "Final", "codedGameState": code},
                "teams": {"home": {"team": {"id": 1}}, "away": {"team": {"id": 2}}}}
    p = {"dates": [{"date": "2020-09-01", "games": [game(1, "F"), game(1, "F"), game(2, "D"), game(3, "C")]}]}
    assert completed_schedule(p, 2020) == (1, 2)


def test_replacement_scales_to_games_without_rescaling_batting():
    hitting = _mlb().with_columns(pl.lit(2020).alias("season"))
    schedules = pl.DataFrame({"season": [2020], "completed_games": [898], "teams": [30]})
    result = calendar_targets(hitting, schedules)
    assert result["component_war"].sum() == pytest.approx(570 * 898 / 2430)
    assert result["legacy_component_war"].sum() == pytest.approx(570)
    with pytest.raises(ValueError, match="Protected"):
        calendar_targets(hitting.with_columns(pl.lit(2026).alias("season")), schedules)


def test_zero_vs_censored_and_complete_cumulative_window():
    f = pl.DataFrame({"origin_year": [2022, 2023, 2025], "player_id": [7, 7, 7]})
    t = pl.DataFrame({"season": [2023, 2024, 2025], "player_id": [8, 8, 8], "mlb_pa": [5., 5., 5.], "component_war": [-1., 1., 1.]})
    p = attach_outcomes(f, t)
    assert p["war_c3"].to_list() == [0., None, None]
    assert p["war_h1"].to_list() == [0., 0., None]
    assert training_mask(p, 2024, 2).tolist() == [True, False, False]
    assert not training_mask(p, 2025, 3, [7]).any()
    assert attach_outcomes(f, t.filter(pl.col("season") != 2024))["war_c3"].null_count() == 3


def test_future_stats_do_not_change_earlier_features_and_missing_season_not_shifted():
    snapshots = pl.DataFrame({"snapshot_year": [2017, 2021], "player_id": [1, 1], "age_years": [22., 26.], "as_of_level_group": ["AAA", "AAA"]})
    targets = pl.DataFrame({"season": [2017], "player_id": [1], "component_war": [1.]})
    membership = pl.DataFrame({"season": [2017], "player_id": [1], "on_40man": [True]})
    a, bcols, cols = prepare_features(snapshots, _stat_rows(), targets, membership)
    altered = pl.concat([_stat_rows(), _stat_rows().filter(pl.col("season") == 2017).with_columns(pl.lit(2018).cast(pl.Int64).alias("season"), pl.lit(14).cast(pl.Int64).alias("home_runs"))])
    b, _, _ = prepare_features(snapshots, altered, targets, membership)
    np.testing.assert_equal(a.filter(pl.col("origin_year") == 2017).select(cols).to_numpy(), b.filter(pl.col("origin_year") == 2017).select(cols).to_numpy())
    assert a.filter(pl.col("origin_year") == 2021)["missing_lag1"].item() == 1
    assert not set(cols) & {"player_id", "origin_year", "war_h1", "war_c3"}
