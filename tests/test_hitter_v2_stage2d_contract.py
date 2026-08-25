import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "hitter-v2-stage2d-development-contract.json"
SIDECAR_RESULT_PATH = ROOT / "docs" / "hitter-v2-matchup-context-sidecar-result.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_stage2d_contract_preserves_prefit_and_protected_boundaries() -> None:
    contract = _load(CONTRACT_PATH)

    assert contract["status"] == (
        "pre_registered_before_event_label_implementation_candidate_fit_or_score"
    )
    assert contract["development_boundary"]["2026"].endswith("unopened")
    assert contract["implementation_state"] == {
        "event_label_sidecar_implemented": False,
        "candidate_implemented": False,
        "candidate_fit": False,
        "candidate_scored": False,
        "scorer_frozen": False,
    }
    assert contract["downstream_authorization"] == {
        "event_label_source_materialization": True,
        "candidate_implementation_after_label_gate": False,
        "candidate_fit": False,
        "candidate_scoring": False,
        "tracking": False,
        "stage3": False,
        "full_war": False,
    }
    assert contract["next_gate"] == (
        "source_only_terminal_outcome_label_sidecar_materialization_and_reconciliation"
    )


def test_stage2d_contract_freezes_fallback_ladder_and_no_search() -> None:
    contract = _load(CONTRACT_PATH)
    ladder = contract["candidate_ladder"]

    assert contract["universal_base"]["model_id"] == "B1_MARCEL_345_K1200"
    assert "equals B1 exactly" in contract["universal_base"]["fallback_identity"]
    assert ladder[0]["must_pass_before_next_candidate"] is True
    assert ladder[1]["authorized_only_if_j0_passes"] is True
    assert ladder[1]["cannot_rescue_failed_j0"] is True
    assert contract["fit_protocol"]["hyperparameter_search"] is False
    assert contract["fit_protocol"]["post_score_refit_or_tuning"] is False
    assert contract["pitcher_quality_feature"]["same_day_events_allowed"] is False
    assert contract["pitcher_quality_feature"]["future_events_allowed"] is False
    assert contract["j1_forward_development"]["scale_invariance_test"].endswith(
        "1e-12"
    )


def test_stage2d_contract_isolates_contextual_hypothesis() -> None:
    contract = _load(CONTRACT_PATH)
    excluded = set(contract["excluded_from_stage2d"])

    assert {
        "park_effects",
        "contact_direction_or_trajectory",
        "exit_velocity",
        "estimated_distance",
        "lineup_slot",
        "height",
        "weight",
        "country_of_origin",
    }.issubset(excluded)
    assert contract["evaluation"]["metric_wise_comparator"] == (
        "lowest loss among B0_ONE_YEAR_EB, B1_MARCEL_345_K1200, and frozen "
        "failed C0_NESTED_EB on identical forecast-target rows"
    )
    invariants = set(contract["scientific_invariants"])
    assert "removing matchup context returns B1 probabilities exactly" in invariants
    assert "rescaling a continuous J1 predictor cannot change predictions" in invariants
    assert "contact shape and tracking cannot alter J0 or J1" in invariants


def test_stage2d_contract_points_to_certified_matchup_artifacts() -> None:
    contract = _load(CONTRACT_PATH)
    sidecar_result = _load(SIDECAR_RESULT_PATH)
    storage = sidecar_result["storage"]

    assert contract["parent_evidence"]["matchup_sidecar_sha256"] == storage[
        "sidecar"
    ]["file_sha256"]
    assert contract["parent_evidence"]["matchup_reconciliation_sha256"] == storage[
        "reconciliation"
    ]["file_sha256"]
    assert len(hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest()) == 64
