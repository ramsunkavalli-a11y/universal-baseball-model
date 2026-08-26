from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_S0_scoring_contract_freezes_runner_inputs_and_boundaries() -> None:
    contract = json.loads(
        (ROOT / "docs/hitter-v2-S0-scoring-contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["status"] == "frozen_before_first_disclosed_S0_score"
    assert contract["runner_sha256"] == sha256(
        (ROOT / contract["runner_path"]).read_bytes()
    ).hexdigest()
    for fold in ("V2022", "V2023", "V2024"):
        for record in contract["folds"][fold]["inputs"]:
            assert record["sha256"] == sha256(
                (ROOT / record["path"]).read_bytes()
            ).hexdigest()
    assert contract["one_shot_scoring_authorized"] is True
    for boundary in (
        "post_result_retuning_authorized",
        "later_increment_fit_authorized",
        "protected_confirmation_access_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        assert contract[boundary] is False
