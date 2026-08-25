from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "docs/hitter-v2-post-H0-diagnostic-authorization.json"


def test_post_H0_authorization_is_diagnostic_only() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    result = ROOT / authorization["H0_result_path"]
    assert authorization["H0_result_sha256"] == sha256(result.read_bytes()).hexdigest()
    assert authorization["fixed_H0_ablation_order"] == [
        "L0_reference_C0_ALL_translation",
        "L1_C0_age_conditioned_translation",
        "L2_C0_age_conditioned_translation_plus_development",
        "L3_full_H0_plus_calibration",
    ]
    assert not any(authorization["immutable_boundaries"].values())


def test_post_H0_diagnostic_contract_freezes_runner_and_ablation() -> None:
    contract = json.loads(
        (ROOT / "docs/hitter-v2-post-H0-diagnostic-contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["status"] == "frozen_before_diagnostic_execution"
    for path_key, hash_key in (("runner_path", "runner_sha256"), ("test_path", "test_sha256")):
        path = ROOT / contract[path_key]
        assert contract[hash_key] == sha256(path.read_bytes()).hexdigest()
    assert contract["H0_ablation_order"] == [
        "L0_REFERENCE_WRAPPED_C0",
        "L1_AGE_TRANSLATION_ONLY",
        "L2_PLUS_DEVELOPMENT",
        "L3_PLUS_CALIBRATION_H0",
    ]
    assert contract["candidate_fit_authorized"] is False
    assert contract["protected_confirmation_access_authorized"] is False
