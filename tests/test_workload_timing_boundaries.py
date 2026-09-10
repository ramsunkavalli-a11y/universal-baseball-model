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


def test_asof_workload_report_enforces_mature_training_windows() -> None:
    result = json.loads(
        (ROOT / "docs/prospect-workload-asof-validation-result.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["boundaries"]["forecast_time_chronology_safe"] is True
    assert result["boundaries"]["training_windows_end_before_evaluation_year"] is True
    for fold in result["chronology"]:
        assert fold["maximum_training_window_end"] < fold["evaluation_year"]
