import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/hitter-v2-stage2f-H0-comparison-result.json"


def test_stage2f_H0_failure_is_final_and_does_not_open_downstream_work() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["status"] == "failed_final_without_retuning"
    assert result["development_gate_pass"] is False
    assert result["production_promotion_made"] is False
    assert not any(row["fold"] for row in result["gate_summary"].values() if isinstance(row, dict))
    assert all(result["closed"].values())
    assert result["execution_incident"]["partial_result_used"] is False


def test_stage2f_H0_loses_every_primary_metric_in_every_required_view() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    for fold in result["candidate_minus_metric_wise_strongest_baseline"].values():
        for view in fold.values():
            assert all(delta >= 0.0 for delta in view.values())
    for view in result["pooled_relative_improvement"].values():
        assert all(value < 0.0 for value in view.values())
