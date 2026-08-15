from __future__ import annotations

from datetime import UTC, datetime

import pytest

from universal_baseball.armstjc_assets import (
    ArmstjcAsset,
    asset_from_github_payload,
    parse_pbp_asset_name,
    validate_asset_inventory,
)


def test_parse_pbp_asset_name() -> None:
    assert parse_pbp_asset_name("2025_3_aaa_pbp.csv") == (2025, 3, "aaa")
    assert parse_pbp_asset_name("2025_4_a+_pbp.csv") == (2025, 4, "a+")
    assert parse_pbp_asset_name("2024_6_rk_pbp.csv") == (2024, 6, "rk")
    assert parse_pbp_asset_name("README.md") is None
    with pytest.raises(ValueError, match="invalid filename period"):
        parse_pbp_asset_name("2025_13_aaa_pbp.csv")


def test_asset_from_github_payload_preserves_upstream_timestamps() -> None:
    payload = {
        "id": 123,
        "name": "2025_4_aa_pbp.csv",
        "size": 456,
        "created_at": "2025-05-02T01:02:03Z",
        "updated_at": "2025-05-02T01:03:04Z",
        "browser_download_url": "https://example.test/asset.csv",
    }
    asset = asset_from_github_payload(payload)
    assert asset is not None
    assert asset.asset_id == 123
    assert asset.year == 2025
    assert asset.filename_period == 4
    assert asset.filename_level == "aa"
    assert asset.created_at_utc == datetime(2025, 5, 2, 1, 2, 3, tzinfo=UTC)


def test_inventory_rejects_duplicate_names_and_bad_timing() -> None:
    baseline = ArmstjcAsset(
        asset_id=1,
        name="2025_3_aaa_pbp.csv",
        size_bytes=100,
        created_at_utc=datetime(2025, 4, 1, tzinfo=UTC),
        updated_at_utc=datetime(2025, 4, 1, tzinfo=UTC),
        browser_download_url="https://example.test/a",
        year=2025,
        filename_period=3,
        filename_level="aaa",
    )
    duplicate_name = ArmstjcAsset(
        asset_id=2,
        name=baseline.name,
        size_bytes=200,
        created_at_utc=baseline.created_at_utc,
        updated_at_utc=baseline.updated_at_utc,
        browser_download_url="https://example.test/b",
        year=2025,
        filename_period=3,
        filename_level="aaa",
    )
    with pytest.raises(ValueError, match="duplicate armstjc asset name"):
        validate_asset_inventory([baseline, duplicate_name])

    bad = ArmstjcAsset(
        asset_id=3,
        name="2025_4_aaa_pbp.csv",
        size_bytes=100,
        created_at_utc=datetime(2025, 5, 2, tzinfo=UTC),
        updated_at_utc=datetime(2025, 5, 1, tzinfo=UTC),
        browser_download_url="https://example.test/c",
        year=2025,
        filename_period=4,
        filename_level="aaa",
    )
    with pytest.raises(ValueError, match="updated before creation"):
        validate_asset_inventory([bad])
