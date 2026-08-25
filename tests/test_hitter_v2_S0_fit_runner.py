from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from universal_baseball.hitter_v2_model import NESTED_NODES


SCRIPT = Path("scripts/fit_hitter_v2_S0.py")
SPEC = importlib.util.spec_from_file_location("fit_hitter_v2_S0", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_oldest_fold_expands_frozen_all_component_default() -> None:
    selection = json.loads(
        Path("docs/hitter-v2-stage2-component-selection-result.json").read_text(
            encoding="utf-8"
        )
    )
    half_lives, priors = MODULE._component_parameters(selection, "V2022")
    assert set(half_lives) == {node.name for node in NESTED_NODES}
    assert set(priors) == set(half_lives)
    assert set(half_lives.values()) == {3.0}
    assert set(priors.values()) == {800.0}
