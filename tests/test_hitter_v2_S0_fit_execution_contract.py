from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/hitter-v2-S0-fit-execution-contract.json"


def test_S0_fit_execution_contract_freezes_code_inputs_and_boundaries() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["status"] == "frozen_before_first_S0_fit_execution"
    assert contract["runner_sha256"] == sha256(
        (ROOT / contract["runner_path"]).read_bytes()
    ).hexdigest()
    for record in contract["shared_inputs"]:
        assert record["sha256"] == sha256(
            (ROOT / record["path"]).read_bytes()
        ).hexdigest()
    for fold in ("V2022", "V2023", "V2024"):
        for record in contract["folds"][fold]["inputs"]:
            assert record["sha256"] == sha256(
                (ROOT / record["path"]).read_bytes()
            ).hexdigest()
    assert contract["target_free_fit_authorized"] is True
    for boundary in (
        "disclosed_validation_scoring_authorized",
        "protected_confirmation_access_authorized",
        "later_increment_fit_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        assert contract[boundary] is False
