import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_opportunity_calendar import (
    exact_contributions, mean_origin, prepare_rows, regime, score_rows, summarize,
)
from universal_baseball.storage import sha256_file


def examples():
    history = pl.DataFrame({"origin_year": [2016, 2016, 2018, 2018], "player_id": [1, 2, 1, 3],
        "pa_h2": [0, 300, 200, 0], "war_h2": [0., 2., 1., 0.], "performance_anchor": [2., 3., 2., 1.],
        "activity_h2_challenger": [.3, .9, .9, .2], "conditional_pa_h2_challenger": [100., 400., 500., 50.]})
    base = history.select("origin_year", "player_id", "pa_h2").with_columns(
        pl.Series("activity_h2", [.2, .8, .8, .1]), pl.Series("expected_pa_h2", [20., 240., 320., 10.]))
    updates = pl.DataFrame({"origin_year": [2016], "player_id": [2], "actual_pa": [300],
        "p1": [.9], "pa1": [270.], "p0": [.8], "pa0": [240.]})
    return history, base, updates


def test_keyed_updates_preserve_conditional_pa_and_order():
    h, b, u = examples()
    a = prepare_rows(h, b, u)
    z = prepare_rows(h.reverse(), b.reverse(), u.reverse())
    assert a.equals(z)
    assert a["old_p"].to_list() == [.2, .9, .8, .1]
    assert a["old_q"].to_list() == [100., 300., 400., 100.]


def test_missing_rows_duplicate_keys_and_different_labels_fail():
    h, b, u = examples()
    with pytest.raises(ValueError, match="cohorts"):
        prepare_rows(h, b.head(3), u)
    with pytest.raises(ValueError, match="Duplicate"):
        prepare_rows(pl.concat([h, h.head(1)]), b, u)
    with pytest.raises(AssertionError):
        prepare_rows(h, b.with_columns(pl.lit(0).alias("pa_h2")), u)
    with pytest.raises(AssertionError):
        prepare_rows(h, b, u.with_columns(pl.lit(0).alias("actual_pa")))
    with pytest.raises(ValueError, match="Missing"):
        prepare_rows(h, b, u.with_columns(pl.lit(None, dtype=pl.Float64).alias("p1")))


def test_protected_or_unobserved_labels_fail():
    h, b, u = examples()
    with pytest.raises(ValueError, match="Protected"):
        prepare_rows(h.with_columns(pl.when(pl.col("origin_year") == 2018).then(2025)
            .otherwise(pl.col("origin_year")).alias("origin_year")), b, u)
    with pytest.raises(ValueError, match="Missing"):
        prepare_rows(h.with_columns(pl.lit(None, dtype=pl.Float64).alias("war_h2")), b, u)
    with pytest.raises(ValueError, match="Nonzero production"):
        prepare_rows(h.with_columns(pl.lit(1.).alias("war_h2")), b, u)


def test_head_swap_contributions_sum_exactly_for_pa_and_value():
    scored = score_rows(prepare_rows(*examples()))
    for target in ("pa", "value"):
        np.testing.assert_allclose(scored[f"{target}_activity_contribution"] + scored[f"{target}_conditional_contribution"],
            scored[f"{target}_loss_11"] - scored[f"{target}_loss_00"])
    a, q = exact_contributions(np.array([10.]), np.array([5.]), np.array([10.]), np.array([5.]))
    assert a[0] == -5 and q[0] == 0


def test_no_play_is_zero_in_total_pa_but_excluded_from_conditional_scores():
    s = score_rows(prepare_rows(*examples()))
    report = summarize(s)
    assert report["rows"] == 4 and report["active_rows"] == 2
    assert report["actual_pa"] == 125
    assert report["actual_pa_if_active"] == 250
    assert report["old"]["conditional_pa"] == 350
    empty_active = summarize(s.filter(pl.col("pa_h2") == 0))
    assert empty_active["old"]["conditional_rmse"] is None
    assert empty_active["old"]["pa_mse"] > 0


def test_hindsight_scaling_is_only_2020_and_never_changes_labels_or_odds():
    matched = prepare_rows(*examples())
    rows = matched.filter(pl.col("origin_year") == 2018)
    ordinary, sensitivity = score_rows(rows), score_rows(rows, .37)
    np.testing.assert_allclose(sensitivity["pa_11"], ordinary["pa_11"] * .37)
    assert sensitivity["new_p"].equals(ordinary["new_p"])
    assert sensitivity["pa_h2"].equals(ordinary["pa_h2"])
    with pytest.raises(ValueError, match="target 2020"):
        score_rows(matched, .37)
    assert regime(2019) == "pandemic_bridge_to_2021"
    assert regime(2021) == "ordinary_post"


def test_equal_origin_metrics_do_not_pool_or_depend_on_order():
    f = pl.DataFrame({"origin_year": [2016, 2016, 2018], "player_id": [1, 2, 1], "x": [1., 3., 10.]})
    assert mean_origin(f, "x") == 6
    assert mean_origin(f.reverse(), "x") == 6


def test_diagnostic_package_is_complete_and_keeps_forecasts_unchanged():
    root = Path(__file__).resolve().parents[1]
    package = root / "model_artifacts/hitter-opportunity-calendar-v1-2026-09-22"
    manifest = json.loads((package / "manifest.json").read_text())
    assert not manifest["forecast_changed"] and not manifest["protected_outcomes_used"]
    for name, digest in manifest["files"].items():
        assert sha256_file(package / name) == digest
    for name, digest in manifest["sources"].items():
        assert sha256_file(root / name) == digest
    report = json.loads((package / "report.json").read_text())
    assert report["rows"] == 26571 and report["excluded_opportunity_origin"]["origin"] == 2023
    ordinary = report["calendar_scopes"]["ordinary"]["Top50"]
    assert ordinary["origins"] == [2016, 2017, 2021, 2022] and ordinary["rows"] == 200
    young = report["calendar_scopes"]["ordinary"]["Top50 under26"]
    assert young["rows"] == 63 and not young["supported_multiorigin"]
    assert "paired_pa_mse" not in young
    assert report["hindsight_exposure"]["fraction"] == pytest.approx(898 / 2430)
