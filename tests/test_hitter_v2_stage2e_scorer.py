from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/score_hitter_v2_stage2e_j0r.py"


def _module():
    specification = importlib.util.spec_from_file_location("stage2e_scorer", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_primary_gate_uses_metric_wise_strongest_frozen_comparator() -> None:
    module = _module()
    metrics = {
        model: {metric: 1.0 for metric in module.GATE_METRICS}
        for model in module.MODELS
    }
    metrics["B1_MARCEL_345_K1200"]["woba_rmse"] = 0.9
    metrics[module.CANDIDATE]["woba_rmse"] = 0.89
    gate = module._primary_gate(metrics)
    assert gate["metrics"]["woba_rmse"]["comparator"] == "B1_MARCEL_345_K1200"
    assert gate["metrics"]["woba_rmse"]["pass"] is True
    assert gate["pass"] is False


def test_scoring_boundary_keeps_all_later_gates_closed(tmp_path: Path) -> None:
    module = _module()
    runner = tmp_path / "runner.py"
    runner.write_bytes(b"frozen")
    from universal_baseball.storage import sha256_file

    contract = {
        "status": "frozen_before_first_target_access",
        "runner_sha256": sha256_file(runner),
        "candidate_scoring_authorized": True,
        "post_result_tuning_authorized": False,
        "protected_2026_access_authorized": False,
        "J1_authorized": False,
        "tracking_authorized": False,
        "stage3_authorized": False,
        "full_war_authorized": False,
    }
    module.verify_scoring_boundary(contract, runner=runner)
    contract["J1_authorized"] = True
    try:
        module.verify_scoring_boundary(contract, runner=runner)
    except ValueError as error:
        assert "J1_authorized" in str(error)
    else:
        raise AssertionError("scorer accepted an open later gate")
