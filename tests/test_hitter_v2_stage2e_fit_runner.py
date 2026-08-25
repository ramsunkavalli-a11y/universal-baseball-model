from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fit_hitter_v2_stage2e_j0r.py"


def _module():
    specification = importlib.util.spec_from_file_location("stage2e_fit_runner", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_fit_boundary_requires_certification_and_keeps_scoring_closed() -> None:
    module = _module()
    authorization = {
        "current_gate": {
            "chronology_safe_v2022_v2023_v2024_fit_open": True,
            "forecast_targets_open": False,
            "candidate_scoring_open": False,
        },
        "certification_result_sha256": module.EXPECTED["certification"],
        "immutable_boundaries": {
            "post_fit_parameter_change": False,
            "J0_rerun_or_rescue": False,
            "protected_2026_access_authorized": False,
            "J1_authorized": False,
            "tracking_authorized": False,
            "stage3_authorized": False,
            "full_war_authorized": False,
        },
    }
    certification = {"accepted": True, "real_outcomes_loaded": False}
    hashes = {**module.EXPECTED, "authorization": "recorded-separately"}
    module.verify_fit_boundary(authorization, certification, hashes)

    authorization["current_gate"]["candidate_scoring_open"] = True
    try:
        module.verify_fit_boundary(authorization, certification, hashes)
    except ValueError as error:
        assert "cannot score" in str(error)
    else:
        raise AssertionError("fit runner accepted an open scoring gate")
