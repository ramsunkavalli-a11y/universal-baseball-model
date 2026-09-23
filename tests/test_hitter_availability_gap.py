from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_availability_gap import build_gap_features, position_lookup
from universal_baseball.hitter_health_budget import available_date, exposure_training, budget_ledger, health_state
from universal_baseball.storage import sha256_file


def toy():
    records = [{"season": y, "player_id": i, "mlb_pa": 500+i} for y in range(2010, 2020) for i in range(40)]
    targets = pl.DataFrame(records)
    fielding = targets.select("season", "player_id").with_columns(pl.lit("C").alias("position_abbreviation"),
        pl.lit(100).alias("games_played"), pl.lit(1000).alias("fielding_outs"))
    panel = pl.DataFrame({"origin_year": [2016, 2016], "player_id": [0, 100]})
    return panel, targets, fielding, {y: 1. for y in range(2010, 2020)}


def test_future_outcomes_and_positions_do_not_change_past_proxy():
    panel, targets, fielding, fractions = toy()
    a, notes = build_gap_features(panel, targets, fielding, fractions)
    changed = targets.with_columns(pl.when(pl.col("season") > 2016).then(99999).otherwise(pl.col("mlb_pa")).alias("mlb_pa"))
    later_pos = fielding.with_columns(pl.when(pl.col("season") > 2016).then(pl.lit("SS")).otherwise(pl.col("position_abbreviation")).alias("position_abbreviation"))
    b, _ = build_gap_features(panel, changed, later_pos, fractions)
    assert a.equals(b)
    assert all(max(n["prior_years"]) < n["season"] for n in notes)
    # A current-season PA drop cannot change the prior-defined regular flag or peer target.
    changed = targets.with_columns(pl.when((pl.col("season") == 2016) & (pl.col("player_id") == 0))
        .then(0).otherwise(pl.col("mlb_pa")).alias("mlb_pa"))
    c, _ = build_gap_features(panel, changed, fielding, fractions)
    assert c["gap_regular_0"].to_list() == a["gap_regular_0"].to_list()
    assert c["gap_reference_0"].to_list() == a["gap_reference_0"].to_list()
    assert c["gap_shortfall_0"][0] == 1


def test_unknown_is_not_a_zero_shortfall_regular_and_order_is_stable():
    panel, targets, fielding, fractions = toy()
    a, _ = build_gap_features(panel, targets, fielding, fractions)
    b, _ = build_gap_features(panel.reverse(), targets.reverse(), fielding.reverse(), fractions)
    assert a.equals(b)
    unknown = a.filter(pl.col("player_id") == 100).row(0, named=True)
    assert unknown["gap_measured_0"] == 0 and unknown["gap_expected_pa_0"] is None
    assert unknown["gap_prior_position"] == "unknown"


def test_position_comes_from_historical_usage_not_current_profile():
    f = pl.DataFrame({"season": [2015]*3, "player_id": [1]*3, "position_abbreviation": ["C", "1B", "DH"],
        "games_played": [30, 40, 50], "fielding_outs": [810, 1080, 0]})
    assert position_lookup(f)[2015, 1] == "DH"


def test_conservative_event_date_does_not_backdate_future_il():
    assert available_date({"date": "2024-02-01", "effectiveDate": "2025-02-15", "resolutionDate": "2025-02-15"}) == date(2025, 2, 15)
    with pytest.raises(ValueError):
        available_date({})
    events = [{"transaction_id": 1, "available_date": date(2023, 8, 1), "kind": "placement"},
              {"transaction_id": 2, "available_date": date(2024, 2, 1), "kind": "activation"}]
    a = health_state(events, date(2023, 12, 31), date(2023, 10, 1), True)
    b = health_state(events[:1], date(2023, 12, 31), date(2023, 10, 1), True)
    assert a == b and a["health_open"] == 1
    unknown = health_state(events, date(2023, 12, 31), date(2023, 10, 1), False)
    assert unknown["health_status"] == "unknown_scope" and unknown["recorded_il_days730"] is None


def test_exposure_uses_only_mature_labels_and_poisson_identity():
    panel = pl.DataFrame({"origin_year": [2016, 2017, 2018], "player_id": [1, 2, 3],
                          "pa_h2": [500, 400, 99999], "war_h2": [1., 2., 99.]})
    t, e = exposure_training(panel, 2019, {2018: 1., 2019: 1., 2020: .37})
    assert t["origin_year"].to_list() == [2016, 2017] and e.tolist() == [1., 1.]
    with pytest.raises(ValueError):
        exposure_training(panel, 2026, {})
    y, exposure, a, b = 200., .37, 500., 600.
    rate_loss_difference = exposure*((a-y/exposure*np.log(a))-(b-y/exposure*np.log(b)))
    count_loss_difference = (exposure*a-y*np.log(exposure*a))-(exposure*b-y*np.log(exposure*b))
    assert rate_loss_difference == pytest.approx(count_loss_difference)


def test_budget_records_excess_without_rescaling_and_signed_value_gap():
    under = budget_ledger(100., 600., 120., 570.)
    assert under["unallocated_pa"] == 20 and under["signed_value_gap_not_pure_outsider_value"] == -30
    over = budget_ledger(130., 500., 120., 570.)
    assert over["pa_excess"] == 10 and over["named_player_pa"] == 130
    assert over["named_player_pa"] + over["unallocated_pa"] - over["pa_excess"] == over["league_pa_budget"]


def test_saved_forecasts_probabilities_rates_and_source_hashes():
    root = Path(__file__).resolve().parents[1]
    package = root/"model_artifacts/hitter-availability-gap-v1-2026-09-22"
    manifest = json.loads((package/"manifest.json").read_text())
    for name, digest in manifest["files"].items():
        assert sha256_file(package/name) == digest
    for name, digest in manifest["sources"].items():
        assert sha256_file(root/name) == digest
    f = pl.read_parquet(package/"historical-predictions.parquet")
    assert f.height == 17164 and set(f["origin_year"]) == {2019, 2021, 2022, 2023}
    for form in ("E", "T", "P"):
        np.testing.assert_allclose(f[form+"_pa"], f[form+"_q"]*f["activity_h2_challenger"])
        np.testing.assert_allclose(f[form+"_value"], f[form+"_pa"]*f["performance_anchor"]/600)
    report = json.loads((package/"report.json").read_text())
    assert not report["forecast_changed"] and not report["protected_outcomes_used"]
    assert report["budget_audit"]["league_pa_bf_verified_seasons"] == 17
    assert not report["budget_audit"]["rescaled_or_redistributed"]
