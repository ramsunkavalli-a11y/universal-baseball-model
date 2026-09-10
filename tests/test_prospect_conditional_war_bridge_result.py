from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/prospect-conditional-war-bridge-result.json"


def test_conditional_war_bridge_preserves_declared_boundaries() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["protocol"]["training_origin"] == 2018
    assert report["protocol"]["outer_origin"] == 2021
    assert report["protocol"]["horizon_years"] == 2
    assert report["protocol"]["ridge_alpha"] == 100.0
    assert report["protocol"]["rate_regression_opportunities"] == 200.0
    assert report["protocol"]["frozen_plan_sha256"] == sha256(
        (ROOT / "docs/prospect-conditional-war-bridge-plan.md").read_bytes()
    ).hexdigest()
    assert report["boundaries"] == {
        "all_non_arrivals_retained": True,
        "demographics_used_as_talent": False,
        "organization_used": False,
        "outside_fv_used": False,
        "predictions_clipped": False,
        "production_values_changed": False,
    }


def test_conditional_war_bridge_improves_errors_but_respects_frozen_bias_gate() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    for player_type in ("hitter", "pitcher"):
        result = report["results"][player_type]
        baseline = result["end_to_end_baseline"]
        candidate = result["end_to_end_candidate"]
        assert candidate["rmse"] < baseline["rmse"]
        assert candidate["mae"] < baseline["mae"]
        assert result["paired_difference"]["mse"]["ci_high"] < 0
        assert result["paired_difference"]["mae"]["ci_high"] < 0
        assert (
            result["conditional_on_observed_arrival_candidate"]["rmse"]
            < result["conditional_on_observed_arrival_baseline"]["rmse"]
        )
        assert result["decision_checks"]["absolute_bias_not_worse"] is False
        assert result["promising_development_evidence"] is False
        features = {
            row["feature"] for row in result["standardized_ridge_coefficients"]
        }
        assert len(features) == 19
        assert not any(
            token in feature
            for feature in features
            for token in ("birth", "country", "height", "weight", "draft", "fv")
        )


def test_unchanged_bridge_fit_fails_later_stability_gate_as_declared() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["stability_protocol"]["fit_origin"] == 2018
    assert report["stability_protocol"]["evaluation_origins"] == [2022, 2023]
    assert report["stability_protocol"]["refit_or_recalibration"] is False
    assert report["stability_protocol"]["frozen_plan_sha256"] == sha256(
        (ROOT / "docs/prospect-conditional-war-bridge-stability-plan.md").read_bytes()
    ).hexdigest()
    assert report["stability_passed"] is False
    for origin in ("2022", "2023"):
        hitter = report["stability_results"]["hitter"][origin]
        pitcher = report["stability_results"]["pitcher"][origin]
        assert (
            hitter["conditional_on_observed_arrival_candidate"]["rmse"]
            > hitter["conditional_on_observed_arrival_baseline"]["rmse"]
        )
        assert pitcher["decision_checks"]["absolute_bias_not_worse"] is False
        assert pitcher["paired_difference"]["mse"]["ci_high"] >= 0
