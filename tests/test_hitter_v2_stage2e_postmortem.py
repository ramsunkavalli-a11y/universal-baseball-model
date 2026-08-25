from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/diagnose_hitter_v2_stage2e_failure.py"


def _module():
    specification = importlib.util.spec_from_file_location("stage2e_postmortem", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_component_diagnostic_reports_signed_bias() -> None:
    module = _module()
    outcomes = list(module.HITTER_TALENT_OUTCOMES)
    counts = {outcome: [0] for outcome in outcomes}
    counts["1B"] = [1]
    counts["OTHER_OUT"] = [1]
    target = pl.DataFrame({"player_id": [1], "hitter_talent_pa": [2], **counts})
    probabilities = {f"p_{outcome}": [0.0] for outcome in outcomes}
    probabilities["p_1B"] = [0.6]
    probabilities["p_OTHER_OUT"] = [0.4]
    prediction = pl.DataFrame({"player_id": [1], **probabilities})
    rows = module.component_diagnostics(prediction, target, weighting="player")
    one_b = next(row for row in rows if row["outcome"] == "1B")
    assert one_b["actual_rate"] == 0.5
    assert abs(one_b["bias"] - 0.1) < 1e-12
