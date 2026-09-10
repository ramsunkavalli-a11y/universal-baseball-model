from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/prospect-broad-history-positive-tail-result.json"


def test_broad_history_tail_test_preserves_frozen_protocol() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    protocol = report["protocol"]
    assert protocol["training_origins"] == [2008, 2009, 2010]
    assert protocol["old_evaluation_origins"] == [2013, 2014, 2015, 2016, 2017]
    assert protocol["modern_evaluation_origins"] == [2021, 2022, 2023]
    assert protocol["horizon_years"] == 2
    assert protocol["threshold_component_war"] == 0.25
    assert protocol["logistic_c"] == 0.1
    assert protocol["frozen_plan_sha256"] == sha256(
        (ROOT / "docs/prospect-broad-history-positive-tail-plan.md").read_bytes()
    ).hexdigest()
    assert protocol["chronology_correction_sha256"] == sha256(
        (ROOT / "docs/prospect-broad-history-positive-tail-chronology-correction.md").read_bytes()
    ).hexdigest()
    assert protocol["cohort_correction_sha256"] == sha256(
        (ROOT / "docs/prospect-broad-history-pre-mlb-cohort-correction.md").read_bytes()
    ).hexdigest()
    forbidden = ("birth", "country", "height", "weight", "draft", "fv", "team")
    features = [
        feature
        for player_features in protocol["features"].values()
        for feature in player_features
    ]
    assert not any(
        token in feature
        for feature in features
        for token in forbidden
    )


def test_broad_history_tail_test_rejects_unstable_basic_family() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["decision"] == "reject_basic_tail_family"
    assert report["production_changed"] is False
    hitter = report["results"]["hitter"]
    pitcher = report["results"]["pitcher"]
    assert hitter["gate_passed"] is False
    assert pitcher["gate_passed"] is False
    assert all(report["law_checks"].values())


def test_broad_history_tail_training_weights_people_not_repeat_rows() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    for player_type in ("hitter", "pitcher"):
        training = report["results"][player_type]["training"]
        assert training["inverse_player_frequency_weighting"] is True
        assert training["players"] < training["rows"]
        assert 0 < training["positive_rows"] < training["rows"]
