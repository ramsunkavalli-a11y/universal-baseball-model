from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path("scripts/score_hitter_v2_S0.py")
SPEC = importlib.util.spec_from_file_location("score_hitter_v2_S0", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_pooled_gate_requires_every_metric_and_view() -> None:
    metrics = {}
    for model, value in (
        ("C0_NESTED_EB", 1.0),
        ("B1_MARCEL_345_K1200", 1.1),
        ("S0_C0_MARCEL_STABILITY_BLEND", 0.98),
    ):
        metrics[model] = {
            view: {metric: value for metric in MODULE.PRIMARY_METRICS}
            for view in ("player", "pa")
        }
    assert MODULE._pooled_gate(metrics)["pass"] is True
    metrics[MODULE.CANDIDATE]["pa"]["woba_rmse"] = 0.995
    assert MODULE._pooled_gate(metrics)["pass"] is False


def test_scoring_runner_does_not_name_protected_season() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "2026" not in source
