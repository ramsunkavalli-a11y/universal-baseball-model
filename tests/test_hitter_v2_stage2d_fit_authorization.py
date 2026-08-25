from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fit_hitter_v2_stage2d_j0.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_runner() -> object:
    spec = importlib.util.spec_from_file_location("fit_hitter_v2_stage2d_j0", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fit_authorization_opens_only_the_fit_gate() -> None:
    authorization = json.loads(
        (ROOT / "docs/hitter-v2-stage2d-j0-fit-authorization.json").read_text(
            encoding="utf-8"
        )
    )
    assert authorization["J0_real_data_fit_authorized"] is True
    closed = [key for key in authorization if key.endswith("_authorized")]
    assert closed == [
        "J0_real_data_fit_authorized",
        "candidate_scoring_authorized",
        "post_fit_tuning_authorized",
        "J1_authorized",
        "protected_2026_access_authorized",
        "tracking_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ]
    assert all(authorization[key] is False for key in closed[1:])


def test_runner_accepts_exact_frozen_boundary() -> None:
    runner = _load_runner()
    contract_path = ROOT / "docs/hitter-v2-stage2d-j0-fit-execution-contract.json"
    authorization_path = ROOT / "docs/hitter-v2-stage2d-j0-fit-authorization.json"
    implementation_path = ROOT / "src/universal_baseball/hitter_v2_stage2d.py"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))

    runner.verify_execution_boundary(
        contract,
        authorization,
        contract_sha256=_sha256(contract_path),
        implementation_sha256=_sha256(implementation_path),
        event_input_sha256=authorization["event_input_sha256"],
    )


def test_runner_rejects_scoring_authorization() -> None:
    runner = _load_runner()
    contract_path = ROOT / "docs/hitter-v2-stage2d-j0-fit-execution-contract.json"
    authorization_path = ROOT / "docs/hitter-v2-stage2d-j0-fit-authorization.json"
    implementation_path = ROOT / "src/universal_baseball/hitter_v2_stage2d.py"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    authorization["candidate_scoring_authorized"] = True

    try:
        runner.verify_execution_boundary(
            contract,
            authorization,
            contract_sha256=_sha256(contract_path),
            implementation_sha256=_sha256(implementation_path),
            event_input_sha256=authorization["event_input_sha256"],
        )
    except ValueError as error:
        assert "later scientific gate" in str(error)
    else:
        raise AssertionError("runner accepted an authorization that opened scoring")
