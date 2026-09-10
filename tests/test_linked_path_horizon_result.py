from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _report(player_type: str) -> dict[str, object]:
    path = ROOT / f"docs/dependent-career-linked-{player_type}-replay-result.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_pitcher_linked_path_tradeoff_persists_across_horizons() -> None:
    report = _report("pitcher")
    rows = report["horizon_sensitivity"]
    assert [row["horizon_years"] for row in rows] == [1, 2, 3, 4]
    assert all(
        row["arrival_only_candidate"]["mae"] > row["incumbent"]["mae"]
        for row in rows
    )
    assert report["model_effect"] == "none"


def test_hitter_linked_path_tradeoff_persists_across_horizons() -> None:
    report = _report("hitter")
    rows = report["horizon_sensitivity"]
    assert [row["horizon_years"] for row in rows] == [1, 2, 3, 4]
    assert all(
        row["arrival_only_candidate"]["rmse"] > row["incumbent"]["rmse"]
        for row in rows
    )
    assert report["boundaries"]["production_values_changed"] is False


def test_pitcher_blends_remain_exposed_research_and_worsen_mae() -> None:
    report = _report("pitcher")
    blends = report["blend_sensitivity"]
    assert [row["linked_weight"] for row in blends] == [0.25, 0.5, 0.75]
    assert all(
        row["status"] == "exposed_cohort_sensitivity_not_candidate"
        for row in blends
    )
    incumbent_mae = report["continuous_validation_harness"]["incumbent"]["mae"]
    assert all(row["scores"]["mae"] > incumbent_mae for row in blends)


def test_quarter_linked_hitter_blend_is_promising_but_not_promoted() -> None:
    report = _report("hitter")
    blend = report["blend_sensitivity"][0]
    incumbent = report["continuous_validation_harness"]["incumbent"]
    assert blend["linked_weight"] == 0.25
    assert blend["scores"]["rmse"] < incumbent["rmse"]
    assert blend["scores"]["mae"] < incumbent["mae"]
    assert abs(blend["scores"]["bias"]) < abs(incumbent["bias"])
    assert blend["paired_difference_vs_incumbent"]["mse"]["ci_high"] > 0
    assert blend["status"] == "exposed_cohort_sensitivity_not_candidate"
