from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "docs/hitter-v2-stage2f-authorization.json"


def test_authorization_opens_only_target_free_H0_implementation() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    contract = ROOT / authorization["contract_path"]
    assert authorization["contract_sha256"] == sha256(contract.read_bytes()).hexdigest()
    gate = authorization["current_gate"]
    assert gate["target_free_H0_implementation_authorized"] is True
    assert gate["synthetic_invariants_authorized"] is True
    assert gate["real_data_fit_open"] is False
    assert gate["candidate_scoring_open"] is False
    assert not any(authorization["immutable_boundaries"].values())
