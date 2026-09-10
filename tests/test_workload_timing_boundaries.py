import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_workload_cohort_reports_do_not_claim_forecast_time_chronology() -> None:
    for name in (
        "prospect-workload-distribution-validation-result.json",
        "pitcher-workload-era-candidate-result.json",
    ):
        result = json.loads((ROOT / "docs" / name).read_text(encoding="utf-8"))
        boundaries = result["boundaries"]
        assert boundaries["forecast_time_chronology_safe"] is False
        assert boundaries["training_path_outcomes_extend_past_evaluation_debut"] is True
