from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_J0_fit_incident_failed_closed_without_score_or_artifact() -> None:
    incident = json.loads(
        (ROOT / "docs/hitter-v2-stage2d-j0-fit-incident.json").read_text(
            encoding="utf-8"
        )
    )
    assert incident["status"] == "failed_closed"
    assert incident["exit_code"] == 1
    assert incident["artifact_audit"] == {
        "result_directory_created": False,
        "model_artifacts_published": False,
        "partial_fit_accepted": False,
    }
    boundary = incident["scientific_boundary"]
    assert boundary["candidate_fit_attempted"] is True
    assert boundary["candidate_fit_completed"] is False
    assert boundary["candidate_scored"] is False
    assert boundary["forecast_targets_loaded"] is False
    assert boundary["protected_2026_opened"] is False
    assert boundary["tolerance_changed_after_failure"] is False
    assert boundary["rerun_attempted"] is False
    assert boundary["rescue_tuning_allowed"] is False
    assert incident["failing_node"] == "not_identified_by_frozen_runner"
    assert incident["candidate_scoring_authorized"] is False
