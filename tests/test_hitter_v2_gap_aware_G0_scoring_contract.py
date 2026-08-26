import json
from pathlib import Path

from universal_baseball.storage import sha256_file


ROOT = Path(__file__).resolve().parents[1]


def test_G0_scorer_and_inputs_are_frozen_before_score() -> None:
    contract = json.loads(
        (ROOT / "docs/hitter-v2-gap-aware-G0-scoring-contract.json").read_text()
    )
    assert contract["status"] == "frozen_before_first_disclosed_G0_score"
    assert sha256_file(ROOT / contract["runner_path"]) == contract["runner_sha256"]
    assert contract["one_shot_scoring_authorized"] is True
    for fold in ("V2022", "V2023", "V2024"):
        for record in contract["folds"][fold]["inputs"]:
            assert sha256_file(ROOT / record["path"]) == record["sha256"]


def test_G0_scoring_contract_keeps_later_gates_closed() -> None:
    contract = json.loads(
        (ROOT / "docs/hitter-v2-gap-aware-G0-scoring-contract.json").read_text()
    )
    for boundary in (
        "post_result_retuning_authorized",
        "later_increment_fit_authorized",
        "protected_confirmation_access_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        assert contract[boundary] is False
