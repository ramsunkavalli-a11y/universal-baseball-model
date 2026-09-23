import numpy as np
import polars as pl
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_established_hitter_opportunity import _dataset, _mature_training
from report_multiyear_hitter_followup_v2 import deliver, MEANS

from universal_baseball.multiyear_hitter_followup import (
    calibrate, compare_losses, interval_score, opportunity_mask, upper_quantile,
)


def test_mature_and_pandemic_opportunity_mask():
    f = pl.DataFrame({"origin_year": [2015, 2017, 2019, 2021, 2022],
                      "established": [True]*5, "war_h3": [1.]*5})
    assert opportunity_mask(f, 2024, 3).tolist() == [True, False, False, True, False]


def test_upper_quantile_uses_finite_sample_rank():
    assert upper_quantile(np.arange(10)) == 8.
    with pytest.raises(ValueError):
        upper_quantile([])


def test_interval_score_penalizes_misses_and_preserves_negative_values():
    np.testing.assert_equal(interval_score([-2., 0., 3.], [-1.]*3, [1.]*3), [12., 2., 22.])


def test_calibration_ignores_unmatured_and_future_labels():
    def origin(year, value):
        return pl.DataFrame({"origin_year": [year]*200, "player_id": list(range(200)),
            "stage": ["Upper minors"]*200, "mean": np.arange(200)/100,
            "actual": [value]*200, "raw_lo": [-1.]*200, "raw_hi": [1.]*200})
    past = pl.concat([origin(2012, 0.), origin(2013, 2.), origin(2014, 1000.), origin(2025, 2000.)])
    test = origin(2016, 99.)
    a = calibrate(past, test, 2016, 3)
    b = calibrate(past.filter(pl.col("origin_year") <= 2013), test.with_columns(pl.lit(-999.).alias("actual")), 2016, 3)
    for col in ("q2_lo", "q2_hi", "q0_lo", "q0_hi"):
        np.testing.assert_equal(a[col].to_numpy(), b[col].to_numpy())
    assert a["latest_calibration_origin"].max() == 2013
    assert a["correction"].min() >= 0
    assert a.filter(pl.col("high_prior"))["stage_fallback"].all()


def test_no_calibration_without_two_origins():
    f = pl.DataFrame({"origin_year": [2012]*200, "player_id": list(range(200)),
        "stage": ["Lower minors"]*200, "mean": [0.]*200, "actual": [0.]*200,
        "raw_lo": [-1.]*200, "raw_hi": [1.]*200})
    result = calibrate(f, f.with_columns(pl.lit(2016).alias("origin_year")), 2016, 3)
    assert result["q2_lo"].null_count() == 200


def test_equal_origin_cluster_loss():
    f = pl.DataFrame({"player_id": [1, 2, 1], "origin_year": [2016, 2016, 2022],
                      "a": [1., 1., 3.], "b": [0., 0., 0.]})
    assert compare_losses(f, "a", "b", draws=20)["delta"] == 2.
    assert compare_losses(f, "a", "a", draws=20)["interval95"] == [0., 0.]


def test_legacy_dataset_does_not_zero_unobserved_future():
    features = pl.DataFrame({"season":[2021,2022,2025],"player_id":[1,1,1],"origin_age":[20.,21.,24.]})
    outcomes = pl.DataFrame({"season":[2025],"player_id":[2],"pa":[100.]})
    result = _dataset(features,outcomes,3,complete_seasons=(2024,2025))
    assert result["future_pa"].to_list()==[0.,0.,None]
    assert _mature_training(result,2024,3)["season"].to_list()==[2021]


def test_shuffled_opportunity_rows_deliver_by_id_and_preserve_means():
    import json
    root = Path(__file__).resolve().parents[1]
    folder = root/"model_artifacts/multiyear-hitter-followup-v2-2026-09-22"
    original = pl.read_parquet(root/"model_artifacts/multiyear-hitter-development-2026-09-22/forecast-2026-2028.parquet")
    opportunities = pl.read_parquet(folder/"opportunity-predictions.parquet").sample(fraction=1,shuffle=True,seed=91)
    intervals = pl.read_parquet(folder/"calibrated-predictions.parquet")
    report = json.loads((folder/"delivery-report.json").read_text())
    actual = deliver(original.reverse(),opportunities,intervals,report).sort("player_id")
    expected = pl.read_parquet(folder/"forecast-2026-2028.parquet").sort("player_id")
    for col in [*MEANS, "activity_h1","activity_h2","activity_h3","expected_pa_h1","expected_pa_h2","expected_pa_h3"]:
        np.testing.assert_array_equal(actual[col].to_numpy(),expected[col].to_numpy())
    for col in MEANS:
        assert actual[col+"_lower80"].null_count()==3907


def test_published_probabilities_reproduce_saved_coefficients_by_player():
    import json
    from evaluate_multiyear_hitter_followup_v2 import established_features, p_matrix, SOURCE
    root = Path(__file__).resolve().parents[1]
    panel_path = root/"reports/generated/multiyear-hitter-v1/panel.parquet"
    if not panel_path.exists() or not SOURCE.exists():
        pytest.skip("Local recovered source inventory required for coefficient replay")
    folder = root/"model_artifacts/multiyear-hitter-followup-v2-2026-09-22"
    features = established_features(pl.read_parquet(panel_path)).filter((pl.col("origin_year")==2025)&pl.col("established")).sort("player_id")
    forecasts = pl.read_parquet(folder/"forecast-2026-2028.parquet").filter(pl.col("established_opportunity_eligible")).sort("player_id")
    fits = json.loads((folder/"opportunity-fits.json").read_text())
    for h in (1,2,3):
        fit = next(r for r in fits if r["origin"]==2025 and r["horizon"]==h)
        z = (p_matrix(features,h)-fit["logistic_means"])/fit["logistic_scales"]
        logits = z@np.asarray(fit["logistic_coefficients"])[0]+fit["logistic_intercept"][0]
        np.testing.assert_allclose(1/(1+np.exp(-logits)),forecasts[f"activity_h{h}"],rtol=1e-12)
