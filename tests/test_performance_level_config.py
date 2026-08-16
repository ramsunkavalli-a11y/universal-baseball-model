from __future__ import annotations

import pytest

from universal_baseball.bin_value_policy import LEAGUE_LEVEL_GROUP
from universal_baseball.performance_level_config import (
    PERFORMANCE_LEVEL_SPECS_2024,
    performance_level_spec_2024,
    validate_performance_level_specs_2024,
)


def test_2024_level_specs_cover_every_certified_affiliated_league_once() -> None:
    validate_performance_level_specs_2024()
    represented = [
        league_id
        for spec in PERFORMANCE_LEVEL_SPECS_2024.values()
        for league_id in spec.league_ids
    ]
    assert len(represented) == len(set(represented))
    assert set(represented) == set(LEAGUE_LEVEL_GROUP)


def test_middle_level_assets_match_pre_registered_2024_validation_inputs() -> None:
    assert performance_level_spec_2024("aa").calibration_asset == "2024_6_aa_pbp.csv"
    assert performance_level_spec_2024("a+").calibration_asset == "2024_6_a+_pbp.csv"
    assert performance_level_spec_2024("a").calibration_asset == "2024_6_a_pbp.csv"


def test_rookie_spec_keeps_acl_fcl_dsl_in_one_value_level_group() -> None:
    spec = performance_level_spec_2024("rk")
    assert spec.level_group == "ROOKIE_COMPLEX"
    assert spec.league_ids == frozenset({121, 124, 130})
    assert spec.calibration_asset == "2024_6_rk_pbp.csv"


def test_unknown_filename_level_fails() -> None:
    with pytest.raises(KeyError):
        performance_level_spec_2024("mlb")
