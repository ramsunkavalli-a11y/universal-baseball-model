from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


SCRIPT = Path("scripts/diagnose_hitter_v2_post_H0.py")
SPEC = importlib.util.spec_from_file_location("post_h0_diagnostic", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_age_translation_replaces_all_offset_without_changing_simplex() -> None:
    probabilities = {outcome: 0.01 for outcome in HITTER_TALENT_OUTCOMES}
    probabilities["OTHER_OUT"] += 1.0 - sum(probabilities.values())
    row = {
        "player_id": 1,
        "model_id": "L0",
        "prior_level": "AAA",
        **{f"p_{outcome}": value for outcome, value in probabilities.items()},
    }
    offsets = pl.DataFrame(
        {
            "component": ["plate_appearance", "plate_appearance"],
            "level": ["AAA", "AAA"],
            "age_band": ["ALL", "LE_20"],
            "link_offset_to_MLB": [0.1, 0.3],
        }
    )
    result = MODULE.age_translation_only(
        pl.DataFrame([row]), pl.DataFrame({"player_id": [1], "age_years": [20.0]}), offsets
    )
    assert result["model_id"][0] == "L1_AGE_TRANSLATION_ONLY"
    assert abs(sum(result[f"p_{outcome}"][0] for outcome in HITTER_TALENT_OUTCOMES) - 1.0) < 1e-12
    assert result["p_K"][0] > probabilities["K"]
