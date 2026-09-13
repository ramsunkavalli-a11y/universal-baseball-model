from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl


sys.path.insert(0, str(Path("scripts").resolve()))

from audit_peak_pitcher_structure import (  # noqa: E402
    _attach_origin_role,
    _structure_features,
)
from audit_one_year_talent_development import PITCHER_COMPONENTS  # noqa: E402
from universal_baseball.projection_composition import sequential_helmert_ilr_basis  # noqa: E402


def test_origin_role_join_uses_same_season_starter_share() -> None:
    examples = pl.DataFrame({"player_id": [1], "origin_year": [2024]})
    source = pl.DataFrame({
        "player_id": [1, 1], "season": [2024, 2024], "games": [10, 5], "starts": [8, 1]
    })
    result = _attach_origin_role(examples, source)
    assert result.item(0, "start_share") == 0.6


def test_combined_features_add_role_and_level_interactions() -> None:
    row = {
        "age_years": 20.0, "age_relative_to_level": -2.0,
        "weighted_affiliated_exposure": 200.0, "level_group": "AA",
        "start_share": 0.8,
        "p_so": 0.25, "p_ubb": 0.08, "p_hbp": 0.01, "p_hr": 0.02, "p_other": 0.64,
    }
    basis = sequential_helmert_ilr_basis(len(PITCHER_COMPONENTS))
    baseline_width = 6 + len(PITCHER_COMPONENTS) - 1 + (len(PITCHER_COMPONENTS) - 1)
    result = _structure_features([row], "combined", basis)
    assert result.shape[0] == 1
    assert result.shape[1] > baseline_width
    assert np.isfinite(result).all()
