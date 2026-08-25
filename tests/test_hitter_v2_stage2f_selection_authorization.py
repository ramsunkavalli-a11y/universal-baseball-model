from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "docs/hitter-v2-stage2f-H0-selection-authorization.json"


def test_selection_authorization_opens_only_strictly_earlier_origins() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    contract = ROOT / authorization["contract_path"]
    checkpoint = ROOT / authorization["fit_checkpoint_path"]

    assert authorization["contract_sha256"] == sha256(contract.read_bytes()).hexdigest()
    assert (
        authorization["fit_checkpoint_sha256"]
        == sha256(checkpoint.read_bytes()).hexdigest()
    )
    gate = authorization["current_gate"]
    assert gate["strictly_earlier_training_origin_outcomes_open"] is True
    assert gate["frozen_grid_selection_open"] is True
    assert gate["final_parameter_refit_and_freeze_open"] is True
    assert gate["prescore_invariants_open"] is True
    assert gate["disclosed_validation_scoring_open"] is False
    assert not any(authorization["immutable_boundaries"].values())
