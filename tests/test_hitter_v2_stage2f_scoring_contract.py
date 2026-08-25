from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/hitter-v2-stage2f-H0-scoring-contract.json"


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_stage2f_scoring_contract_freezes_runner_and_all_inputs() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["status"] == "frozen_before_first_disclosed_target_access"
    assert _hash(ROOT / contract["runner_path"]) == contract["runner_sha256"]
    assert _hash(ROOT / contract["validation_module_path"]) == contract["validation_module_sha256"]
    assert _hash(ROOT / contract["authorization_path"]) == contract["authorization_sha256"]
    assert _hash(ROOT / contract["selection_checkpoint_path"]) == contract["selection_checkpoint_sha256"]
    assert _hash(ROOT / contract["selection_report_path"]) == contract["selection_report_sha256"]

    for fold in contract["folds"].values():
        for model, relative in fold["prediction_paths"].items():
            assert _hash(ROOT / relative) == fold["prediction_sha256"][model]
        for key in ("target", "training", "age", "raw_marcel"):
            assert _hash(ROOT / fold[f"{key}_path"]) == fold[f"{key}_sha256"]
        translation = fold["translation_offsets_path"]
        if translation is None:
            assert fold["translation_offsets_sha256"] is None
        else:
            assert _hash(ROOT / translation) == fold["translation_offsets_sha256"]


def test_stage2f_scoring_contract_keeps_every_later_gate_closed() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["candidate_scoring_authorized"] is True
    for key in (
        "post_result_retuning_authorized",
        "H1_authorized",
        "tracking_authorized",
        "protected_confirmation_access_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        assert contract[key] is False
    assert contract["promotion_rule"]["all_applicable_rules_required"] is True
