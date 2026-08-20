from __future__ import annotations

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
