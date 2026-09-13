from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl


sys.path.insert(0, str(Path("scripts").resolve()))

from audit_one_year_talent_development import PITCHER_COMPONENTS  # noqa: E402
from audit_pitcher_process_challenger import _design, _process_features  # noqa: E402
from universal_baseball.projection_composition import sequential_helmert_ilr_basis  # noqa: E402


def test_process_features_are_shrunk_relative_to_level_season() -> None:
    raw = pl.DataFrame({
        "season": [2024, 2024], "player_id": [1, 2], "level_group": ["AA", "AA"],
        "bf": [100.0, 100.0], "pitches": [400.0, 400.0],
        "swings": [200.0, 200.0], "whiffs": [80.0, 20.0],
        "strikes": [280.0, 220.0], "balls": [120.0, 180.0],
    })
    result = _process_features(raw).sort("player_id")
    assert result.item(0, "process_whiff") > 0
    assert result.item(1, "process_whiff") < 0
    assert np.isfinite(result.select(pl.exclude("level_group")).to_numpy()).all()


def test_process_design_does_not_add_raw_workload_as_a_candidate_advantage() -> None:
    base = {
        "age_years": 21.0, "age_relative_to_level": -1.0,
        "weighted_affiliated_exposure": 300.0, "level_group": "AA",
        "p_so": 0.25, "p_ubb": 0.08, "p_hbp": 0.01, "p_hr": 0.02, "p_other": 0.64,
        "process_whiff": 0.02, "process_strike": 0.01,
        "process_swing": -0.01, "process_ppbf": 0.1,
    }
    low = {**base, "bf": 50.0}
    high = {**base, "bf": 500.0}
    basis = sequential_helmert_ilr_basis(len(PITCHER_COMPONENTS))
    design = _design([low, high], basis, "all_process")
    np.testing.assert_allclose(design[0], design[1])
