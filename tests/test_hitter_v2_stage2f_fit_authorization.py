from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION = ROOT / "docs/hitter-v2-stage2f-H0-fit-authorization.json"


def test_authorization_opens_source_and_fit_but_not_scoring() -> None:
    authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
    contract = ROOT / authorization["contract_path"]
    checkpoint = ROOT / authorization["target_free_checkpoint_path"]

    assert authorization["contract_sha256"] == sha256(contract.read_bytes()).hexdigest()
    assert (
        authorization["target_free_checkpoint_sha256"]
        == sha256(checkpoint.read_bytes()).hexdigest()
    )
    gate = authorization["current_gate"]
    assert gate["historical_predictor_source_audit_open"] is True
    assert gate["chronology_safe_source_materialization_open"] is True
    assert gate["real_data_H0_fit_open"] is True
    assert gate["fit_only_diagnostics_open"] is True
    assert gate["candidate_scoring_open"] is False
    assert not any(authorization["immutable_boundaries"].values())
