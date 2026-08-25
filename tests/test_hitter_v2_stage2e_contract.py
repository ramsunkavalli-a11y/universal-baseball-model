from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/hitter-v2-stage2e-development-contract.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_stage2e_is_distinct_and_preserves_failed_J0() -> None:
    contract = _contract()
    candidate = contract["candidate"]
    assert candidate["model_id"] == "J0R_FIXED_INFORMATION_SHRINKAGE"
    assert candidate["identity"] == "distinct_successor_not_a_J0_amendment_or_rerun"
    assert candidate["J0_JOINT_CONTEXTUAL_NESTED_status"] == (
        "final_documented_numerical_failure"
    )
    assert candidate["J0_artifacts_reused"] is False
    assert candidate["J0_partial_parameters_reused"] is False
    assert contract["failure_policy"]["J0_may_be_rescued_or_relabelled"] is False


def test_stage2e_fixed_scale_is_target_free_and_matched() -> None:
    contract = _contract()
    shrinkage = contract["fixed_information_shrinkage"]
    matched = contract["matched_models"]
    chronology = contract["source_and_chronology"]
    assert shrinkage["estimated_variance_iteration"] is False
    assert shrinkage["contextual_and_uncontextual_scale_identity"] is True
    assert shrinkage["scale_selected_from_validation_metrics"] is False
    assert matched["identical_event_rows"] is True
    assert matched["identical_batter_penalty_within_each_pair"] is True
    assert chronology["target_year_membership_environment_or_outcomes_allowed"] is False
    assert chronology["protected_2026_opened"] is False


def test_stage2e_certification_is_synthetic_and_observable() -> None:
    contract = _contract()
    certification = contract["numerical_certification_before_real_fit"]
    observability = contract["required_observability"]
    assert certification["real_outcomes_loaded"] is False
    assert certification["forecast_targets_loaded"] is False
    assert certification["real_fit_authorized_by_certification"] is False
    assert certification["synthetic_seeds"] == [20260824, 20260825]
    assert "intentional_nonconvergence_names_node_and_phase" in certification[
        "required_tests"
    ]
    assert "accepted_step_size" in observability["per_optimizer_iteration"]
    assert observability["incident_write_policy"].startswith("atomic_separate_incident")


def test_stage2e_opens_no_execution_or_downstream_gate() -> None:
    authorization = _contract()["authorization"]
    assert authorization["contract_frozen"] is True
    closed = [key for key, value in authorization.items() if key.endswith("authorized")]
    assert closed
    assert all(authorization[key] is False for key in closed)
    assert authorization["next_gate"] == (
        "review_contract_then_authorize_target_free_implementation_and_numerical_certification_only"
    )


def test_stage2e_provenance_hashes_match_preserved_evidence() -> None:
    provenance = _contract()["provenance"]
    for path_key, hash_key in (
        ("stage2d_contract_path", "stage2d_contract_sha256"),
        ("J0_incident_path", "J0_incident_sha256"),
        ("post_J0_review_path", "post_J0_review_sha256"),
    ):
        assert provenance[hash_key] == _sha256(ROOT / provenance[path_key])


def test_workflow_records_contract_hash_and_gated_boundary() -> None:
    workflow = json.loads(
        (ROOT / "docs/hitter-v2-workflow-status.json").read_text(encoding="utf-8")
    )
    record = workflow["stage2e_J0R_contract"]
    assert record["contract_sha256"] == _sha256(CONTRACT)
    assert record["human_readable_sha256"] == _sha256(
        ROOT / record["human_readable_path"]
    )
    authorization = workflow["authorization"]
    assert authorization["stage2e_contract_frozen"] is True
    assert authorization["stage2e_candidate_implementation_authorized"] is True
    assert authorization["stage2e_numerical_certification_authorized"] is True
    certification = workflow["stage2e_numerical_certification"]
    assert certification["sha256"] == _sha256(ROOT / certification["path"])
    assert certification["accepted"] is True
    fit_authorization = workflow["stage2e_fit_authorization"]
    assert fit_authorization["chronology_safe_fold_fit_open"] is True
    assert fit_authorization["forecast_targets_open"] is False
    assert authorization["stage2e_real_data_fit_authorized"] is True
    assert authorization["stage2e_candidate_scoring_authorized"] is False
