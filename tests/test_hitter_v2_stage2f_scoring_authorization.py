from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "docs/hitter-v2-stage2f-H0-scoring-authorization.json"


def test_scoring_authorization_opens_only_frozen_disclosed_comparison() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    contract = ROOT / authorization["contract_path"]
    checkpoint = ROOT / authorization["selection_checkpoint_path"]

    assert authorization["contract_sha256"] == sha256(contract.read_bytes()).hexdigest()
    assert (
        authorization["selection_checkpoint_sha256"]
        == sha256(checkpoint.read_bytes()).hexdigest()
    )
    gate = authorization["current_gate"]
    assert gate["frozen_scorer_implementation_open"] is True
    assert gate["scorer_tests_and_hash_freeze_open"] is True
    assert gate["one_disclosed_V2022_V2024_comparison_open_only_after_scorer_commit"] is True
    assert gate["post_result_documentation_open"] is True
    assert gate["model_parameter_changes_open"] is False
    assert not any(authorization["immutable_boundaries"].values())
