from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/prospect-broad-history-skill-tail-result.json"


def test_skill_tail_preserves_frozen_method_and_statistical_laws() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    protocol = report["protocol"]
    assert protocol["training_origins"] == [2008, 2009, 2010]
    assert protocol["old_evaluation_origins"] == [2013, 2014, 2015, 2016, 2017]
    assert protocol["modern_evaluation_origins"] == [2021, 2022, 2023]
    assert protocol["horizon_years"] == 2
    assert protocol["threshold_component_war"] == 0.25
    assert protocol["logistic_c"] == 0.1
    assert protocol["regression_opportunities"] == 200.0
    assert protocol["frozen_plan_sha256"] == sha256(
        (ROOT / "docs/prospect-broad-history-skill-tail-plan.md").read_bytes()
    ).hexdigest()
    assert protocol["cohort_correction_sha256"] == sha256(
        (ROOT / "docs/prospect-broad-history-pre-mlb-cohort-correction.md").read_bytes()
    ).hexdigest()
    assert all(report["law_checks"].values())


def test_skill_rates_help_basic_model_but_do_not_clear_gate() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["decision"] == "reject_aggregate_skill_tail"
    assert report["production_changed"] is False
    for player_type in ("hitter", "pitcher"):
        result = report["results"][player_type]
        assert result["gate_passed"] is False
        assert result["candidate_beats_constant"]["modern"] is False
        assert sum(
            row["both_scores_improved"] for row in result["by_origin"].values()
        ) >= 5
        assert any(
            result["pooled"][era][metric]["ci_high"] >= 0
            for era in ("old", "modern")
            for metric in ("brier", "log_loss")
        )


def test_skill_rate_directions_are_baseball_coherent_but_not_causal() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    coefficients = {
        player_type: {
            row["feature"]: row["coefficient"]
            for row in report["results"][player_type]["standardized_coefficients"]
        }
        for player_type in ("hitter", "pitcher")
    }
    assert coefficients["hitter"]["rate_2"] < 0  # strikeouts
    assert coefficients["hitter"]["rate_3"] > 0  # home runs
    assert coefficients["pitcher"]["rate_1"] > 0  # strikeouts
    assert coefficients["pitcher"]["rate_2"] < 0  # unintentional walks
