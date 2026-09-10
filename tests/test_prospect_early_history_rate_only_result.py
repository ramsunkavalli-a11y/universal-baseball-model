from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/prospect-early-history-rate-only-result.json"


def test_early_rate_only_test_preserves_frozen_chronology_and_laws() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    protocol = report["protocol"]
    assert protocol["training_origin"] == 2003
    assert protocol["unused_gap_origins"] == [2004, 2005]
    assert protocol["evaluation_origins"] == [2006, 2007]
    assert protocol["horizon_years"] == 2
    assert protocol["threshold_component_war"] == 0.25
    assert protocol["logistic_c"] == 0.1
    assert protocol["regression_opportunities"] == 200.0
    assert protocol["frozen_plan_sha256"] == sha256(
        (ROOT / "docs/prospect-early-history-rate-only-plan.md").read_bytes()
    ).hexdigest()
    assert all(report["law_checks"].values())


def test_early_rate_only_model_is_rejected_without_production_change() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["decision"] == "reject_rate_only_family"
    assert report["production_changed"] is False
    hitter = report["results"]["hitter"]
    pitcher = report["results"]["pitcher"]
    assert sum(row["both_scores_improved"] for row in hitter["by_origin"].values()) == 2
    assert sum(row["both_scores_improved"] for row in pitcher["by_origin"].values()) == 1
    for result in (hitter, pitcher):
        assert result["gate_passed"] is False
        assert result["pooled"]["brier"]["ci_high"] >= 0
        assert result["pooled"]["log_loss"]["ci_high"] >= 0


def test_early_rate_only_coefficients_retain_coherent_main_directions() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    coefficients = {
        player_type: {
            row["feature"]: row["coefficient"]
            for row in report["results"][player_type]["standardized_coefficients"]
        }
        for player_type in ("hitter", "pitcher")
    }
    assert coefficients["hitter"]["rate_2"] < 0
    assert coefficients["hitter"]["rate_3"] > 0
    assert coefficients["pitcher"]["rate_1"] > 0
    assert coefficients["pitcher"]["rate_2"] < 0

