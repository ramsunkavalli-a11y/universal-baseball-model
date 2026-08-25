import json
from pathlib import Path


RESULT_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "hitter-v2-terminal-outcome-label-sidecar-result.json"
)


def test_terminal_label_source_gate_passes_every_frozen_coverage_floor() -> None:
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    gate = result["coverage_gate"]

    assert result["accepted"] is True
    assert gate["passed"] is True
    assert gate["failed_cells"] == []
    assert gate["overall_observed"] >= gate["overall_minimum"]
    for row in result["coverage_by_season_level"]:
        minimum = 0.85 if row["level_group"] == "rk" else 0.90
        assert row["context_label_ready_rate"] >= minimum


def test_terminal_label_result_preserves_source_and_authorization_boundaries() -> None:
    result = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    boundary = result["source_boundary"]
    authorization = result["authorization"]
    amendment = result["source_semantic_amendment"]

    assert boundary["seasons"] == [2021, 2022, 2023, 2024]
    assert boundary["forecast_targets_loaded"] is False
    assert boundary["candidate_implemented"] is False
    assert boundary["candidate_fit"] is False
    assert boundary["candidate_scored"] is False
    assert boundary["protected_2026_opened"] is False
    assert amendment["initial_attempt_accepted"] is False
    assert amendment["totals_used_to_assign_individual_labels"] is False
    assert amendment["runner_only_records_forced_into_hitter_taxonomy"] is False
    assert authorization["J0_implementation_authorized"] is False
    assert authorization["candidate_fit_authorized"] is False
    assert authorization["candidate_scoring_authorized"] is False
