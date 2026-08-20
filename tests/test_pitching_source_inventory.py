from __future__ import annotations

import json
from pathlib import Path

import pytest

from universal_baseball.pitching_source_inventory import (
    FROZEN_2021_2024_MILB_PITCHING_SHA256,
    expected_pitching_source_specs,
    validate_frozen_pitching_sha,
)


def test_expected_pitching_source_specs_are_fixed_before_2025() -> None:
    specs = expected_pitching_source_specs()

    assert len(specs) == 20
    assert {spec.season for spec in specs} == {2021, 2022, 2023, 2024}
    assert {spec.filename_level for spec in specs} == {"aaa", "aa", "a+", "a", "rk"}
    assert not any("2025" in spec.asset_name for spec in specs)
    assert len({spec.asset_name for spec in specs}) == len(specs)


def test_frozen_pitching_hashes_cover_every_planned_asset() -> None:
    planned = {spec.asset_name for spec in expected_pitching_source_specs()}
    assert set(FROZEN_2021_2024_MILB_PITCHING_SHA256) == planned


def test_validate_frozen_pitching_sha_accepts_exact_frozen_bytes() -> None:
    for asset_name, digest in FROZEN_2021_2024_MILB_PITCHING_SHA256.items():
        validate_frozen_pitching_sha(asset_name, digest.upper())


def test_validate_frozen_pitching_sha_rejects_drift_or_unknown_asset() -> None:
    with pytest.raises(ValueError, match="byte drift"):
        validate_frozen_pitching_sha(
            "2024_aaa_season_pitching_stats.csv",
            "0" * 64,
        )
    with pytest.raises(ValueError, match="unexpected Pitching v1"):
        validate_frozen_pitching_sha(
            "2024_win_season_pitching_stats.csv",
            "0" * 64,
        )


def test_frozen_source_inventory_result_records_verified_pre_2025_gate() -> None:
    result_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "pitching-v1-source-inventory-result.json"
    )
    result = json.loads(result_path.read_text(encoding="utf-8"))

    assert result["status"] == "verified"
    assert result["seasons"] == [2021, 2022, 2023, 2024]
    assert result["confirmation_2025_accessed"] is False
    assert result["combined"] == {
        "all_five_previously_certified_2024_hashes_reproduced": True,
        "all_twenty_frozen_source_hashes_reproduced": True,
        "asset_count": 20,
        "distinct_actual_league_count": 14,
        "distinct_player_count": 8497,
        "profile_grain_unique": True,
        "profile_row_count": 132440,
        "summary_grain_unique": True,
        "summary_row_count": 26488,
        "total_batters_faced": 3073606,
    }
    assert result["verification"]["actions_run_id"] == 32399807939
    assert result["artifact"]["id"] == 9418056648
