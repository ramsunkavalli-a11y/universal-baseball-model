from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_stage2e_authorization_is_conditional_and_keeps_current_fit_closed() -> None:
    authorization = json.loads(
        (ROOT / "docs/hitter-v2-stage2e-authorization.json").read_text(
            encoding="utf-8"
        )
    )
    assert authorization["contract_sha256"] == _sha256(
        ROOT / authorization["contract_path"]
    )
    program = authorization["program_authorization"]
    assert all(program.values())
    current = authorization["current_gate"]
    assert current["target_free_implementation_authorized"] is True
    assert current["numerical_certification_authorized"] is True
    assert current["real_data_fit_open"] is False
    assert current["candidate_scoring_open"] is False
    assert all(value is False for value in authorization["immutable_boundaries"].values())
