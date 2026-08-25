from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from universal_baseball.hitter_v2_stage2e import Stage2eFitError


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/certify_hitter_v2_stage2e_numerics.py"


def _runner() -> object:
    spec = importlib.util.spec_from_file_location("stage2e_certification", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_incident_writer_names_node_and_keeps_candidate_closed(tmp_path: Path) -> None:
    runner = _runner()
    path = tmp_path / "incident.json"
    error = Stage2eFitError(
        "HR",
        "contextual",
        "intentional",
        [{"iteration": 1, "accepted_step_size": 1.0}],
    )
    runner.write_incident(path, error, phase="synthetic_test", hashes={"x": "y"})
    incident = json.loads(path.read_text(encoding="utf-8"))
    assert incident["status"] == "failed_closed"
    assert incident["node"] == "HR"
    assert incident["optimizer_phase"] == "contextual"
    assert incident["candidate_artifact_published"] is False
    assert incident["real_outcomes_loaded"] is False
    assert incident["forecast_targets_loaded"] is False
    assert incident["protected_2026_opened"] is False
